from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty, StringProperty
from kivy.vector import Vector
from src.kinematics.inverse_kinematics import inverse_kinematics_2D_2link


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

    # End effector positions (inputs)
    left_hand_x = NumericProperty(100)
    left_hand_y = NumericProperty(300)
    right_hand_x = NumericProperty(200)
    right_hand_y = NumericProperty(300)
    left_foot_x = NumericProperty(100)
    left_foot_y = NumericProperty(100)
    right_foot_x = NumericProperty(200)
    right_foot_y = NumericProperty(100)

    # Joint positions (now driven by end effectors, not calculated)
    shoulder_x = NumericProperty(150)
    shoulder_y = NumericProperty(280)
    pelvis_x = NumericProperty(150)
    pelvis_y = NumericProperty(130)

    head_image = StringProperty("assets/He watches.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Bind end effector positions to inverse kinematics update
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

        # Initial calculation
        self.inverse_kinematics_update()

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
