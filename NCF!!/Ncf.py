from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

class Cybergottalent(App):
    def go_to_screen(self, screenName):
        self.root.current = screenName

    def build(self):
        return super().build()

Cybergottalent().run()