from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.vector import Vector

class StickFigure(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)