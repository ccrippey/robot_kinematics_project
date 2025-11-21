from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty, StringProperty
from kivy.vector import Vector
from kivy.core.window import Window
from src.kinematics.inverse_kinematics import inverse_kinematics_2D_2link
from src.kinematics import projection2d


class StickFigure(Widget):
    """A stick figure that receives end effector positions and calculates limb angles.

    End effector positions (inputs):
    - left_hand_x, left_hand_y
    - right_hand_x, right_hand_y
    - left_foot_x, left_foot_y
    - right_foot_x, right_foot_y
    - shoulder_x, shoulder_y (now an input, not calculated)
    - pelvis_x, pelvis_y (now an input, not calculated)

    The inverse kinematics solver will calculate the individual limb angles (thetas)
    to position the hands and feet at the specified locations given the shoulder
    and pelvis positions.
    """

    # End effector positions (inputs) - 3D source of truth
    left_hand_x3 = NumericProperty(100)
    left_hand_y3 = NumericProperty(300)
    left_hand_z3 = NumericProperty(0)
    right_hand_x3 = NumericProperty(200)
    right_hand_y3 = NumericProperty(300)
    right_hand_z3 = NumericProperty(0)
    left_foot_x3 = NumericProperty(100)
    left_foot_y3 = NumericProperty(100)
    left_foot_z3 = NumericProperty(0)
    right_foot_x3 = NumericProperty(200)
    right_foot_y3 = NumericProperty(100)
    right_foot_z3 = NumericProperty(0)

    # 2D projected coordinates used for rendering/IK
    left_hand_x = NumericProperty(100)
    left_hand_y = NumericProperty(300)
    right_hand_x = NumericProperty(200)
    right_hand_y = NumericProperty(300)
    left_foot_x = NumericProperty(100)
    left_foot_y = NumericProperty(100)
    right_foot_x = NumericProperty(200)
    right_foot_y = NumericProperty(100)

    # Joint positions (3D source of truth)
    shoulder_x3 = NumericProperty(150)
    shoulder_y3 = NumericProperty(280)
    shoulder_z3 = NumericProperty(0)
    pelvis_x3 = NumericProperty(150)
    pelvis_y3 = NumericProperty(130)
    pelvis_z3 = NumericProperty(0)

    # Projected 2D shoulder/pelvis
    shoulder_x = NumericProperty(150)
    shoulder_y = NumericProperty(280)
    pelvis_x = NumericProperty(150)
    pelvis_y = NumericProperty(130)

    # Projection mode
    projection_mode = NumericProperty(0.0)

    head_image = StringProperty("assets/He watches.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Bind projection changes from 3D -> 2D, then IK update
        self.bind(
            projection_mode=self._update_projection_2d,
            left_hand_x3=self._update_projection_2d,
            left_hand_y3=self._update_projection_2d,
            left_hand_z3=self._update_projection_2d,
            right_hand_x3=self._update_projection_2d,
            right_hand_y3=self._update_projection_2d,
            right_hand_z3=self._update_projection_2d,
            left_foot_x3=self._update_projection_2d,
            left_foot_y3=self._update_projection_2d,
            left_foot_z3=self._update_projection_2d,
            right_foot_x3=self._update_projection_2d,
            right_foot_y3=self._update_projection_2d,
            right_foot_z3=self._update_projection_2d,
            shoulder_x3=self._update_projection_2d,
            shoulder_y3=self._update_projection_2d,
            shoulder_z3=self._update_projection_2d,
            pelvis_x3=self._update_projection_2d,
            pelvis_y3=self._update_projection_2d,
            pelvis_z3=self._update_projection_2d,
        )

        self.bind(
            left_hand_x=self.inverse_kinematics_update,
            left_hand_y=self.inverse_kinematics_update,
            right_hand_x=self.inverse_kinematics_update,
            right_hand_y=self.inverse_kinematics_update,
            left_foot_x=self.inverse_kinematics_update,
            left_foot_y=self.inverse_kinematics_update,
            right_foot_x=self.inverse_kinematics_update,
            right_foot_y=self.inverse_kinematics_update,
            shoulder_x=self.inverse_kinematics_update,
            shoulder_y=self.inverse_kinematics_update,
            pelvis_x=self.inverse_kinematics_update,
            pelvis_y=self.inverse_kinematics_update,
        )

        # Initial projection + IK
        self._update_projection_2d()
        self.inverse_kinematics_update()

    def _update_projection_2d(self, *args):
        """Project stored 3D joint locations into 2D display coordinates."""
        self.left_hand_x, self.left_hand_y, _ = projection2d.project_point(
            (self.left_hand_x3, self.left_hand_y3, self.left_hand_z3), self.projection_mode, (Window.width, Window.height)
        )
        self.right_hand_x, self.right_hand_y, _ = projection2d.project_point(
            (self.right_hand_x3, self.right_hand_y3, self.right_hand_z3), self.projection_mode, (Window.width, Window.height)
        )
        self.left_foot_x, self.left_foot_y, _ = projection2d.project_point(
            (self.left_foot_x3, self.left_foot_y3, self.left_foot_z3), self.projection_mode, (Window.width, Window.height)
        )
        self.right_foot_x, self.right_foot_y, _ = projection2d.project_point(
            (self.right_foot_x3, self.right_foot_y3, self.right_foot_z3), self.projection_mode, (Window.width, Window.height)
        )
        self.shoulder_x, self.shoulder_y, _ = projection2d.project_point(
            (self.shoulder_x3, self.shoulder_y3, self.shoulder_z3), self.projection_mode, (Window.width, Window.height)
        )
        self.pelvis_x, self.pelvis_y, _ = projection2d.project_point(
            (self.pelvis_x3, self.pelvis_y3, self.pelvis_z3), self.projection_mode, (Window.width, Window.height)
        )

    def inverse_kinematics_update(self, *args):
        if not {"left_arm", "right_arm", "left_leg", "right_leg"}.issubset(self.ids):
            return  # Wait until errthang is available

        leftarm = self.ids.left_arm
        (leftarm.theta_origin, leftarm.theta) = inverse_kinematics_2D_2link(
            leftarm.a1, leftarm.a2, self.shoulder_x, self.shoulder_y, self.left_hand_x, self.left_hand_y
        )
        rightarm = self.ids.right_arm
        (rightarm.theta_origin, rightarm.theta) = inverse_kinematics_2D_2link(
            rightarm.a1, rightarm.a2, self.shoulder_x, self.shoulder_y, self.right_hand_x, self.right_hand_y
        )

        leftleg = self.ids.left_leg
        (leftleg.theta_origin, leftleg.theta) = inverse_kinematics_2D_2link(
            leftleg.a1, leftleg.a2, self.pelvis_x, self.pelvis_y, self.left_foot_x, self.left_foot_y
        )

        rightleg = self.ids.right_leg
        (rightleg.theta_origin, rightleg.theta) = inverse_kinematics_2D_2link(
            rightleg.a1, rightleg.a2, self.pelvis_x, self.pelvis_y, self.right_foot_x, self.right_foot_y
        )
