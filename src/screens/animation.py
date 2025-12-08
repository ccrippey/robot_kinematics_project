"""Animation playback screen with precomputed trajectories."""

from typing import List
import numpy as np
from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window

from ..kinematics.interpolation import create_interpolator, InterpolationMode, InterpolationSpace
from ..kinematics.inverse_kinematics import cart_to_joint_config
from ..kinematics.stick_config import CartesianStickConfig, JointStickConfig, JointLimbConfig, LIMB_LENGTH_RATIOS


class AnimationScreen(Screen):
    """Animation playback screen that reads keyframes from KeyframeEditor."""

    # Playback state
    current_time = NumericProperty(0.0)
    current_frame_index = NumericProperty(0)
    current_keyframe_index = NumericProperty(0)
    is_playing = BooleanProperty(False)

    # Display properties
    time_display = StringProperty("0.00s")
    frame_display = StringProperty("Frame 1 / 1")
    total_duration = NumericProperty(0.0)

    # Configuration
    TARGET_FPS = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frame_times = None  # Numpy array of all frame times
        self.frame_configs_cart = None  # Array of CartesianStickConfig (for Cartesian interp)
        self.frame_configs_joint = None  # Array of JointStickConfig (for Joint interp)
        self.keyframe_indices = []
        self.keyframe_times = []
        self._playback_event = None

    def on_pre_enter(self):
        """Called before screen is displayed - precompute animation."""
        kf_screen = self.manager.get_screen("keyframes")
        self.keyframes = kf_screen.frames  # List of CartesianStickConfig
        self.keyframe_times = kf_screen.frame_times
        self.keyframe_interps = kf_screen.frame_interps

        if len(self.keyframes) < 2:
            self.frame_times = np.array([0.0])
            self.frame_configs_cart = [self.keyframes[0]] if self.keyframes else []
            self.keyframe_indices = [0]
            self.total_duration = 0.0
        else:
            self._precompute_animation()

        self._update_displays()

    def on_leave(self):
        """Stop playback when leaving screen."""
        self.pause_playback()

    def _precompute_animation(self):
        """Precompute all animation frames at target FPS using vectorized operations."""
        self.total_duration = self.keyframe_times[-1]
        num_frames = int(self.total_duration * self.TARGET_FPS) + 1
        self.frame_times = np.linspace(0, self.total_duration, num_frames)

        # Find keyframe indices using vectorized argmin
        self.keyframe_indices = np.argmin(
            np.abs(self.frame_times[:, np.newaxis] - np.array(self.keyframe_times)), axis=0
        ).tolist()

        # Precompute configs for all frames by segment
        self.frame_configs_cart = []
        self.frame_configs_joint = []

        for seg_idx in range(len(self.keyframes) - 1):
            t0, t1 = self.keyframe_times[seg_idx], self.keyframe_times[seg_idx + 1]
            interp_settings = self.keyframe_interps[seg_idx + 1]

            # Find all frames in this segment
            mask = (self.frame_times >= t0) & (self.frame_times <= t1)
            segment_times = self.frame_times[mask]

            if interp_settings.mode == InterpolationMode.NONE:
                # Repeat first pose
                for _ in range(len(segment_times)):
                    self.frame_configs_cart.append(self.keyframes[seg_idx])
                    self.frame_configs_joint.append(None)  # Will convert on-demand
            elif interp_settings.space == InterpolationSpace.CARTESIAN:
                configs = self._interpolate_cartesian_segment(
                    self.keyframes[seg_idx], self.keyframes[seg_idx + 1], t0, t1, segment_times, interp_settings.mode
                )
                self.frame_configs_cart.extend(configs)
                self.frame_configs_joint.extend([None] * len(configs))
            else:  # JOINT space
                configs = self._interpolate_joint_segment(
                    self.keyframes[seg_idx], self.keyframes[seg_idx + 1], t0, t1, segment_times, interp_settings.mode
                )
                self.frame_configs_cart.extend([None] * len(configs))
                self.frame_configs_joint.extend(configs)

            # Remove duplicates at segment boundaries
            if seg_idx > 0:
                if self.frame_configs_cart and self.frame_configs_cart[-len(segment_times)] is not None:
                    self.frame_configs_cart.pop(-len(segment_times))
                    self.frame_configs_joint.pop(-len(segment_times))
                elif self.frame_configs_joint and self.frame_configs_joint[-len(segment_times)] is not None:
                    self.frame_configs_cart.pop(-len(segment_times))
                    self.frame_configs_joint.pop(-len(segment_times))

    def _interpolate_cartesian_segment(
        self,
        config0: CartesianStickConfig,
        config1: CartesianStickConfig,
        t0: float,
        t1: float,
        times: np.ndarray,
        mode: InterpolationMode,
    ) -> List[CartesianStickConfig]:
        """Interpolate Cartesian positions for all frames in segment.

        Returns: list of CartesianStickConfig objects
        """
        # Convert configs to numpy arrays for interpolation
        p0 = config0.to_numpy().flatten()  # Shape: (18,) from (6, 3)
        p1 = config1.to_numpy().flatten()

        # Create interpolator for all 18 parameters
        interp = create_interpolator(mode.value, t0, t1, p0, p1)
        result_flat = interp.interpolate(times)  # Shape: (n_times, 18)

        # Convert back to configs
        configs = []
        for i in range(len(times)):
            pose_array = result_flat[i].reshape(6, 3)
            configs.append(CartesianStickConfig.from_numpy(pose_array))

        return configs

    def _interpolate_joint_segment(
        self,
        config0: CartesianStickConfig,
        config1: CartesianStickConfig,
        t0: float,
        t1: float,
        times: np.ndarray,
        mode: InterpolationMode,
    ) -> List[JointStickConfig]:
        """Interpolate in joint space for all frames in segment.

        Returns: list of JointStickConfig objects
        """
        # Convert both configs to joint space
        joint0 = cart_to_joint_config(config0)
        joint1 = cart_to_joint_config(config1)

        # Convert to numpy for interpolation
        j0 = joint0.to_numpy()  # Shape: (22,)
        j1 = joint1.to_numpy()

        # Interpolate all joint parameters at once
        interp = create_interpolator(mode.value, t0, t1, j0, j1)
        joints_interp = interp.interpolate(times)  # Shape: (n_times, 22)

        # Convert back to configs
        configs = []
        for i in range(len(times)):
            configs.append(JointStickConfig.from_numpy(joints_interp[i]))

        return configs

    def _update_displays(self):
        """Update time and frame displays."""
        self.time_display = f"{self.current_time:.2f}s"
        if self.frame_times is not None and len(self.frame_times) > 0:
            self.frame_display = f"Frame {self.current_frame_index + 1} / {len(self.frame_times)}"
        else:
            self.frame_display = "No animation"

    def _load_frame(self, frame_idx: int):
        """Load a specific frame into the stick viewer."""
        if frame_idx >= len(self.frame_configs_cart) or frame_idx >= len(self.frame_configs_joint):
            return

        # Use whichever config is available (Cartesian or Joint)
        if self.frame_configs_cart[frame_idx] is not None:
            self.ids["stick_viewer"].load_cart(self.frame_configs_cart[frame_idx])
        elif self.frame_configs_joint[frame_idx] is not None:
            self.ids["stick_viewer"].load_joint(self.frame_configs_joint[frame_idx])

    def play_pause(self):
        """Toggle play/pause."""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """Start animation playback."""
        if self.frame_times is None or len(self.frame_times) <= 1:
            return
        self.is_playing = True
        self._playback_event = Clock.schedule_interval(self._advance_frame, 1.0 / self.TARGET_FPS)

    def pause_playback(self):
        """Pause animation playback."""
        self.is_playing = False
        if self._playback_event:
            self._playback_event.cancel()
            self._playback_event = None

    def _advance_frame(self, dt):
        """Advance to next frame during playback."""
        self.current_time += dt
        if self.current_time > self.total_duration:
            self.current_time = 0.0

        self.current_frame_index = min(
            int(np.searchsorted(self.frame_times, self.current_time)), len(self.frame_times) - 1
        )
        self.current_keyframe_index = int(np.searchsorted(self.keyframe_times, self.current_time))

        self._load_frame(self.current_frame_index)
        self._update_displays()

    def seek_to_time(self, time: float):
        """Seek to specific time."""
        self.current_time = float(np.clip(time, 0.0, self.total_duration))
        self.current_frame_index = int(np.searchsorted(self.frame_times, self.current_time))
        self.current_frame_index = min(self.current_frame_index, len(self.frame_times) - 1)
        self.current_keyframe_index = int(np.searchsorted(self.keyframe_times, self.current_time))
        self._load_frame(self.current_frame_index)
        self._update_displays()

    def skip_to_start(self):
        """Skip to beginning."""
        self.seek_to_time(0.0)

    def skip_to_end(self):
        """Skip to end."""
        self.seek_to_time(self.total_duration)

    def prev_keyframe(self):
        """Skip to previous keyframe using current_keyframe_index."""
        if self.current_keyframe_index > 0:
            self.seek_to_time(self.keyframe_times[self.current_keyframe_index - 1])

    def next_keyframe(self):
        """Skip to next keyframe using current_keyframe_index."""
        if self.current_keyframe_index < len(self.keyframe_times) - 1:
            self.seek_to_time(self.keyframe_times[self.current_keyframe_index + 1])

    def on_time_input(self, text):
        """Handle manual time entry."""
        try:
            self.seek_to_time(float(text))
        except ValueError:
            pass

    def go_home(self):
        """Return to home screen."""
        self.pause_playback()
        self.manager.current = "home"

    def go_keyframes(self):
        """Return to keyframe editor."""
        self.pause_playback()
        self.manager.current = "keyframes"
