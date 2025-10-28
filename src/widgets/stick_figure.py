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
        self.bind(left_hand_x=self.inverse_kinematics_update,
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
                  pelvis_y=self.inverse_kinematics_update)
        
        # Initial calculation
        self.inverse_kinematics_update()
    
    def inverse_kinematics_update(self, *args):
        #Template for calling IK
        #(left_arm_theta1, left_arm_theta2) = inverse_kinematics_2D_2link(<left_arm_bicep_length>, <left_arm_forearm_length>, <shoulder_x>, self.shoulder_x, self.shoulder_y, self.left_hand_x, self.left_hand_y)
        """Calculate limb angles from end effector and joint positions.
        
        Now that shoulder and pelvis positions are driven by end effectors,
        this function will eventually calculate the individual link thetas
        to reach the hand and foot positions.
        
        TODO: Implement proper inverse kinematics solver for limb angles
        Currently just uses the effector positions directly.
        """
        # Shoulder and pelvis are now driven directly by end effectors
        # TODO: Calculate limb thetas based on:
        #   - shoulder_x/y and left_hand_x/y -> left arm thetas
        #   - shoulder_x/y and right_hand_x/y -> right arm thetas  
        #   - pelvis_x/y and left_foot_x/y -> left leg thetas
        #   - pelvis_x/y and right_foot_x/y -> right leg thetas
        pass