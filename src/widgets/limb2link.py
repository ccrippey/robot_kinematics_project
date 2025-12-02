from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Color, Line
from ..kinematics import forward_kinematics as fk


class Limb2Link(Widget):
    """A 2-link limb rendered via forward kinematics."""

    a1 = NumericProperty(0)
    a2 = NumericProperty(0)
    theta = NumericProperty(0)
    origin_pos = ListProperty([0, 0])
    theta_origin = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0, 0, 0, 1)
            self.line = Line(points=[], width=2)

        # Bind all properties that affect limb rendering
        for prop in ("a1", "a2", "theta", "origin_pos", "theta_origin"):
            self.bind(**{prop: self._update_line})

    def _update_line(self, *args):
        """Update limb line using forward kinematics."""
        self.line.points = fk.forward_kinematics_2D_2link(
            self.a1, self.a2, self.origin_pos[0], self.origin_pos[1], self.theta_origin, self.theta
        )
