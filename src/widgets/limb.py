from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.vector import Vector
from kivy.graphics import Color, Line


class Limb(Widget):
    x1 = NumericProperty(0)
    y1 = NumericProperty(0)
    x2 = NumericProperty(0)
    y2 = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0, 0, 0, 1)
            self.line = Line(points=[self.x1, self.y1, self.x2, self.y2], width=2)
        
        self.bind(x1=self._update_line,
                  y1=self._update_line,
                  x2=self._update_line,
                  y2=self._update_line)

    def _update_line(self, *args):
        self.line.points = [self.x1, self.y1, self.x2, self.y2]