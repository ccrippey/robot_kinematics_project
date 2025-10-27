from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.graphics import Color, Line
from ..kinematics import forward_kinematics as fk
import math


class Limb2Link(Widget):
    a1 = NumericProperty(0)
    a2 = NumericProperty(0)
    theta = NumericProperty(0)
    origin_x = NumericProperty(0)
    origin_y = NumericProperty(0)
    theta_origin = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0, 0, 0, 1)
            self.line = Line(points=[], width=2)
        
        self.bind(a1=self._update_line,
                  a2=self._update_line,
                  theta=self._update_line,
                  origin_x=self._update_line,
                  origin_y=self._update_line,
                  theta_origin=self._update_line)

    def _update_line(self, *args):

        self.line.points = fk.forward_kinematics_2D_2link(self.a1, self.a2, self.origin_x, self.origin_y, self.theta_origin,  self.theta)