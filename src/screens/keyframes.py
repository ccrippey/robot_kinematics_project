from copy import deepcopy

from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen


class KeyframeEditor(Screen):
    """Screen that lets users edit multiple stick-figure keyframes."""

    PELVIS_FOLLOW_FACTOR = 0.35

    frame_label = StringProperty("Frame 1 / 1")
    frame_choices = ListProperty(["1"])
    current_index = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frames = []
        self._initial_frame = None

        # Motion propagation state for the editable (current) layer
        self._pelvis_prev = None
        self._shoulder_prev = None
        self._foot_midpoint_base = None
        self._pelvis_offset_from_feet = (0, 0)
        self._suppress_pelvis_event = False
        self._suppress_shoulder_event = False

        self._loading_frame = False

        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, dt):
        self._bind_current_end_effectors()
        self._initialize_motion_propagation()

        # Capture the starting pose as frame 1
        self._initial_frame = self._capture_current_frame()
        self.frames = [deepcopy(self._initial_frame)]
        self._refresh_frame_meta()
        self._load_frame(0)

    # ---- Binding editable layer to stick figure ----
    def _bind_current_end_effectors(self):
        if 'stick_current' not in self.ids:
            return
        stick = self.ids.stick_current

        # Hands
        for hand_id, attr_x, attr_y in (
            ('curr_hand_left', 'left_hand_x', 'left_hand_y'),
            ('curr_hand_right', 'right_hand_x', 'right_hand_y'),
        ):
            if hand_id in self.ids:
                eff = self.ids[hand_id]
                eff.bind(center_x=lambda inst, val, attr=attr_x: setattr(stick, attr, val))
                eff.bind(center_y=lambda inst, val, attr=attr_y: setattr(stick, attr, val))
                setattr(stick, attr_x, eff.center_x)
                setattr(stick, attr_y, eff.center_y)

        # Feet
        for foot_id, attr_x, attr_y in (
            ('curr_foot_left', 'left_foot_x', 'left_foot_y'),
            ('curr_foot_right', 'right_foot_x', 'right_foot_y'),
        ):
            if foot_id in self.ids:
                eff = self.ids[foot_id]
                eff.bind(center_x=lambda inst, val, attr=attr_x: setattr(stick, attr, val))
                eff.bind(center_y=lambda inst, val, attr=attr_y: setattr(stick, attr, val))
                setattr(stick, attr_x, eff.center_x)
                setattr(stick, attr_y, eff.center_y)

        # Shoulder & pelvis
        if 'curr_shoulder' in self.ids:
            self.ids.curr_shoulder.bind(center_x=lambda inst, val: setattr(stick, 'shoulder_x', val))
            self.ids.curr_shoulder.bind(center_y=lambda inst, val: setattr(stick, 'shoulder_y', val))
            stick.shoulder_x = self.ids.curr_shoulder.center_x
            stick.shoulder_y = self.ids.curr_shoulder.center_y

        if 'curr_pelvis' in self.ids:
            self.ids.curr_pelvis.bind(center_x=lambda inst, val: setattr(stick, 'pelvis_x', val))
            self.ids.curr_pelvis.bind(center_y=lambda inst, val: setattr(stick, 'pelvis_y', val))
            stick.pelvis_x = self.ids.curr_pelvis.center_x
            stick.pelvis_y = self.ids.curr_pelvis.center_y

    # ---- Motion propagation (feet -> pelvis -> shoulders -> hands) ----
    def _initialize_motion_propagation(self):
        if 'curr_pelvis' in self.ids:
            self._pelvis_prev = (self.ids.curr_pelvis.center_x, self.ids.curr_pelvis.center_y)
        if 'curr_shoulder' in self.ids:
            self._shoulder_prev = (self.ids.curr_shoulder.center_x, self.ids.curr_shoulder.center_y)

        self._foot_midpoint_base = self._current_foot_midpoint()
        if self._foot_midpoint_base and self._pelvis_prev:
            self._pelvis_offset_from_feet = (
                self._pelvis_prev[0] - self._foot_midpoint_base[0],
                self._pelvis_prev[1] - self._foot_midpoint_base[1],
            )

        self._setup_propagation_bindings()

    def _setup_propagation_bindings(self):
        for eff_id in ('curr_foot_left', 'curr_foot_right'):
            if eff_id in self.ids:
                eff = self.ids[eff_id]
                eff.bind(center_x=self._on_foot_moved, center_y=self._on_foot_moved)

        if 'curr_pelvis' in self.ids:
            self.ids.curr_pelvis.bind(center_x=self._on_pelvis_moved, center_y=self._on_pelvis_moved)

        if 'curr_shoulder' in self.ids:
            self.ids.curr_shoulder.bind(center_x=self._on_shoulder_moved, center_y=self._on_shoulder_moved)

    def _current_foot_midpoint(self):
        if 'curr_foot_left' in self.ids and 'curr_foot_right' in self.ids:
            left = self.ids.curr_foot_left.center
            right = self.ids.curr_foot_right.center
            return ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
        return None

    def _on_foot_moved(self, *args):
        if self._loading_frame:
            return
        
        if 'curr_pelvis' not in self.ids:
            return

        foot_mid = self._current_foot_midpoint()
        if not foot_mid or self._pelvis_prev is None:
            return

        target_x = foot_mid[0] + self._pelvis_offset_from_feet[0]
        target_y = foot_mid[1] + self._pelvis_offset_from_feet[1]
        self._apply_pelvis_follow(target_x, target_y)

    def _apply_pelvis_follow(self, target_x, target_y):
        current_x, current_y = self.ids.curr_pelvis.center
        dx = target_x - current_x
        dy = target_y - current_y
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            return

        new_x = current_x + dx * self.PELVIS_FOLLOW_FACTOR
        new_y = current_y + dy * self.PELVIS_FOLLOW_FACTOR
        self._set_pelvis_center(new_x, new_y, update_offset=False)

    def _on_pelvis_moved(self, *args):
        if self._loading_frame:
            return
        
        if self._suppress_pelvis_event or self._pelvis_prev is None:
            self._pelvis_prev = (self.ids.curr_pelvis.center_x, self.ids.curr_pelvis.center_y)
            return

        new_center = (self.ids.curr_pelvis.center_x, self.ids.curr_pelvis.center_y)
        delta = (new_center[0] - self._pelvis_prev[0], new_center[1] - self._pelvis_prev[1])
        self._pelvis_prev = new_center

        if delta == (0, 0):
            return

        foot_mid = self._current_foot_midpoint()
        if foot_mid:
            self._pelvis_offset_from_feet = (new_center[0] - foot_mid[0], new_center[1] - foot_mid[1])

        self._move_shoulders_by(delta)

    def _set_pelvis_center(self, new_x, new_y, update_offset):
        prev = self._pelvis_prev
        self._suppress_pelvis_event = True
        self.ids.curr_pelvis.center = (new_x, new_y)
        self._suppress_pelvis_event = False

        new_center = (new_x, new_y)
        self._pelvis_prev = new_center
        if update_offset:
            foot_mid = self._current_foot_midpoint()
            if foot_mid:
                self._pelvis_offset_from_feet = (new_center[0] - foot_mid[0], new_center[1] - foot_mid[1])

        if prev:
            delta = (new_center[0] - prev[0], new_center[1] - prev[1])
            if delta != (0, 0):
                self._move_shoulders_by(delta)

    def _move_shoulders_by(self, delta):
        if self._loading_frame:
            return
        
        if 'curr_shoulder' not in self.ids:
            return

        cur_x, cur_y = self.ids.curr_shoulder.center
        self._set_shoulder_center((cur_x + delta[0], cur_y + delta[1]))

    def _on_shoulder_moved(self, *args):
        if self._suppress_shoulder_event or self._shoulder_prev is None:
            self._shoulder_prev = (self.ids.curr_shoulder.center_x, self.ids.curr_shoulder.center_y)
            return

        new_center = (self.ids.curr_shoulder.center_x, self.ids.curr_shoulder.center_y)
        delta = (new_center[0] - self._shoulder_prev[0], new_center[1] - self._shoulder_prev[1])
        self._shoulder_prev = new_center

        if delta != (0, 0):
            self._move_hands_by(delta)

    def _set_shoulder_center(self, new_center):
        prev = self._shoulder_prev
        self._suppress_shoulder_event = True
        self.ids.curr_shoulder.center = new_center
        self._suppress_shoulder_event = False

        self._shoulder_prev = new_center
        if prev:
            delta = (new_center[0] - prev[0], new_center[1] - prev[1])
            if delta != (0, 0):
                self._move_hands_by(delta)

    def _move_hands_by(self, delta):
        if self._loading_frame:
            return
        
        dx, dy = delta
        for eff_id in ('curr_hand_left', 'curr_hand_right'):
            if eff_id in self.ids:
                eff = self.ids[eff_id]
                eff.center = (eff.center_x + dx, eff.center_y + dy)

    # ---- Frame storage helpers ----
    def _capture_current_frame(self):
        def pos(eff_id):
            eff = self.ids.get(eff_id)
            return (eff.center_x, eff.center_y) if eff else (0, 0)

        return {
            'left_hand': pos('curr_hand_left'),
            'right_hand': pos('curr_hand_right'),
            'left_foot': pos('curr_foot_left'),
            'right_foot': pos('curr_foot_right'),
            'shoulder': pos('curr_shoulder'),
            'pelvis': pos('curr_pelvis'),
        }

    def _apply_frame_to_current(self, frame):
        self._loading_frame = True
        mapping = {
            'curr_hand_left': frame.get('left_hand'),
            'curr_hand_right': frame.get('right_hand'),
            'curr_foot_left': frame.get('left_foot'),
            'curr_foot_right': frame.get('right_foot'),
            'curr_shoulder': frame.get('shoulder'),
            'curr_pelvis': frame.get('pelvis'),
        }
        i = 0
        for eff_id, coords in mapping.items():
            if eff_id in self.ids and coords:
                self.ids[eff_id].center = coords

        if 'curr_pelvis' in self.ids:
            self._pelvis_prev = (self.ids.curr_pelvis.center_x,
                                self.ids.curr_pelvis.center_y)
        if 'curr_shoulder' in self.ids:
            self._shoulder_prev = (self.ids.curr_shoulder.center_x,
                                self.ids.curr_shoulder.center_y)

        self._foot_midpoint_base = self._current_foot_midpoint()
        if self._foot_midpoint_base and self._pelvis_prev:
            self._pelvis_offset_from_feet = (
                self._pelvis_prev[0] - self._foot_midpoint_base[0],
                self._pelvis_prev[1] - self._foot_midpoint_base[1],
            )
        
        self._loading_frame = False

    def _apply_frame_to_ghost(self, frame):
        ghost_layer = self.ids.get('ghost_layer')
        if not frame or not ghost_layer:
            if ghost_layer:
                ghost_layer.opacity = 0
            return

        ghost_layer.opacity = 0.35
        mapping = {
            'ghost_hand_left': frame.get('left_hand'),
            'ghost_hand_right': frame.get('right_hand'),
            'ghost_foot_left': frame.get('left_foot'),
            'ghost_foot_right': frame.get('right_foot'),
            'ghost_shoulder': frame.get('shoulder'),
            'ghost_pelvis': frame.get('pelvis'),
        }
        for eff_id, coords in mapping.items():
            if eff_id in self.ids and coords:
                self.ids[eff_id].center = coords

        if 'ghost_stick' in self.ids:
            ghost = self.ids.ghost_stick
            ghost.left_hand_x, ghost.left_hand_y = frame['left_hand']
            ghost.right_hand_x, ghost.right_hand_y = frame['right_hand']
            ghost.left_foot_x, ghost.left_foot_y = frame['left_foot']
            ghost.right_foot_x, ghost.right_foot_y = frame['right_foot']
            ghost.shoulder_x, ghost.shoulder_y = frame['shoulder']
            ghost.pelvis_x, ghost.pelvis_y = frame['pelvis']

    def _refresh_frame_meta(self):
        total = max(1, len(self.frames))
        self.frame_label = f"Frame {self.current_index + 1} / {total}"
        self.frame_choices = [str(i + 1) for i in range(total)]
        if 'frame_spinner' in self.ids:
            self.ids.frame_spinner.text = str(self.current_index + 1)

    def _save_current_to_list(self):
        if not self.frames:
            return
        self.frames[self.current_index] = self._capture_current_frame()

    def _load_frame(self, index):
        if not self.frames:
            return
        index = max(0, min(index, len(self.frames) - 1))
        self.current_index = index
        self._apply_frame_to_current(self.frames[index])
        prev_frame = self.frames[index - 1] if index > 0 else None
        self._apply_frame_to_ghost(prev_frame)
        self._refresh_frame_meta()

    def add_keyframe(self):
        self._save_current_to_list()
        new_frame = deepcopy(self.frames[self.current_index]) if self.frames else self._capture_current_frame()
        self.frames.append(new_frame)
        self._load_frame(len(self.frames) - 1)

    def next_frame(self):
        if not self.frames or self.current_index >= len(self.frames) - 1:
            return
        self._save_current_to_list()
        self._load_frame(self.current_index + 1)

    def prev_frame(self):
        if not self.frames or self.current_index <= 0:
            return
        self._save_current_to_list()
        self._load_frame(self.current_index - 1)

    def on_frame_chosen(self, text_value):
        try:
            idx = int(text_value) - 1
        except ValueError:
            return
        if 0 <= idx < len(self.frames) and self.current_index != idx:
            self._save_current_to_list()
            self._load_frame(idx)

    def clear_frames(self):
        self.frames = [deepcopy(self._initial_frame)] if self._initial_frame else [self._capture_current_frame()]
        self._load_frame(0)

    def remove_all_frames(self):
        self.clear_frames()

    def go_home(self):
        self._save_current_to_list()
        if self.manager:
            self.manager.current = 'home'

    def go_animation(self):
        self._save_current_to_list()
        if self.manager and 'animation' in self.manager.screen_names:
            self.manager.current = 'animation'
