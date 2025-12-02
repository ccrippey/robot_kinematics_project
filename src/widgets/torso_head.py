from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.graphics import Color, Line
import math


class TorsoHead(Widget):
    """Combined torso and head widget defined by shoulder and pelvis points.

    The torso is a line between shoulders and pelvis.
    The head is positioned and oriented above the shoulders point.
    """

    shoulder_pos = ListProperty([0, 0])
    pelvis_pos = ListProperty([0, 0])
    head_image = StringProperty("")
    head_size = NumericProperty(75)

    def __init__(self, **kwargs):
        super(TorsoHead, self).__init__(**kwargs)

        # Draw the torso line
        with self.canvas:
            Color(0, 0, 0, 1)
            self.torso_line = Line(points=[], width=2)

        self.bind(shoulder_pos=self._update_torso, pelvis_pos=self._update_torso)

        # Schedule head update after widget tree is built
        from kivy.clock import Clock

        Clock.schedule_once(lambda dt: self._update_head_position(), 0)

    def _update_torso(self, *args):
        """Update the torso line when shoulder or pelvis positions change."""
        self.torso_line.points = self.shoulder_pos + self.pelvis_pos
        # Update head position based on shoulder position
        self._update_head_position()

    def _update_head_position(self):
        """Calculate head position and orientation based on shoulder position."""
        # Position head above shoulders
        # Calculate torso angle for proper head orientation
        dx = self.pelvis_pos[0] - self.shoulder_pos[0]
        dy = self.pelvis_pos[1] - self.shoulder_pos[1]

        if dx != 0 or dy != 0:
            torso_angle = math.atan2(dy, dx)
        else:
            torso_angle = -math.pi / 2  # Default to vertical

        # Head offset distance above shoulders (perpendicular to torso)
        head_offset = self.head_size // 2

        # Calculate perpendicular direction (180 degrees from torso)
        perp_angle = torso_angle - math.pi

        # Position head offset from shoulders in perpendicular direction
        head_x = self.shoulder_pos[0] + head_offset * math.cos(perp_angle)
        head_y = self.shoulder_pos[1] + head_offset * math.sin(perp_angle)

        # Update head widget if it exists (defined in .kv file as id: head_widget)
        if "head_widget" in self.ids:
            self.ids.head_widget.x = head_x - self.ids.head_widget.width / 2
            self.ids.head_widget.y = head_y - self.ids.head_widget.height / 2
