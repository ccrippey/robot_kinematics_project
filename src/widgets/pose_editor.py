"""Unified pose editor widget with motion propagation.

This widget provides the core pose editing functionality used by both
the free editor (Figure2D) and the keyframe editor (KeyframeEditor).
"""

from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, DictProperty
from kivy.clock import Clock


class PoseEditor(RelativeLayout):
    """Interactive pose editor with motion propagation.

    Provides draggable end effectors for hands, feet, shoulder, and pelvis
    with automatic motion propagation:
    - Feet movement → pelvis follows
    - Pelvis movement → shoulder follows
    - Shoulder movement → hands follow
    """

    projection_mode = NumericProperty(0.0)
    PELVIS_FOLLOW_FACTOR = 0.35

    # Effector IDs we expect to find in the widget tree
    EFFECTOR_IDS = {
        "hands": ["hand_left", "hand_right"],
        "feet": ["foot_left", "foot_right"],
        "joints": ["shoulder", "pelvis"],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Motion propagation state
        self._pelvis_prev = None
        self._shoulder_prev = None
        self._foot_midpoint_base = None
        self._pelvis_offset_from_feet = (0, 0)
        self._suppress_pelvis_event = False
        self._suppress_shoulder_event = False
        self._loading_pose = False

        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, dt):
        """Initialize after widget tree is built."""
        self._bind_end_effectors_to_stick()
        self._apply_projection_mode()
        self._initialize_motion_propagation()

    def _bind_end_effectors_to_stick(self):
        """Bind end effector 3D positions to stick figure IK system."""
        stick = self.ids["stick_figure"]
        stick.projection_mode = self.projection_mode
        self.bind(projection_mode=lambda inst, val: setattr(stick, "projection_mode", val))

        # Bind all effectors using mapping
        effector_mapping = {
            "hand_left": "left_hand_pos3d",
            "hand_right": "right_hand_pos3d",
            "foot_left": "left_foot_pos3d",
            "foot_right": "right_foot_pos3d",
            "shoulder": "shoulder_pos3d",
            "pelvis": "pelvis_pos3d",
        }

        for eff_id, stick_attr in effector_mapping.items():
            eff = self.ids[eff_id]
            eff.bind(pos3d=lambda inst, val, attr=stick_attr: setattr(stick, attr, val))
            setattr(stick, stick_attr, eff.pos3d)

    def _apply_projection_mode(self):
        """Apply current projection mode to all effectors and stick figure."""
        all_effectors = sum(self.EFFECTOR_IDS.values(), [])
        for eff_id in all_effectors:
            eff = self.ids[eff_id]
            eff.projection_mode = self.projection_mode

    def on_projection_mode(self, instance, value):
        """Handle projection mode changes."""
        if self._loading_pose:
            return
        # Reset motion propagation state when view angle changes
        self._pelvis_prev = None
        self._shoulder_prev = None
        self._foot_midpoint_base = None
        self._loading_pose = True
        self.projection_mode = value
        self._apply_projection_mode()
        self._loading_pose = False

    def _initialize_motion_propagation(self):
        """Set up motion propagation between effectors."""
        pelvis = self.ids["pelvis"]
        shoulder = self.ids["shoulder"]

        self._pelvis_prev = pelvis.center
        self._shoulder_prev = shoulder.center
        self._foot_midpoint_base = self._current_foot_midpoint()

        if self._foot_midpoint_base and self._pelvis_prev:
            self._pelvis_offset_from_feet = (
                self._pelvis_prev[0] - self._foot_midpoint_base[0],
                self._pelvis_prev[1] - self._foot_midpoint_base[1],
            )

        self._setup_propagation_bindings()

    def _setup_propagation_bindings(self):
        """Bind motion propagation callbacks."""
        for foot_id in self.EFFECTOR_IDS["feet"]:
            foot = self.ids[foot_id]
            foot.bind(center_x=self._on_foot_moved, center_y=self._on_foot_moved)

        pelvis = self.ids["pelvis"]
        pelvis.bind(center_x=self._on_pelvis_moved, center_y=self._on_pelvis_moved)

        shoulder = self.ids["shoulder"]
        shoulder.bind(center_x=self._on_shoulder_moved, center_y=self._on_shoulder_moved)

    def _current_foot_midpoint(self):
        """Calculate midpoint between left and right feet."""
        left = self.ids["foot_left"].center
        right = self.ids["foot_right"].center
        return ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)

    def _on_foot_moved(self, *args):
        """When feet move, pull pelvis toward the feet midpoint."""
        if self._loading_pose:
            return

        foot_mid = self._current_foot_midpoint()
        if not foot_mid or self._pelvis_prev is None:
            return

        target_x = foot_mid[0] + self._pelvis_offset_from_feet[0]
        target_y = foot_mid[1] + self._pelvis_offset_from_feet[1]
        self._apply_pelvis_follow(target_x, target_y)

    def _apply_pelvis_follow(self, target_x, target_y):
        """Move pelvis partially toward target position."""
        pelvis = self.ids["pelvis"]
        current_x, current_y = pelvis.center
        dx = target_x - current_x
        dy = target_y - current_y

        if abs(dx) < 0.01 and abs(dy) < 0.01:
            return

        new_x = current_x + dx * self.PELVIS_FOLLOW_FACTOR
        new_y = current_y + dy * self.PELVIS_FOLLOW_FACTOR
        self._set_pelvis_center(new_x, new_y, update_offset=False)

    def _on_pelvis_moved(self, *args):
        """When pelvis moves, update shoulder and recalculate offsets."""
        if self._loading_pose or self._suppress_pelvis_event:
            pelvis = self.ids["pelvis"]
            self._pelvis_prev = pelvis.center
            return

        pelvis = self.ids["pelvis"]
        new_center = pelvis.center
        delta = (new_center[0] - self._pelvis_prev[0], new_center[1] - self._pelvis_prev[1])
        self._pelvis_prev = new_center

        if delta == (0, 0):
            return

        # Update offset from feet
        foot_mid = self._current_foot_midpoint()
        if foot_mid:
            self._pelvis_offset_from_feet = (new_center[0] - foot_mid[0], new_center[1] - foot_mid[1])

        self._move_shoulders_by(delta)

    def _set_pelvis_center(self, new_x, new_y, update_offset):
        """Set pelvis center with event suppression."""
        pelvis = self.ids["pelvis"]
        prev = self._pelvis_prev

        self._suppress_pelvis_event = True
        pelvis.center = (new_x, new_y)
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
        """Move shoulder by delta amount."""
        if self._loading_pose:
            return

        shoulder = self.ids["shoulder"]
        cur_x, cur_y = shoulder.center
        self._set_shoulder_center((cur_x + delta[0], cur_y + delta[1]))

    def _on_shoulder_moved(self, *args):
        """When shoulder moves, propagate to hands."""
        if self._loading_pose or self._suppress_shoulder_event:
            shoulder = self.ids["shoulder"]
            self._shoulder_prev = shoulder.center
            return

        shoulder = self.ids["shoulder"]
        new_center = shoulder.center
        delta = (new_center[0] - self._shoulder_prev[0], new_center[1] - self._shoulder_prev[1])
        self._shoulder_prev = new_center

        if delta != (0, 0):
            self._move_hands_by(delta)

    def _set_shoulder_center(self, new_center):
        """Set shoulder center with event suppression."""
        shoulder = self.ids["shoulder"]
        prev = self._shoulder_prev

        self._suppress_shoulder_event = True
        shoulder.center = new_center
        self._suppress_shoulder_event = False

        self._shoulder_prev = new_center
        if prev:
            delta = (new_center[0] - prev[0], new_center[1] - prev[1])
            if delta != (0, 0):
                self._move_hands_by(delta)

    def _move_hands_by(self, delta):
        """Move both hands by delta amount."""
        if self._loading_pose:
            return

        dx, dy = delta
        for hand_id in self.EFFECTOR_IDS["hands"]:
            hand = self.ids[hand_id]
            hand.center = (hand.center_x + dx, hand.center_y + dy)

    def capture_pose(self):
        """Capture current pose as a dictionary of 3D positions."""
        pose = {}
        for eff_id in sum(self.EFFECTOR_IDS.values(), []):
            pose[eff_id] = list(self.ids[eff_id].pos3d)
        return pose

    def load_pose(self, pose):
        """Load a pose from a dictionary of 3D positions."""
        self._loading_pose = True

        for eff_id, pos3d in pose.items():
            if eff_id in self.ids:
                self.ids[eff_id].pos3d = pos3d

        # Reset motion propagation state
        pelvis = self.ids["pelvis"]
        shoulder = self.ids["shoulder"]
        self._pelvis_prev = pelvis.center
        self._shoulder_prev = shoulder.center
        self._foot_midpoint_base = self._current_foot_midpoint()

        if self._foot_midpoint_base and self._pelvis_prev:
            self._pelvis_offset_from_feet = (
                self._pelvis_prev[0] - self._foot_midpoint_base[0],
                self._pelvis_prev[1] - self._foot_midpoint_base[1],
            )

        self._loading_pose = False
