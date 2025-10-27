
from kivy.lang import Builder
from kivy.factory import Factory
from .end_effector import EndEffector
from .limb import Limb
from .stick_figure import StickFigure
from .limb2joint import Limb2Link

# Register the Python class with the Factory
Factory.register('EndEffector', cls=EndEffector)
Factory.register('Limb', cls=Limb)
Factory.register('StickFigure', cls=StickFigure)
Factory.register('Limb2Link', cls=Limb2Link)

# Load the associated kv file automatically
Builder.load_file(__file__.replace('__init__.py', 'end_effector.kv'))
Builder.load_file(__file__.replace('__init__.py', 'stick_figure.kv'))