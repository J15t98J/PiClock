import time

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget


class ClockProgram(Widget):
    curtime = StringProperty()
    def update(self, dt):
        self.curtime = time.strftime("%H:%M:%S")

class AsyncTouchImage(AsyncImage):
    event = None

    def changeImage(self, dt):
        self.source = self.source + "#"
        self.reload()

    def on_touch_down(self, touch):
        self.startTime = time.time()
        self.event = Clock.schedule_once(self.changeImage, 1)
        return True

    def on_touch_up(self, touch):
        timeDiff = time.time() - self.startTime
        if timeDiff < 1000:
            Clock.unschedule(self.event)
        return True


class ClockApp(App):
    def build(self):
        instance = ClockProgram()
        Clock.schedule_interval(instance.update, 1/60)
        return instance

if __name__ == "__main__":
    ClockApp().run()