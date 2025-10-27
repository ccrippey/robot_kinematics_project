from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ListProperty
from kivy.vector import Vector

class EndEffector(Widget):
    velocity_x = NumericProperty(0.1)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    color = ListProperty([1, 0, 0, 1])  # Default color (red)

    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

    def set_color(self, rgba):
        self.color = rgba