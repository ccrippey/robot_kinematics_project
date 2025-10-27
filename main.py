from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
import os

# Import your screen logic
from src.screens.screens import Figure2D
from src import widgets
from kivy.core.window import Window


class AppScreenManager(ScreenManager):
    pass

class MyApp(App):
    def build(self):
        base_dir = os.path.dirname(__file__)
        kv_dir = os.path.join(base_dir, 'src', 'screens')
        kv_widgets = os.path.join(base_dir, 'src', 'widgets')


        # Explicitly load all kv files
        Builder.load_file(os.path.join(kv_dir, 'figure2d.kv'))

        # Load the root kv (optional)
        Builder.load_file(os.path.join(base_dir, 'src', 'app.kv'))

        sm = AppScreenManager()
        sm.add_widget(Figure2D(name='figure2d'))
        sm.current = 'figure2d'
        return sm

if __name__ == '__main__':
    Window.clearcolor = (1, 1, 1, 1)
    MyApp().run()
