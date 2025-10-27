from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import DragBehavior
from kivy.properties import ListProperty, StringProperty

class EndEffector(DragBehavior, BoxLayout):
    """A draggable circular handle widget with a position display label.
    
    This widget can be clicked and dragged around the screen.
    Its position can be accessed via the `pos` property (inherited from Widget).
    A text label below the handle displays the current position coordinates.
    """
    
    color = ListProperty([1, 0, 0, 1])  # Default color (red)
    position_text = StringProperty("0, 0")  # Text displaying current position
    
    def __init__(self, **kwargs):
        super(EndEffector, self).__init__(**kwargs)
        # Configure drag behavior to allow dragging from anywhere on the widget
        self.drag_rectangle = self.x, self.y, self.width, self.height
        self.drag_distance = 5  # Start dragging immediately
        
        # Update drag rectangle when position or size changes
        self.bind(pos=self._update_drag_rect, size=self._update_drag_rect)
        self.bind(pos=self._update_position_text)
    
    def _update_drag_rect(self, *args):
        """Update the drag rectangle to match the widget bounds."""
        self.drag_rectangle = self.x, self.y, self.width, self.height
    
    def _update_position_text(self, *args):
        """Update the position text label when the widget moves."""
        self.position_text = f"{int(self.pos[0])}, {int(self.pos[1])}"
        
    def set_color(self, rgba):
        """Set the color of the end effector handle."""
        self.color = rgba
