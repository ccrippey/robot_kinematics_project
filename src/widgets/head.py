from kivy.uix.image import Image
from kivy.properties import StringProperty, NumericProperty


class Head(Image):
    """A head widget that displays a photo at the top of the torso.
    
    The displayed image can be changed by setting the `head_image` property,
    which can eventually be set from the root StickFigure object.
    """
    
    head_image = StringProperty("")  # Path to the head image file
    head_size = NumericProperty(75)  # Size of the head image
    
    def __init__(self, **kwargs):
        super(Head, self).__init__(**kwargs)
        self.bind(head_image=self._update_image)
    
    def _update_image(self, instance, value):
        """Update the displayed image when head_image property changes."""
        if value:
            self.source = value
