from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty, StringProperty
from kivy.vector import Vector

class StickFigure(Widget):
    """A stick figure that receives end effector positions and calculates joint positions.
    
    End effector positions:
    - left_hand_x, left_hand_y
    - right_hand_x, right_hand_y
    - left_foot_x, left_foot_y
    - right_foot_x, right_foot_y
    
    Calculated joint positions:
    - shoulder_x, shoulder_y (midpoint between hands)
    - pelvis_x, pelvis_y (midpoint between feet)
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
    
    # Calculated joint positions (outputs)
    shoulder_x = NumericProperty(0)
    shoulder_y = NumericProperty(0)
    pelvis_x = NumericProperty(0)
    pelvis_y = NumericProperty(0)
    
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
                  right_foot_y=self.inverse_kinematics_update)
        
        # Initial calculation
        self.inverse_kinematics_update()
    
    def inverse_kinematics_update(self, *args):
        """Calculate joint positions from end effector positions.
        
        Currently implements a simple test: 
        - Shoulder position = midpoint between hands
        - Pelvis position = midpoint between feet
        
        TODO: Implement proper inverse kinematics solver
        """
        # Calculate shoulder as midpoint between hands
        self.shoulder_x = (self.left_hand_x + self.right_hand_x) / 2
        self.shoulder_y = (self.left_hand_y + self.right_hand_y) / 2
        
        # Calculate pelvis as midpoint between feet
        self.pelvis_x = (self.left_foot_x + self.right_foot_x) / 2
        self.pelvis_y = (self.left_foot_y + self.right_foot_y) / 2