from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import DragBehavior
from kivy.core.window import Window
from kivy.properties import ListProperty, StringProperty, BooleanProperty, NumericProperty

from src.kinematics import projection2d


class EndEffector(DragBehavior, BoxLayout):
    """A draggable circular handle widget with a position display label.

    This widget can be clicked and dragged around the screen.
    Its position can be accessed via the `pos` property (inherited from Widget).
    A text label below the handle displays the current position coordinates.
    """

    color = ListProperty([1, 0, 0, 1])  # Default color (red)
    position_text = StringProperty("0, 0")  # Text displaying current position
    draggable = BooleanProperty(True)

    # 3D coordinates (source of truth); display position is projected
    pos3d = ListProperty([0.0, 0.0, 0.0])
    depth = NumericProperty(0.0)
    projection_mode = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super(EndEffector, self).__init__(**kwargs)
        # Configure drag behavior to allow dragging from anywhere on the widget
        self._update_drag_rect()
        self.drag_distance = 5

        # Internal flags to avoid recursion when syncing 2D/3D
        self._syncing_display = False
        self._syncing_3d = False

        # Update drag rectangle when position or size changes
        self.bind(pos=self._update_drag_rect, size=self._update_drag_rect)
        self.bind(pos=self._on_display_moved)
        self.bind(pos3d=self._update_display_from_3d, projection_mode=self._update_display_from_3d)
        # Initialize display from starting 3D values
        self._update_display_from_3d()

    def _update_drag_rect(self, *args):
        """Update the drag rectangle to match the widget bounds."""
        self.drag_rectangle = self.x, self.y, self.width, self.height

    def _update_position_text(self, *args):
        """Update the position text label when the widget moves."""
        self.position_text = f"{int(self.center_x)}, {int(self.center_y)}"

    def _on_display_moved(self, *args):
        """Handle 2D drag movement by refreshing label and 3D point."""
        self._update_position_text()
        if self._syncing_display:
            return
        self._update_3d_from_display()

    def _update_3d_from_display(self):
        if self._syncing_display:
            return
        self._syncing_3d = True
        x3, y3, z3 = projection2d.back_project(
            (self.center_x, self.center_y), self.projection_mode, self.depth, (Window.width, Window.height)
        )
        self.pos3d = [x3, y3, z3]
        self._syncing_3d = False

    def _update_display_from_3d(self, *args):
        if self._syncing_3d:
            return
        self._syncing_display = True
        u, v, depth = projection2d.project_point(self.pos3d, self.projection_mode, (Window.width, Window.height))
        self.center = (u, v)
        self.depth = depth
        self._update_position_text()
        self._syncing_display = False

    def set_color(self, rgba):
        """Set the color of the end effector handle."""
        self.color = rgba

    def on_touch_down(self, touch):
        if not self.draggable:
            return super(DragBehavior, self).on_touch_down(touch)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if not self.draggable:
            return super(DragBehavior, self).on_touch_move(touch)
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.draggable:
            return super(DragBehavior, self).on_touch_up(touch)
        return super().on_touch_up(touch)
