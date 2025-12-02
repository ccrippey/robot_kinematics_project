from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen


class Figure2D(Screen):
    """Simple pose editor screen without keyframe management."""
    
    projection_mode = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._post_init, 0)
    
    def _post_init(self, dt):
        """Sync projection mode with pose editor after widget tree is built."""
        if 'pose_editor' in self.ids:
            self.ids.pose_editor.projection_mode = self.projection_mode
            self.bind(projection_mode=lambda inst, val: setattr(self.ids.pose_editor, 'projection_mode', val))

