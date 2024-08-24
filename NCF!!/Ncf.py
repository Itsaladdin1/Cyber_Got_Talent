
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image

class ncfholdApp(App):
    def go_to_screen(self, screenName):
        self.root.current = screenName
        
ncfholdApp().run()