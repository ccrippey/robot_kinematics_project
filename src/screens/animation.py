"""Animation playback screen with precomputed trajectories."""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List
from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window

from ..kinematics.interpolation import create_interpolator, InterpolationMode, InterpolationSpace
from ..kinematics.inverse_kinematics import inverse_kinematics_3D_2link, choose_best_solution_3d
from ..kinematics.forward_kinematics import forward_kinematics_3D_2link


@dataclass
class LimbConfig:
    """Configuration for a limb - source of truth from stick_figure.kv."""

    a1_ratio: float  # Ratio of height
    a2_ratio: float
    origin_key: str  # "shoulder" or "pelvis"
    target_key: str  # "hand_left", etc.
    name: str  # "left_arm", etc.


# Limb configurations matching stick_figure.kv
LIMB_CONFIGS = [
    LimbConfig(0.14, 0.12, "shoulder", "hand_left", "left_arm"),
    LimbConfig(0.14, 0.12, "shoulder", "hand_right", "right_arm"),
    LimbConfig(0.15, 0.14, "pelvis", "foot_left", "left_leg"),
    LimbConfig(0.15, 0.14, "pelvis", "foot_right", "right_leg"),
]


class AnimationScreen(Screen):
    """Animation playback screen that reads keyframes from KeyframeEditor."""

    # Playback state
    current_time = NumericProperty(0.0)
    current_frame_index = NumericProperty(0)
    current_keyframe_index = NumericProperty(0)  # Index into keyframe_times
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
        self.frame_poses = None  # Numpy array shape (n_frames, n_effectors, 3)
        self.keyframe_indices = []  # Frame indices where keyframes occur
        self.keyframe_times = []  # Times of keyframes
        self._playback_event = None

    def on_pre_enter(self):
        """Called before screen is displayed - precompute animation."""
        kf_screen = self.manager.get_screen("keyframes")
        self.keyframes = kf_screen.frames
        self.keyframe_times = kf_screen.frame_times
        self.keyframe_interps = kf_screen.frame_interps

        if len(self.keyframes) < 2:
            self.frame_times = np.array([0.0])
            self.frame_poses = self._poses_to_array([self.keyframes[0]]) if self.keyframes else np.zeros((1, 6, 3))
            self.keyframe_indices = [0]
            self.total_duration = 0.0
        else:
            self._precompute_animation()

        self._update_displays()

    def on_leave(self):
        """Stop playback when leaving screen."""
        self.pause_playback()

    def _poses_to_array(self, pose_dicts: List[Dict]) -> np.ndarray:
        """Convert list of pose dicts to numpy array (n_poses, 6, 3).

        Effector order: shoulder, pelvis, hand_left, hand_right, foot_left, foot_right
        """
        effector_keys = ["shoulder", "pelvis", "hand_left", "hand_right", "foot_left", "foot_right"]
        return np.array([[pose[key] for key in effector_keys] for pose in pose_dicts])

    def _array_to_pose(self, pose_array: np.ndarray) -> Dict:
        """Convert numpy array (6, 3) back to pose dict."""
        effector_keys = ["shoulder", "pelvis", "hand_left", "hand_right", "foot_left", "foot_right"]
        return {key: pose_array[i].tolist() for i, key in enumerate(effector_keys)}

    def _get_limb_lengths(self) -> np.ndarray:
        """Get a1, a2 for all limbs based on current window size.

        Returns: array shape (4, 2) for [left_arm, right_arm, left_leg, right_leg]
        """
        height = Window.height
        return np.array([[cfg.a1_ratio * height, cfg.a2_ratio * height] for cfg in LIMB_CONFIGS])

    def _precompute_animation(self):
        """Precompute all animation frames at target FPS using vectorized operations."""
        self.total_duration = self.keyframe_times[-1]
        num_frames = int(self.total_duration * self.TARGET_FPS) + 1
        self.frame_times = np.linspace(0, self.total_duration, num_frames)

        # Find keyframe indices using vectorized argmin
        self.keyframe_indices = np.argmin(
            np.abs(self.frame_times[:, np.newaxis] - np.array(self.keyframe_times)), axis=0
        ).tolist()

        # Precompute poses for all frames by segment
        all_poses = []
        for seg_idx in range(len(self.keyframes) - 1):
            t0, t1 = self.keyframe_times[seg_idx], self.keyframe_times[seg_idx + 1]
            interp_settings = self.keyframe_interps[seg_idx + 1]

            # Find all frames in this segment
            mask = (self.frame_times >= t0) & (self.frame_times <= t1)
            segment_times = self.frame_times[mask]

            if interp_settings.mode == InterpolationMode.NONE:
                # Repeat first pose
                poses = np.tile(self._poses_to_array([self.keyframes[seg_idx]])[0], (len(segment_times), 1, 1))
            elif interp_settings.space == InterpolationSpace.CARTESIAN:
                poses = self._interpolate_cartesian_segment(
                    self.keyframes[seg_idx], self.keyframes[seg_idx + 1], t0, t1, segment_times, interp_settings.mode
                )
            else:  # JOINT space
                poses = self._interpolate_joint_segment(
                    self.keyframes[seg_idx], self.keyframes[seg_idx + 1], t0, t1, segment_times, interp_settings.mode
                )

            # Avoid duplicating frames at segment boundaries
            if seg_idx > 0:
                poses = poses[1:]
            all_poses.append(poses)

        self.frame_poses = np.vstack(all_poses)

    def _interpolate_cartesian_segment(
        self, pose0: Dict, pose1: Dict, t0: float, t1: float, times: np.ndarray, mode: InterpolationMode
    ) -> np.ndarray:
        """Interpolate Cartesian positions for all frames in segment.

        Returns: array shape (n_times, 6, 3)
        """
        p0 = self._poses_to_array([pose0])[0]  # Shape: (6, 3)
        p1 = self._poses_to_array([pose1])[0]

        # Create interpolator for all 18 parameters (6 effectors * 3 coords)
        p0_flat = p0.flatten()  # Shape: (18,)
        p1_flat = p1.flatten()

        interp = create_interpolator(mode.value, t0, t1, p0_flat, p1_flat)
        result_flat = interp.interpolate(times)  # Shape: (n_times, 18)

        return result_flat.reshape(-1, 6, 3)

    def _interpolate_joint_segment(
        self, pose0: Dict, pose1: Dict, t0: float, t1: float, times: np.ndarray, mode: InterpolationMode
    ) -> np.ndarray:
        """Interpolate in joint space for all frames in segment.

        Returns: array shape (n_times, 6, 3)
        """
        # Convert both poses to joint parameters
        joints0 = self._pose_to_joints(pose0)  # Shape: (10,) - [4 limbs * 2 angles + 6 origin coords]
        joints1 = self._pose_to_joints(pose1)

        # Interpolate all joint parameters at once
        interp = create_interpolator(mode.value, t0, t1, joints0, joints1)
        joints_interp = interp.interpolate(times)  # Shape: (n_times, 10)

        # Convert back to Cartesian for all frames
        return self._joints_to_poses(joints_interp, pose0)

    def _pose_to_joints(self, pose: Dict) -> np.ndarray:
        """Convert pose to joint parameters using 3D IK.

        Returns: array shape (10,) containing:
          - 4 hip_yaw angles
          - 4 hip_pitch angles
          - 4 hip_roll angles
          - 4 knee_pitch angles
          - 6 origin coordinates (shoulder x,y,z, pelvis x,y,z)
        """
        limb_lengths = self._get_limb_lengths()
        scale = 2.0 / (Window.width + Window.height)

        joint_angles = []
        for cfg, (a1, a2) in zip(LIMB_CONFIGS, limb_lengths):
            origin = np.array(pose[cfg.origin_key])
            target = np.array(pose[cfg.target_key])

            solutions = inverse_kinematics_3D_2link(a1 * scale, a2 * scale, origin, target)
            hip_yaw, hip_pitch, hip_roll, knee_pitch = choose_best_solution_3d(solutions, cfg.name)
            joint_angles.extend([hip_yaw, hip_pitch, hip_roll, knee_pitch])

        # Append origin positions
        shoulder = pose["shoulder"]
        pelvis = pose["pelvis"]
        return np.array(joint_angles + shoulder + pelvis)

    def _joints_to_poses(self, joints_array: np.ndarray, reference_pose: Dict) -> np.ndarray:
        """Convert joint parameters to Cartesian poses using 3D FK.

        Args:
            joints_array: shape (n_times, 22) - joint angles + origins
            reference_pose: for z-coordinate fallback

        Returns: array shape (n_times, 6, 3)
        """
        n_times = joints_array.shape[0]
        poses = np.zeros((n_times, 6, 3))
        limb_lengths = self._get_limb_lengths()
        scale = 2.0 / (Window.width + Window.height)

        for t_idx in range(n_times):
            joints = joints_array[t_idx]

            # Extract origins
            shoulder = joints[16:19]
            pelvis = joints[19:22]
            poses[t_idx, 0] = shoulder  # shoulder at index 0
            poses[t_idx, 1] = pelvis  # pelvis at index 1

            # Compute limb endpoints using FK
            for limb_idx, (cfg, (a1, a2)) in enumerate(zip(LIMB_CONFIGS, limb_lengths)):
                base_idx = limb_idx * 4
                hip_yaw = joints[base_idx]
                hip_pitch = joints[base_idx + 1]
                hip_roll = joints[base_idx + 2]
                knee_pitch = joints[base_idx + 3]

                origin = shoulder if cfg.origin_key == "shoulder" else pelvis
                points = forward_kinematics_3D_2link(
                    a1 * scale, a2 * scale, origin, hip_yaw, hip_pitch, hip_roll, knee_pitch
                )

                # Store endpoint (last point from FK)
                effector_idx = 2 + limb_idx  # hand_left=2, hand_right=3, foot_left=4, foot_right=5
                poses[t_idx, effector_idx] = points[-1]

        return poses

    def _update_displays(self):
        """Update time and frame displays."""
        self.time_display = f"{self.current_time:.2f}s"
        if self.frame_times is not None and len(self.frame_times) > 0:
            self.frame_display = f"Frame {self.current_frame_index + 1} / {len(self.frame_times)}"
        else:
            self.frame_display = "No animation"

    def _load_frame(self, frame_idx: int):
        """Load a specific frame into the pose editor."""
        if self.frame_poses is None or frame_idx >= len(self.frame_poses):
            return
        pose = self._array_to_pose(self.frame_poses[frame_idx])
        self.ids["pose_viewer"].load_pose(pose)

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
