from copy import deepcopy
from dataclasses import dataclass
from enum import Enum

from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen

from ..kinematics.interpolation import (
    INTERPOLATION_MODES,
    INTERPOLATION_SPACES,
    InterpolationMode,
    InterpolationSpace,
    InterpolationSettings,
)


class KeyframeEditor(Screen):
    """Screen that lets users edit multiple stick-figure keyframes."""

    projection_mode = NumericProperty(0.0)
    frame_label = StringProperty("Frame 1 / 1")
    frame_choices = ListProperty(["1"])
    current_index = NumericProperty(0)
    current_time = NumericProperty(0.0)
    current_interp_before = StringProperty("None")
    current_interp_after = StringProperty("None")
    current_space_before = StringProperty("Joint")
    current_space_after = StringProperty("Joint")
    interp_choices = ListProperty(INTERPOLATION_MODES)
    space_choices = ListProperty(INTERPOLATION_SPACES)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frames = []  # List of CartesianStickConfig
        self.frame_times = []  # Time in seconds for each frame
        self.frame_interps = []  # InterpolationSettings before each frame
        self._initial_frame = None
        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, dt):
        """Initialize after widget tree is built."""
        # Sync projection mode with pose editors
        # for pose_id in ["current_pose", "ghost_pose"]:
        #     pose_editor = self.ids[pose_id]
        #     pose_editor.projection_mode = self.projection_mode
        #     self.bind(projection_mode=lambda inst, val, p=pose_editor: setattr(p, "projection_mode", val))

        # Configure ghost pose (non-draggable, gray appearance)
        ghost_pose = self.ids["ghost_pose"]
        for eff_id in ghost_pose.EFFECTOR_IDS:
            eff = ghost_pose.ids[eff_id]
            eff.draggable = False
            eff.color = (0.6, 0.6, 0.6, 0.6)
        ghost_pose.ids["stick_figure"].opacity = 0.6

        # Capture the starting pose as frame 1
        self._initial_frame = self.ids["current_pose"].capture_pose()
        self.frames = [deepcopy(self._initial_frame)]
        self.frame_times = [0.0]  # First frame always at t=0
        self.frame_interps = [
            InterpolationSettings(InterpolationMode.NONE, InterpolationSpace.JOINT)
        ]  # First frame has no interpolation before it
        self._refresh_frame_meta()
        self._load_frame(0)

    def _refresh_frame_meta(self):
        """Update frame counter and spinner choices."""
        total = max(1, len(self.frames))
        self.frame_label = f"Frame {self.current_index + 1} / {total}"
        self.frame_choices = [str(i + 1) for i in range(total)] + ["+ New Keyframe"]
        if "frame_spinner" in self.ids:
            self.ids.frame_spinner.text = str(self.current_index + 1)

        # Update time and interpolation UI
        self._update_time_interp_ui()

    def _save_current_to_list(self):
        """Save current pose to the frame list."""
        if not self.frames:
            return
        self.frames[self.current_index] = self.ids["current_pose"].capture_pose()
        # Time and interpolation are saved via their on_change handlers

    def _load_frame(self, index):
        """Load a frame by index."""
        if not self.frames:
            return
        index = max(0, min(index, len(self.frames) - 1))
        self.current_index = index

        # Load current frame
        self.ids["current_pose"].load_cart(self.frames[index])

        # Load previous frame into ghost
        prev_frame = self.frames[index - 1] if index > 0 else None
        if prev_frame:
            self.ids["ghost_layer"].opacity = 0.35
            self.ids["ghost_pose"].load_cart(prev_frame)
        else:
            self.ids["ghost_layer"].opacity = 0

        # Load time and interpolation for this frame
        self.current_time = self.frame_times[index]
        self.current_interp_before = self.frame_interps[index].mode.value
        self.current_space_before = self.frame_interps[index].space.value

        # Set interp_after (interpolation to next frame)
        if index < len(self.frames) - 1:
            self.current_interp_after = self.frame_interps[index + 1].mode.value
            self.current_space_after = self.frame_interps[index + 1].space.value
        else:
            self.current_interp_after = "None"
            self.current_space_after = "Joint"

        self._refresh_frame_meta()

    def add_keyframe(self):
        """Add a new keyframe after the current one."""
        self._save_current_to_list()
        new_frame = (
            deepcopy(self.frames[self.current_index]) if self.frames else self.ids["current_pose"].capture_pose()
        )
        self.frames.append(new_frame)

        # New frame gets time 1 second after current, with Linear interpolation
        new_time = self.frame_times[self.current_index] + 1.0 if self.frame_times else 1.0
        self.frame_times.append(new_time)
        self.frame_interps.append(InterpolationSettings(InterpolationMode.LINEAR, InterpolationSpace.JOINT))

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
        # Handle "+ New Keyframe" option
        if text_value == "+ New Keyframe":
            self.add_keyframe()
            return

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
        self.frame_times = [0.0]
        self.frame_interps = [InterpolationSettings(InterpolationMode.NONE, InterpolationSpace.JOINT)]
        self._load_frame(0)

    def go_home(self):
        self._save_current_to_list()
        if self.manager:
            self.manager.current = "home"

    def go_animation(self):
        self._save_current_to_list()
        if self.manager and "animation" in self.manager.screen_names:
            self.manager.current = "animation"

    def _update_time_interp_ui(self):
        """Update time and interpolation UI widgets based on current frame."""
        if not self.frames:
            return

        # Enable/disable time input (first frame is always 0)
        is_first = self.current_index == 0
        is_last = self.current_index == len(self.frames) - 1
        self.ids.time_input.disabled = is_first

        # Enable/disable interpolation before spinners (first frame has None)
        self.ids.interp_before_spinner.disabled = is_first
        self.ids.space_before_spinner.disabled = is_first
        if is_first:
            self.ids.interp_before_spinner.text = "None"
            self.ids.space_before_spinner.text = "Joint"

        # Enable/disable interpolation after spinners (last frame has None)
        self.ids.interp_after_spinner.disabled = is_last
        self.ids.space_after_spinner.disabled = is_last
        if is_last:
            self.ids.interp_after_spinner.text = "None"
            self.ids.space_after_spinner.text = "Joint"

    def on_time_changed(self, text_value):
        """Handle user changing the time value."""
        if self.current_index == 0:
            # First frame is always at t=0
            return

        try:
            new_time = float(text_value)
        except ValueError:
            return

        # Validate: must be after previous frame
        if self.current_index > 0:
            prev_time = self.frame_times[self.current_index - 1]
            if new_time <= prev_time:
                new_time = prev_time + 0.01  # Minimum gap

        # Validate: must be before next frame
        if self.current_index < len(self.frames) - 1:
            next_time = self.frame_times[self.current_index + 1]
            if new_time >= next_time:
                new_time = next_time - 0.01  # Minimum gap

        self.frame_times[self.current_index] = new_time
        self.current_time = new_time

        # Update the text input to show validated value
        if "time_input" in self.ids:
            self.ids.time_input.text = f"{new_time:.2f}"

    def on_interp_before_changed(self, text_value):
        """Handle user changing the interpolation mode before this frame."""
        if self.current_index == 0:
            return

        mode = InterpolationMode[text_value.upper()]
        self.frame_interps[self.current_index].mode = mode
        self.current_interp_before = text_value

    def on_space_before_changed(self, text_value):
        """Handle user changing the interpolation space before this frame."""
        if self.current_index == 0:
            return

        space = InterpolationSpace[text_value.upper()]
        self.frame_interps[self.current_index].space = space
        self.current_space_before = text_value

    def on_interp_after_changed(self, text_value):
        """Handle user changing the interpolation mode after this frame."""
        if self.current_index >= len(self.frames) - 1:
            return

        mode = InterpolationMode[text_value.upper()]
        self.frame_interps[self.current_index + 1].mode = mode
        self.current_interp_after = text_value

    def on_space_after_changed(self, text_value):
        """Handle user changing the interpolation space after this frame."""
        if self.current_index >= len(self.frames) - 1:
            return

        space = InterpolationSpace[text_value.upper()]
        self.frame_interps[self.current_index + 1].space = space
        self.current_space_after = text_value
