from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty, StringProperty
from kivy.vector import Vector

class StickFigure(Widget):
    head_image = StringProperty("")  # Path to the head image file
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)