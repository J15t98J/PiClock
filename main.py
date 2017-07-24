import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.loader import Loader
from kivy.properties import StringProperty
from kivy.uix.button import Button
from kivy.uix.effectwidget import HorizontalBlurEffect, VerticalBlurEffect
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget


class ClockProgram(Widget):
    curtime = StringProperty()

    def update(self, dt):
        self.curtime = time.strftime("%H:%M:%S")


class AsyncTouchImage(AsyncImage):
    src = "https://source.unsplash.com/featured/?nature" # TODO: allow setting custom search term via settings; TODO: night image mode?
    startTime = 0

    def __init__(self, **kwargs):
        super(AsyncTouchImage, self).__init__(**kwargs)
        # set initial background image
        self.cycleImage(None)

    # wrapper function for event callback bind
    def setImage(self, image):
        self.texture=image.texture

    def cycleImage(self, dt):
        # TODO: keep next image cached?
        image = Loader.image(self.src)
        image.bind(on_load=self.setImage)
        self.src = self.src + "#" # refuses to change picture if src URL doesn't change

    def on_touch_down(self, touch):
        app = App.get_running_app().instance
        # ensure touch is inside bg pic but outside clock label
        if self.collide_point(*touch.pos) and not app.clocklabel.collide_point(*touch.pos) and app.screen_manager.current == "main":
            self.startTime = time.time()
            self.event = Clock.schedule_once(self.cycleImage, 1)
        return True

    def on_touch_up(self, touch):
        timeDiff = time.time() - self.startTime
        # Picture change requires long press
        if timeDiff < 1000:
            Clock.unschedule(self.event)
        else:
            pass # TODO: show/hide for macro buttons
        return True


class CustomButton(Button):
    def menuButtonPressed(self, instance):
        app = App.get_running_app().instance
        if instance == "pin":
            pass
        elif instance == "alarms":
            pass
        elif instance == "settings":
            app.effWid.effects = [HorizontalBlurEffect(size=20), VerticalBlurEffect(size=20)]
            app.screen_manager.current = "settings"
        elif instance == "exit":
            app.effWid.effects = []
            app.screen_manager.current = "main"


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


# fix for skewed clock label on program start due to clock text not having loaded in yet
def recenter(instance, value):
    instance.center_x = instance.parent.width/2


def recenterimg(instance, value):
    instance.center_y = instance.parent.height/2


class ClockApp(App):
    instance = None

    def build(self):
        self.instance = ClockProgram()
        Clock.schedule_interval(self.instance.update, 1/60)
        # TODO: surely there's a better way of doing this?
        App.get_running_app().instance.clocklabel.bind(size=recenter)
        App.get_running_app().instance.image1.bind(size=recenterimg)
        App.get_running_app().instance.image2.bind(size=recenterimg)
        App.get_running_app().instance.image3.bind(size=recenterimg)
        Window.size = (800, 480) # TODO: remove dev aid
        return self.instance

if __name__ == "__main__":
    ClockApp().run()
