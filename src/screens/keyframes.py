from copy import deepcopy

from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen


class KeyframeEditor(Screen):
    """Screen that lets users edit multiple stick-figure keyframes."""

    projection_mode = NumericProperty(0.0)
    frame_label = StringProperty("Frame 1 / 1")
    frame_choices = ListProperty(["1"])
    current_index = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frames = []
        self._initial_frame = None
        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, dt):
        """Initialize after widget tree is built."""
        # Sync projection mode with pose editors
        for pose_id in ["current_pose", "ghost_pose"]:
            pose_editor = self.ids[pose_id]
            pose_editor.projection_mode = self.projection_mode
            self.bind(projection_mode=lambda inst, val, p=pose_editor: setattr(p, "projection_mode", val))

        # Configure ghost pose (non-draggable, gray appearance)
        ghost_pose = self.ids["ghost_pose"]
        for eff_id in sum(ghost_pose.EFFECTOR_IDS.values(), []):
            eff = ghost_pose.ids[eff_id]
            eff.draggable = False
            eff.color = (0.6, 0.6, 0.6, 0.6)
        ghost_pose.ids["stick_figure"].opacity = 0.6

        # Capture the starting pose as frame 1
        self._initial_frame = self.ids["current_pose"].capture_pose()
        self.frames = [deepcopy(self._initial_frame)]
        self._refresh_frame_meta()
        self._load_frame(0)

    def _refresh_frame_meta(self):
        """Update frame counter and spinner choices."""
        total = max(1, len(self.frames))
        self.frame_label = f"Frame {self.current_index + 1} / {total}"
        self.frame_choices = [str(i + 1) for i in range(total)]
        if "frame_spinner" in self.ids:
            self.ids.frame_spinner.text = str(self.current_index + 1)

    def _save_current_to_list(self):
        """Save current pose to the frame list."""
        if not self.frames:
            return
        self.frames[self.current_index] = self.ids["current_pose"].capture_pose()

    def _load_frame(self, index):
        """Load a frame by index."""
        if not self.frames:
            return
        index = max(0, min(index, len(self.frames) - 1))
        self.current_index = index

        # Load current frame
        self.ids["current_pose"].load_pose(self.frames[index])

        # Load previous frame into ghost
        prev_frame = self.frames[index - 1] if index > 0 else None
        if prev_frame:
            self.ids["ghost_layer"].opacity = 0.35
            self.ids["ghost_pose"].load_pose(prev_frame)
        else:
            self.ids["ghost_layer"].opacity = 0

        self._refresh_frame_meta()

    def add_keyframe(self):
        """Add a new keyframe after the current one."""
        self._save_current_to_list()
        new_frame = (
            deepcopy(self.frames[self.current_index]) if self.frames else self.ids["current_pose"].capture_pose()
        )
        self.frames.append(new_frame)
        self._load_frame(len(self.frames) - 1)

    def next_frame(self):
        """Navigate to next frame."""
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
        """Reset to a single frame (the initial pose)."""
        self.frames = (
            [deepcopy(self._initial_frame)] if self._initial_frame else [self.ids["current_pose"].capture_pose()]
        )
        self._load_frame(0)

    def go_home(self):
        self._save_current_to_list()
        if self.manager:
            self.manager.current = "home"

    def go_animation(self):
        self._save_current_to_list()
        if self.manager and "animation" in self.manager.screen_names:
            self.manager.current = "animation"
