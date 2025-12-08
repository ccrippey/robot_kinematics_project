"""Stick figure configuration dataclasses for Cartesian and Joint space representations."""

import numpy as np
from dataclasses import dataclass
from typing import Tuple


# Limb length ratios (fraction of screen dimension: height + width)
# Matches stick_figure.kv definitions
LIMB_LENGTH_RATIOS = {
    "left_arm": (0.14, 0.12),   # (a1, a2) as fraction of screen size
    "right_arm": (0.14, 0.12),
    "left_leg": (0.15, 0.14),
    "right_leg": (0.15, 0.14),
}


@dataclass
class JointLimbConfig:
    """Joint configuration for a single limb in 3D.
    
    Uses hip terminology (applies to both arms and legs):
    - hip_yaw: rotation around vertical axis (shoulder_yaw for arms)
    - hip_pitch: forward/backward swing (shoulder_pitch for arms)
    - hip_roll: side-to-side rotation (shoulder_roll for arms)
    - knee_pitch: elbow/knee bend (elbow_pitch for arms)
    """
    hip_yaw: float
    hip_pitch: float
    hip_roll: float
    knee_pitch: float
    
    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array [hip_yaw, hip_pitch, hip_roll, knee_pitch]."""
        return np.array([self.hip_yaw, self.hip_pitch, self.hip_roll, self.knee_pitch])
    
    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> 'JointLimbConfig':
        """Create from numpy array [hip_yaw, hip_pitch, hip_roll, knee_pitch]."""
        return cls(hip_yaw=float(arr[0]), hip_pitch=float(arr[1]), 
                   hip_roll=float(arr[2]), knee_pitch=float(arr[3]))


@dataclass
class JointStickConfig:
    """Complete stick figure configuration in joint space (normalized, not pixels).
    
    All positions in normalized 3D coordinates.
    Joint angles in radians.
    """
    shoulder: np.ndarray  # 3D position [x, y, z]
    pelvis: np.ndarray    # 3D position [x, y, z]
    left_arm: JointLimbConfig
    right_arm: JointLimbConfig
    left_leg: JointLimbConfig
    right_leg: JointLimbConfig
    
    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array of shape (22,).
        
        Layout: [shoulder(3), pelvis(3), left_arm(4), right_arm(4), left_leg(4), right_leg(4)]
        """
        return np.concatenate([
            self.shoulder,
            self.pelvis,
            self.left_arm.to_numpy(),
            self.right_arm.to_numpy(),
            self.left_leg.to_numpy(),
            self.right_leg.to_numpy(),
        ])
    
    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> 'JointStickConfig':
        """Create from numpy array of shape (22,)."""
        return cls(
            shoulder=arr[0:3],
            pelvis=arr[3:6],
            left_arm=JointLimbConfig.from_numpy(arr[6:10]),
            right_arm=JointLimbConfig.from_numpy(arr[10:14]),
            left_leg=JointLimbConfig.from_numpy(arr[14:18]),
            right_leg=JointLimbConfig.from_numpy(arr[18:22]),
        )


@dataclass
class CartesianStickConfig:
    """Complete stick figure configuration in Cartesian space (normalized, not pixels).
    
    All positions in normalized 3D coordinates [x, y, z].
    """
    shoulder: np.ndarray   # 3D position
    pelvis: np.ndarray     # 3D position
    hand_left: np.ndarray  # 3D position
    hand_right: np.ndarray # 3D position
    foot_left: np.ndarray  # 3D position
    foot_right: np.ndarray # 3D position
    
    def to_numpy(self) -> np.ndarray:
        """Convert to numpy array of shape (6, 3).
        
        Order: [shoulder, pelvis, hand_left, hand_right, foot_left, foot_right]
        """
        return np.array([
            self.shoulder,
            self.pelvis,
            self.hand_left,
            self.hand_right,
            self.foot_left,
            self.foot_right,
        ])
    
    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> 'CartesianStickConfig':
        """Create from numpy array of shape (6, 3)."""
        return cls(
            shoulder=arr[0],
            pelvis=arr[1],
            hand_left=arr[2],
            hand_right=arr[3],
            foot_left=arr[4],
            foot_right=arr[5],
        )