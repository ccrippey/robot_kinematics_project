"""Simple 2-link limb rendering widget."""

from kivy.uix.widget import Widget
from kivy.graphics import Color, Line


class Limb2Link(Widget):
    """A 2-link limb rendered as a line.

    Line points are set directly by StickFigure after FK computation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(0, 0, 0, 1)
            self.line = Line(points=[], width=2)
