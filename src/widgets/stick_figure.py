import kivy
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.core.window import Window
from src.kinematics.inverse_kinematics import (
    inverse_kinematics_2D_2link,
    inverse_kinematics_3D_2link,
    choose_best_solution_3d,
)
from src.kinematics.forward_kinematics import forward_kinematics_3D_2link
from src.kinematics import projection2d
from src.kinematics.projection2d import project_points
from kivy.clock import Clock


class StickFigure(Widget):
    """A stick figure that receives end effector positions and calculates limb angles.

    End effector positions (inputs):
    - left_hand, right_hand, left_foot, right_foot (3D positions)
    - shoulder, pelvis (3D positions)

    The inverse kinematics solver will calculate the individual limb angles (thetas)
    to position the hands and feet at the specified locations given the shoulder
    and pelvis positions.
    """

    # End effector positions (inputs) - 3D source of truth
    left_hand_pos3d = ListProperty([100, 300, 0])
    right_hand_pos3d = ListProperty([200, 300, 0])
    left_foot_pos3d = ListProperty([100, 100, 0])
    right_foot_pos3d = ListProperty([200, 100, 0])
    shoulder_pos3d = ListProperty([150, 280, 0])
    pelvis_pos3d = ListProperty([150, 130, 0])

    # 2D projected coordinates used for rendering/IK
    left_hand_pos2d = ListProperty([100, 300])
    right_hand_pos2d = ListProperty([200, 300])
    left_foot_pos2d = ListProperty([100, 100])
    right_foot_pos2d = ListProperty([200, 100])
    shoulder_pos2d = ListProperty([150, 280])
    pelvis_pos2d = ListProperty([150, 130])

    # Projection mode
    projection_mode = NumericProperty(0.0)

    head_image = StringProperty("assets/He watches.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Bind projection changes from 3D -> 2D, then IK update
        self.bind(
            projection_mode=self._update_projection_2d,
            left_hand_pos3d=self._update_projection_2d,
            right_hand_pos3d=self._update_projection_2d,
            left_foot_pos3d=self._update_projection_2d,
            right_foot_pos3d=self._update_projection_2d,
            shoulder_pos3d=self._update_projection_2d,
            pelvis_pos3d=self._update_projection_2d,
        )

        self.bind(
            left_hand_pos2d=self.inverse_kinematics_update,
            right_hand_pos2d=self.inverse_kinematics_update,
            left_foot_pos2d=self.inverse_kinematics_update,
            right_foot_pos2d=self.inverse_kinematics_update,
            shoulder_pos2d=self.inverse_kinematics_update,
            pelvis_pos2d=self.inverse_kinematics_update,
        )

        Clock.schedule_once(self._initialize_projection, 0)

    def _initialize_projection(self, dt):
        """Initialize projection and IK after widget tree is ready."""
        self._update_projection_2d()
        self.inverse_kinematics_update()

    def _update_projection_2d(self, *args):
        """Project stored 3D joint locations into 2D display coordinates."""
        projections = {
            "left_hand": self.left_hand_pos3d,
            "right_hand": self.right_hand_pos3d,
            "left_foot": self.left_foot_pos3d,
            "right_foot": self.right_foot_pos3d,
            "shoulder": self.shoulder_pos3d,
            "pelvis": self.pelvis_pos3d,
        }

        for name, pos3d in projections.items():
            x, y, _ = projection2d.project_point(pos3d, self.projection_mode, (Window.width, Window.height))
            setattr(self, f"{name}_pos2d", [x, y])

    def inverse_kinematics_update(self, *args):
        required_ids = {"left_arm", "right_arm", "left_leg", "right_leg"}
        if not required_ids.issubset(self.ids):
            return

        limb_configs = [
            ("left_arm", "shoulder_pos3d", "left_hand_pos3d"),
            ("right_arm", "shoulder_pos3d", "right_hand_pos3d"),
            ("left_leg", "pelvis_pos3d", "left_foot_pos3d"),
            ("right_leg", "pelvis_pos3d", "right_foot_pos3d"),
        ]

        for limb_id, origin_attr, target_attr in limb_configs:
            limb = self.ids[limb_id]
            origin = getattr(self, origin_attr)
            target = getattr(self, target_attr)

            a1 = 2 * limb.a1 / (Window.width + Window.height)
            a2 = 2 * limb.a2 / (Window.width + Window.height)
            solutions = inverse_kinematics_3D_2link(a1, a2, origin, target)
            hip_yaw, hip_pitch, hip_roll, knee_pitch = choose_best_solution_3d(solutions, limb_id)
            points3 = forward_kinematics_3D_2link(a1, a2, origin, hip_yaw, hip_pitch, hip_roll, knee_pitch)
            points2 = project_points(points3, self.projection_mode, (Window.width, Window.height))
            points2d_flat = [int(p) for point in points2 for p in point[:2]]
            limb.line.points = points2d_flat

    def on_projection_mode(self, *args):
        if self.projection_mode == 45.0:
            self.head_image = "assets/R45.png"
        elif self.projection_mode == -45.0:
            self.head_image = "assets/L45.png"
        elif self.projection_mode == 90.0:
            self.head_image = "assets/Right.png"
        elif self.projection_mode == -90.0:
            self.head_image = "assets/Left.png"
        elif self.projection_mode == 180.0:
            self.head_image = "assets/Back.png"
        elif self.projection_mode == 0.0:
            self.head_image = "assets/He watches.png"
