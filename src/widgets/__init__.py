
from kivy.lang import Builder
from kivy.factory import Factory

from .head import Head
from .end_effector import EndEffector
from .limb import Limb
from .stick_figure import StickFigure
from .limb2link import Limb2Link
from .torso_head import TorsoHead
from .pose_editor import PoseEditor

# Register the Python class with the Factory
Factory.register('EndEffector', cls=EndEffector)
Factory.register('Limb', cls=Limb)
Factory.register('StickFigure', cls=StickFigure)
Factory.register('Limb2Link', cls=Limb2Link)
Factory.register('Head', cls=Head)
Factory.register('TorsoHead', cls=TorsoHead)
Factory.register('PoseEditor', cls=PoseEditor)

# Load the associated kv file automatically
Builder.load_file(__file__.replace('__init__.py', 'end_effector.kv'))
Builder.load_file(__file__.replace('__init__.py', 'stick_figure.kv'))
Builder.load_file(__file__.replace('__init__.py', 'head.kv'))
Builder.load_file(__file__.replace('__init__.py', 'torso_head.kv'))
Builder.load_file(__file__.replace('__init__.py', 'pose_editor.kv'))
