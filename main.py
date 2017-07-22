import time

from kivy.app import App
from kivy.clock import Clock
from kivy.loader import Loader
from kivy.properties import StringProperty
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget


class ClockProgram(Widget):
    curtime = StringProperty()

    def update(self, dt):
        self.curtime = time.strftime("%H:%M:%S")


class AsyncTouchImage(AsyncImage):
    src = "https://source.unsplash.com/featured/?nature" # TODO: allow setting custom search term via settings
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
        # ensure touch is inside bg pic but outside clock label
        if self.collide_point(*touch.pos) and not App.get_running_app().instance.clocklabel.collide_point(*touch.pos):
            self.startTime = time.time()
            self.event = Clock.schedule_once(self.cycleImage, 1)
        return True

    def on_touch_up(self, touch):
        timeDiff = time.time() - self.startTime
        # Picture change requires long press
        if timeDiff < 1000:
            Clock.unschedule(self.event)
        else:
            pass # TODO: show/hide for action buttons
        return True


class ClockApp(App):
    instance = None

    def build(self):
        self.instance = ClockProgram()
        Clock.schedule_interval(self.instance.update, 1/60)
        return self.instance

if __name__ == "__main__":
    ClockApp().run()