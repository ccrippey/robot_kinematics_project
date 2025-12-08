from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.core.window import Window
from kivy.clock import Clock
import numpy as np

from src.kinematics.inverse_kinematics import cart_to_joint_config
from src.kinematics.forward_kinematics import forward_kinematics_3D_2link
from src.kinematics import projection2d
from src.kinematics.projection2d import project_points
from src.kinematics.stick_config import CartesianStickConfig, JointStickConfig, JointLimbConfig, LIMB_LENGTH_RATIOS


class StickFigure(Widget):
    """A stick figure for display purposes only.

    Interface:
    - load_cart(config: CartesianStickConfig): Set via Cartesian positions (does IK internally)
    - load_joint(config: JointStickConfig): Set via joint angles (does FK internally)

    All inputs are in normalized coordinates (not pixels).
    Projection and rendering handled internally.
    """

    # 2D projected coordinates for rendering (in pixels)
    left_hand_pos2d = ListProperty([100, 300])
    right_hand_pos2d = ListProperty([200, 300])
    left_foot_pos2d = ListProperty([100, 100])
    right_foot_pos2d = ListProperty([200, 100])
    shoulder_pos2d = ListProperty([150, 280])
    pelvis_pos2d = ListProperty([150, 130])

    projection_mode = NumericProperty(0.0)
    head_image = StringProperty("assets/He watches.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._initialize, 0)

    def _initialize(self, dt):
        """Initialize with default pose after widget tree is ready."""
        # Create default Cartesian config (normalized coordinates)
        default_config = CartesianStickConfig(
            shoulder=np.array([0.0, 0.05, 0.0]),
            pelvis=np.array([0.0, -0.05, 0.0]),
            hand_left=np.array([-0.03, 0.08, 0.0]),
            hand_right=np.array([0.03, 0.08, 0.0]),
            foot_left=np.array([-0.02, -0.15, 0.0]),
            foot_right=np.array([0.02, -0.15, 0.0]),
        )
        self.load_cart(default_config)

    def load_cart(self, config: CartesianStickConfig):
        """Load stick figure from Cartesian configuration (normalized coords).

        Performs IK to compute joint angles, then calls load_joint.
        """
        # Convert Cartesian to Joint space via IK
        joint_config = cart_to_joint_config(config)
        self.load_joint(joint_config)

    def load_joint(self, config: JointStickConfig):
        """Load stick figure from Joint configuration (normalized coords).

        Performs FK and projection to set 2D display positions.
        """

        # Convert normalized positions to pixels
        shoulder_pos = config.shoulder
        pelvis_pos = config.pelvis

        # Do FK for each limb and project to 2D
        limb_configs = [
            ("left_arm", config.left_arm, shoulder_pos),
            ("right_arm", config.right_arm, shoulder_pos),
            ("left_leg", config.left_leg, pelvis_pos),
            ("right_leg", config.right_leg, pelvis_pos),
        ]

        for limb_name, joint_limb, origin_pos in limb_configs:

            limb = self.ids[limb_name]
            a1_ratio, a2_ratio = LIMB_LENGTH_RATIOS[limb_name]

            # FK in pixel space
            points3d_pos = forward_kinematics_3D_2link(
                a1_ratio,
                a2_ratio,
                origin_pos,
                joint_limb.hip_yaw,
                joint_limb.hip_pitch,
                joint_limb.hip_roll,
                joint_limb.knee_pitch,
            )

            # Project to 2D
            points2 = project_points(points3d_pos, self.projection_mode, (Window.width, Window.height))
            points2d_flat = [int(p) for point in points2 for p in point[:2]]
            limb.line.points = points2d_flat

        # Project origin points to 2D
        shoulder_2d = projection2d.project_point(
            tuple(shoulder_pos), self.projection_mode, (Window.width, Window.height)
        )
        pelvis_2d = projection2d.project_point(tuple(pelvis_pos), self.projection_mode, (Window.width, Window.height))

        self.shoulder_pos2d = [shoulder_2d[0], shoulder_2d[1]]
        self.pelvis_pos2d = [pelvis_2d[0], pelvis_2d[1]]

    def on_projection_mode(self, *args):
        """Update head image based on projection mode."""
        mode_to_image = {
            45.0: "assets/R45.png",
            -45.0: "assets/L45.png",
            90.0: "assets/Right.png",
            -90.0: "assets/Left.png",
            180.0: "assets/Back.png",
            0.0: "assets/He watches.png",
        }
        self.head_image = mode_to_image.get(self.projection_mode, "assets/He watches.png")
