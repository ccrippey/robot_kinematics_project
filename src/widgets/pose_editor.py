"""Unified pose editor widget with motion propagation.

This widget provides the core pose editing functionality used by both
the free editor (Figure2D) and the keyframe editor (KeyframeEditor).
"""

from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import NumericProperty, DictProperty
from kivy.clock import Clock
from kivy.core.window import Window
import numpy as np

from ..kinematics.stick_config import CartesianStickConfig


class PoseEditor(RelativeLayout):
    """Interactive pose editor with motion propagation.

    Provides draggable end effectors for hands, feet, shoulder, and pelvis
    with automatic motion propagation:
    - Feet movement → pelvis follows
    - Pelvis movement → shoulder follows
    - Shoulder movement → hands follow
    """

    projection_mode = NumericProperty(0.0)

    # Effector IDs we expect to find in the widget tree
    EFFECTOR_IDS = {
        "hands": ["hand_left", "hand_right"],
        "feet": ["foot_left", "foot_right"],
        "joints": ["shoulder", "pelvis"],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, dt):
        """Initialize after widget tree is built."""
        # Bind all effectors to update handler
        all_effectors = sum(self.EFFECTOR_IDS.values(), [])
        for eff_id in all_effectors:
            eff = self.ids[eff_id]
            eff.bind(pos3d=self.update_stick_config)

    def update_stick_config(self, *args):
        """Handle effector movement - update stick figure via load_cart."""
        # Build config from current effector positions (normalized coords)
        config = self.capture_pose()
        self.ids["stick_figure"].load_cart(config)

    def on_projection_mode(self, instance, value):
        """Handle projection mode changes."""
        self.projection_mode = value
        self.update_stick_config()


    def capture_pose(self):
        """Capture current pose as CartesianStickConfig (normalized coords)."""
        return CartesianStickConfig(
            shoulder=np.array(self.ids["shoulder"].pos3d),
            pelvis=np.array(self.ids["pelvis"].pos3d),
            hand_left=np.array(self.ids["hand_left"].pos3d),
            hand_right=np.array(self.ids["hand_right"].pos3d),
            foot_left=np.array(self.ids["foot_left"].pos3d),
            foot_right=np.array(self.ids["foot_right"].pos3d),
        )

    def load_cart(self, config: CartesianStickConfig):
        """Load a Cartesian config (normalized coords) into the editor."""

        # Convert normalized to pixels for effectors
        effector_updates = {
            "shoulder": config.shoulder,
            "pelvis": config.pelvis,
            "hand_left": config.hand_left,
            "hand_right": config.hand_right,
            "foot_left": config.foot_left,
            "foot_right": config.foot_right,
        }

        for eff_id, pos3d_px in effector_updates.items():
            if eff_id in self.ids:
                self.ids[eff_id].pos3d = pos3d_px.tolist()

        # Update stick figure
        self.ids["stick_figure"].load_cart(config)

