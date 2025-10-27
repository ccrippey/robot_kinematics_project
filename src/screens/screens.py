from kivy.uix.screenmanager import Screen

class Figure2D(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Bind end effectors to stick figure after widgets are created
        from kivy.clock import Clock
        Clock.schedule_once(self._bind_end_effectors, 0)
    
    def _bind_end_effectors(self, dt):
        """Bind the end effector positions to the stick figure's IK system."""
        if hasattr(self.ids, 'sticky1'):
            stick = self.ids.sticky1
            
            # Bind hand positions
            if hasattr(self.ids, 'hand_left'):
                self.ids.hand_left.bind(x=lambda inst, val: setattr(stick, 'left_hand_x', val))
                self.ids.hand_left.bind(y=lambda inst, val: setattr(stick, 'left_hand_y', val))
                # Set initial position
                stick.left_hand_x = self.ids.hand_left.x
                stick.left_hand_y = self.ids.hand_left.y
            
            if hasattr(self.ids, 'hand_right'):
                self.ids.hand_right.bind(x=lambda inst, val: setattr(stick, 'right_hand_x', val))
                self.ids.hand_right.bind(y=lambda inst, val: setattr(stick, 'right_hand_y', val))
                # Set initial position
                stick.right_hand_x = self.ids.hand_right.x
                stick.right_hand_y = self.ids.hand_right.y
            
            # Bind foot positions
            if hasattr(self.ids, 'foot_left'):
                self.ids.foot_left.bind(x=lambda inst, val: setattr(stick, 'left_foot_x', val))
                self.ids.foot_left.bind(y=lambda inst, val: setattr(stick, 'left_foot_y', val))
                # Set initial position
                stick.left_foot_x = self.ids.foot_left.x
                stick.left_foot_y = self.ids.foot_left.y
            
            if hasattr(self.ids, 'foot_right'):
                self.ids.foot_right.bind(x=lambda inst, val: setattr(stick, 'right_foot_x', val))
                self.ids.foot_right.bind(y=lambda inst, val: setattr(stick, 'right_foot_y', val))
                # Set initial position
                stick.right_foot_x = self.ids.foot_right.x
                stick.right_foot_y = self.ids.foot_right.y
