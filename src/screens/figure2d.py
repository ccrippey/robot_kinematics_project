from kivy.clock import Clock
from kivy.uix.screenmanager import Screen


class Figure2D(Screen):
    PELVIS_FOLLOW_FACTOR = 0.35

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # State used to propagate motion up the kinematic chain
        self._pelvis_prev = None
        self._shoulder_prev = None
        self._foot_midpoint_base = None
        self._pelvis_offset_from_feet = (0, 0)
        self._suppress_pelvis_event = False
        self._suppress_shoulder_event = False

        # Bind end effectors to stick figure after widgets are created
        Clock.schedule_once(self._bind_end_effectors, 0)
    
    def _bind_end_effectors(self, dt):
        """Bind the end effector positions to the stick figure's IK system."""
        if hasattr(self.ids, 'sticky1'):
            stick = self.ids.sticky1
            
            # Bind hand positions
            if hasattr(self.ids, 'hand_left'):
                self.ids.hand_left.bind(center_x=lambda inst, val: setattr(stick, 'left_hand_x', val))
                self.ids.hand_left.bind(center_y=lambda inst, val: setattr(stick, 'left_hand_y', val))
                # Set initial position
                stick.left_hand_x = self.ids.hand_left.center_x
                stick.left_hand_y = self.ids.hand_left.center_y
            
            if hasattr(self.ids, 'hand_right'):
                self.ids.hand_right.bind(center_x=lambda inst, val: setattr(stick, 'right_hand_x', val))
                self.ids.hand_right.bind(center_y=lambda inst, val: setattr(stick, 'right_hand_y', val))
                # Set initial position
                stick.right_hand_x = self.ids.hand_right.center_x
                stick.right_hand_y = self.ids.hand_right.center_y
            
            # Bind foot positions
            if hasattr(self.ids, 'foot_left'):
                self.ids.foot_left.bind(center_x=lambda inst, val: setattr(stick, 'left_foot_x', val))
                self.ids.foot_left.bind(center_y=lambda inst, val: setattr(stick, 'left_foot_y', val))
                # Set initial position
                stick.left_foot_x = self.ids.foot_left.center_x
                stick.left_foot_y = self.ids.foot_left.center_y
            
            if hasattr(self.ids, 'foot_right'):
                self.ids.foot_right.bind(center_x=lambda inst, val: setattr(stick, 'right_foot_x', val))
                self.ids.foot_right.bind(center_y=lambda inst, val: setattr(stick, 'right_foot_y', val))
                # Set initial position
                stick.right_foot_x = self.ids.foot_right.center_x
                stick.right_foot_y = self.ids.foot_right.center_y
            
            # Bind shoulder position
            if hasattr(self.ids, 'shoulder'):
                self.ids.shoulder.bind(center_x=lambda inst, val: setattr(stick, 'shoulder_x', val))
                self.ids.shoulder.bind(center_y=lambda inst, val: setattr(stick, 'shoulder_y', val))
                # Set initial position
                stick.shoulder_x = self.ids.shoulder.center_x
                stick.shoulder_y = self.ids.shoulder.center_y
            
            # Bind pelvis position
            if hasattr(self.ids, 'pelvis'):
                self.ids.pelvis.bind(center_x=lambda inst, val: setattr(stick, 'pelvis_x', val))
                self.ids.pelvis.bind(center_y=lambda inst, val: setattr(stick, 'pelvis_y', val))
                # Set initial position
                stick.pelvis_x = self.ids.pelvis.center_x
                stick.pelvis_y = self.ids.pelvis.center_y

            self._initialize_motion_propagation()

    def _initialize_motion_propagation(self):
        """Capture the initial layout and hook propagation callbacks."""
        if hasattr(self.ids, 'pelvis'):
            self._pelvis_prev = (self.ids.pelvis.center_x, self.ids.pelvis.center_y)
        if hasattr(self.ids, 'shoulder'):
            self._shoulder_prev = (self.ids.shoulder.center_x, self.ids.shoulder.center_y)

        self._foot_midpoint_base = self._current_foot_midpoint()
        if self._foot_midpoint_base and self._pelvis_prev:
            self._pelvis_offset_from_feet = (
                self._pelvis_prev[0] - self._foot_midpoint_base[0],
                self._pelvis_prev[1] - self._foot_midpoint_base[1],
            )

        self._setup_propagation_bindings()

    def _setup_propagation_bindings(self):
        for eff_id in ('foot_left', 'foot_right'):
            if hasattr(self.ids, eff_id):
                eff = getattr(self.ids, eff_id)
                eff.bind(center_x=self._on_foot_moved, center_y=self._on_foot_moved)

        if hasattr(self.ids, 'pelvis'):
            self.ids.pelvis.bind(center_x=self._on_pelvis_moved, center_y=self._on_pelvis_moved)

        if hasattr(self.ids, 'shoulder'):
            self.ids.shoulder.bind(center_x=self._on_shoulder_moved, center_y=self._on_shoulder_moved)

    def _current_foot_midpoint(self):
        if hasattr(self.ids, 'foot_left') and hasattr(self.ids, 'foot_right'):
            left = self.ids.foot_left.center
            right = self.ids.foot_right.center
            return ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
        return None

    def _on_foot_moved(self, *args):
        """When a foot moves, pull the pelvis slightly toward the feet midpoint."""
        if not hasattr(self.ids, 'pelvis'):
            return

        foot_mid = self._current_foot_midpoint()
        if not foot_mid or self._pelvis_prev is None:
            return

        target_x = foot_mid[0] + self._pelvis_offset_from_feet[0]
        target_y = foot_mid[1] + self._pelvis_offset_from_feet[1]
        self._apply_pelvis_follow(target_x, target_y)

    def _apply_pelvis_follow(self, target_x, target_y):
        current_x, current_y = self.ids.pelvis.center
        dx = target_x - current_x
        dy = target_y - current_y
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            return

        new_x = current_x + dx * self.PELVIS_FOLLOW_FACTOR
        new_y = current_y + dy * self.PELVIS_FOLLOW_FACTOR
        self._set_pelvis_center(new_x, new_y, update_offset=False)

    def _on_pelvis_moved(self, *args):
        if self._suppress_pelvis_event or self._pelvis_prev is None:
            self._pelvis_prev = (self.ids.pelvis.center_x, self.ids.pelvis.center_y)
            return

        new_center = (self.ids.pelvis.center_x, self.ids.pelvis.center_y)
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
        self.ids.pelvis.center = (new_x, new_y)
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
        if not hasattr(self.ids, 'shoulder'):
            return

        cur_x, cur_y = self.ids.shoulder.center
        self._set_shoulder_center((cur_x + delta[0], cur_y + delta[1]))

    def _on_shoulder_moved(self, *args):
        if self._suppress_shoulder_event or self._shoulder_prev is None:
            self._shoulder_prev = (self.ids.shoulder.center_x, self.ids.shoulder.center_y)
            return

        new_center = (self.ids.shoulder.center_x, self.ids.shoulder.center_y)
        delta = (new_center[0] - self._shoulder_prev[0], new_center[1] - self._shoulder_prev[1])
        self._shoulder_prev = new_center

        if delta != (0, 0):
            self._move_hands_by(delta)

    def _set_shoulder_center(self, new_center):
        prev = self._shoulder_prev
        self._suppress_shoulder_event = True
        self.ids.shoulder.center = new_center
        self._suppress_shoulder_event = False

        self._shoulder_prev = new_center
        if prev:
            delta = (new_center[0] - prev[0], new_center[1] - prev[1])
            if delta != (0, 0):
                self._move_hands_by(delta)

    def _move_hands_by(self, delta):
        dx, dy = delta
        for eff_id in ('hand_left', 'hand_right'):
            if hasattr(self.ids, eff_id):
                eff = getattr(self.ids, eff_id)
                eff.center = (eff.center_x + dx, eff.center_y + dy)
