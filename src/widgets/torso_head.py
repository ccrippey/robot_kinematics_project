from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty
from kivy.graphics import Color, Line
import math


class TorsoHead(Widget):
    """Combined torso and head widget defined by shoulder and pelvis points.
    
    The torso is a line between shoulders and pelvis.
    The head is positioned and oriented above the shoulders point.
    """
    
    shoulder_x = NumericProperty(0)
    shoulder_y = NumericProperty(0)
    pelvis_x = NumericProperty(0)
    pelvis_y = NumericProperty(0)
    head_image = StringProperty("")
    
    def __init__(self, **kwargs):
        super(TorsoHead, self).__init__(**kwargs)
        
        # Draw the torso line
        with self.canvas:
            Color(0, 0, 0, 1)
            self.torso_line = Line(points=[self.shoulder_x, self.shoulder_y, 
                                          self.pelvis_x, self.pelvis_y], width=2)
        
        self.bind(shoulder_x=self._update_torso,
                  shoulder_y=self._update_torso,
                  pelvis_x=self._update_torso,
                  pelvis_y=self._update_torso)
        
        # Schedule head update after widget tree is built
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._update_head_position(), 0)
    
    def _update_torso(self, *args):
        """Update the torso line when shoulder or pelvis positions change."""
        self.torso_line.points = [self.shoulder_x, self.shoulder_y, 
                                  self.pelvis_x, self.pelvis_y]
        # Update head position based on shoulder position
        self._update_head_position()
    
    def _update_head_position(self):
        """Calculate head position and orientation based on shoulder position."""
        # Position head above shoulders
        # Calculate torso angle for proper head orientation
        dx = self.pelvis_x - self.shoulder_x
        dy = self.pelvis_y - self.shoulder_y
        
        if dx != 0 or dy != 0:
            torso_angle = math.degrees(math.atan2(dy, dx))
        else:
            torso_angle = -90  # Default to vertical
        
        # Head offset distance above shoulders (perpendicular to torso)
        head_offset = 40
        
        # Calculate perpendicular direction (90 degrees from torso)
        perp_angle = torso_angle - 90
        perp_rad = math.radians(perp_angle)
        
        # Position head offset from shoulders in perpendicular direction
        head_x = self.shoulder_x + head_offset * math.cos(perp_rad)
        head_y = self.shoulder_y + head_offset * math.sin(perp_rad)
        
        # Update head widget if it exists (defined in .kv file as id: head_widget)
        if hasattr(self, 'ids') and hasattr(self.ids, 'head_widget'):
            self.ids.head_widget.x = head_x - self.ids.head_widget.width / 2
            self.ids.head_widget.y = head_y - self.ids.head_widget.height / 2
