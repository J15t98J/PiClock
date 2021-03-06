import random
import re
import time
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.loader import Loader
from kivy.properties import StringProperty
from kivy.uix.button import Button
from kivy.uix.effectwidget import HorizontalBlurEffect, VerticalBlurEffect
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


class ClockProgram(Widget):  # TODO: move timestring to bound function to reduce overhead
    curtime = StringProperty()

    def update(self, dt):
        timestring = ""
        timestring += "%H:%M" if self.app.config.get("main_screen", "24hr") == "True" else "%I:%M"
        timestring += ":%S" if self.app.config.get("main_screen", "seconds") == "True" else ""
        timestring += " %p" if self.app.config.get("main_screen", "24hr") == "False" else ""
        self.curtime = time.strftime(timestring)


class AsyncTouchImage(AsyncImage):  # TODO: night image mode?
    srcBase = "https://source.unsplash.com/featured/?"
    isPinned = False
    rotateEvent = None
    startTime = 0
    touchEvents = {}
    hasScaleEvent = False
    isScaling = False

    def __init__(self, **kwargs):
        super(AsyncTouchImage, self).__init__(**kwargs)
        # set initial background image
        self.cycleImage(None, userTriggered=False)
        self.rotateEvent = Clock.schedule_interval(partial(self.cycleImage, userTriggered=False), 3600)

    # wrapper function for event callback bind
    def setImage(self, image):
        self.texture=image.texture

    def cycleImage(self, dt, **kwargs):
        # TODO: keep next image cached?
        if not self.isPinned:
            keywords = App.get_running_app().config.get("main_screen", "img_keywords").split(";")
            self.src = self.srcBase + random.choice(keywords) + "#"*random.randrange(1, 30)  # hash guarantees new image even if same keywords
            image = Loader.image(self.src)
            image.bind(on_load=self.setImage)
            if kwargs["userTriggered"]:
                Clock.unschedule(self.rotateEvent)
                self.rotateEvent = Clock.schedule_interval(partial(self.cycleImage, userTriggered=False), 3600)

    def activateLabelZoom(self, dt):
        self.isScaling = True
        self.scaleFrom = App.get_running_app().instance.clocklabel.font_size

    def on_touch_down(self, touch):
        program = App.get_running_app().instance
        # ensure touch is inside bg image and on main screen
        if self.collide_point(*touch.pos) and program.screen_manager.current == "main":
            if program.clocklabel.collide_point(*touch.pos):
                # user is trying to scale the clock label
                if not self.hasScaleEvent:
                    self.touchEvents[touch] = [Clock.schedule_once(self.activateLabelZoom, 1), "label", touch.pos]
                    self.hasScaleEvent = True
            else:
                # user is trying to change the bg image
                self.touchEvents[touch] = [Clock.schedule_once(partial(self.cycleImage, userTriggered=True), 1), "bg"]
            self.startTime = time.time()

        return True

    def on_touch_up(self, touch):
        timeDiff = time.time() - self.startTime
        # Picture change requires long press
        if touch in self.touchEvents and self.touchEvents[touch][1] == "label":
            self.hasScaleEvent = False
            self.isScaling = False
            app = App.get_running_app()
            app.config.set("main_screen", "font_size", app.instance.clocklabel.font_size)
        if timeDiff < 1000:
            if touch in self.touchEvents:
                Clock.unschedule(self.touchEvents[touch][0])
            # TODO: show/hide for macro buttons
        return True

    def on_touch_move(self, touch):
        firstTouch = self.touchEvents[touch] if touch in self.touchEvents else None
        if firstTouch and firstTouch[1] == "label" and self.isScaling:
            program = App.get_running_app().instance
            posDiff = (touch.pos[0] - firstTouch[2][0], touch.pos[1] - firstTouch[2][1])
            distance = (posDiff[0]**2 + posDiff[1]**2)**0.5
            program.clocklabel.font_size = self.scaleFrom + distance if posDiff[1] > 0 else self.scaleFrom - distance


class CustomButton(Button):
    def menuButtonPressed(self, instance):
        app = App.get_running_app()
        program = app.instance
        if instance == "pin":
            program.image1.source = "img\pin-off.png" if program.image1.source == "img\pin.png" else "img\pin.png"
            program.bgimage.isPinned = not program.bgimage.isPinned
            if program.bgimage.rotateEvent:
                Clock.unschedule(program.bgimage.rotateEvent)
                program.bgimage.rotateEvent = None
            else:
                program.bgimage.rotateEvent = Clock.schedule_interval(partial(program.bgimage.cycleImage, userTriggered=False), 3600)
        elif instance == "alarms":
            program.effWid.effects = [HorizontalBlurEffect(size=20), VerticalBlurEffect(size=20)]
            program.screen_manager.current = "alarms"
        elif instance == "settings":
            program.effWid.effects = [HorizontalBlurEffect(size=20), VerticalBlurEffect(size=20)]
            program.screen_manager.current = "settings"
        elif instance == "close":
            app.config.write()
            program.effWid.effects = []
            program.screen_manager.current = "main"
        elif instance == "exit":
            app.stop()


class CustomLabel(Label):
    pass


class KeywordInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        s = re.sub(re.compile(r"[^A-Za-z0-9,;]"), "", substring)
        return super(KeywordInput, self).insert_text(s, from_undo=from_undo)


class MainScreen(Screen):
    pass


class AlarmsScreen(Screen):
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
    config = None

    def build_config(self, config):
        config.setdefaults("main_screen", {
            "24hr": True,
            "seconds": False,
            "font_size": 140,
            "img_keywords": "nature"
        })

    def build(self):
        self.instance = ClockProgram()
        self.instance.app = self

        Clock.schedule_interval(self.instance.update, 1/60)

        # TODO: surely there's a better way of doing this?
        App.get_running_app().instance.clocklabel.bind(size=recenter)
        App.get_running_app().instance.image1.bind(size=recenterimg)
        App.get_running_app().instance.image2.bind(size=recenterimg)
        App.get_running_app().instance.image3.bind(size=recenterimg)

        Window.size = (800, 480)  # TODO: remove dev aid

        return self.instance

if __name__ == "__main__":
    ClockApp().run()
