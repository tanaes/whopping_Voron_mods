import os

import board
import neopixel
import time
import alarm
import storage

from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.sequence import AnimationSequence, AnimateOnce
from adafruit_led_animation.group import AnimationGroup
from adafruit_led_animation.helper import PixelMap, PixelSubset
from adafruit_led_animation import helper

import touchio

from analogio import AnalogIn

from collections import OrderedDict
from adafruit_led_animation.color import RED, PURPLE, WHITE, AMBER, JADE, MAGENTA, ORANGE
VORONRED = 0xD50005

from digitalio import DigitalInOut, Direction, Pull, DriveMode
from time import monotonic, sleep


### Charger interfacing


sw_press = DigitalInOut(board.GP10)
sw_press.direction = Direction.OUTPUT
sw_press.drive_mode = DriveMode.OPEN_DRAIN
sw_press.value = True

led_on = DigitalInOut(board.GP18)
led_on.direction = Direction.INPUT
led_on.pull = None


boost_on = DigitalInOut(board.GP4)

battery_in = AnalogIn(board.A1)

def get_battery_v():
    return (battery_in.value * 3.3 * 2) / 65536

def press_butt(t):
    print('press')
    sw_press.value = False
    time.sleep(t)
    print('unpress')
    sw_press.value = True



### Pixel setup


pixels_edge_num = 12
pixels_grid_num = 24

pixels_edge = neopixel.NeoPixel(board.GP16,
                              pixels_edge_num,
                              brightness = 0.3,
                              auto_write=False)

pixels_grid = neopixel.NeoPixel(board.GP15,
                              pixels_grid_num,
                              brightness = .3                                                      ,
                              auto_write=False)

## Grid animations
pixel_grid_vertical = helper.PixelMap.vertical_lines(
    pixels_grid, 6, 4, helper.horizontal_strip_gridmap(6, alternating=False)
)

pixel_grid_horizontal = helper.PixelMap.horizontal_lines(
    pixels_grid, 6, 4, helper.horizontal_strip_gridmap(6, alternating=False)
)


comet_h = Comet(
    pixel_grid_horizontal, speed=0.1, color=PURPLE, tail_length=3, bounce=True
)
comet_v = Comet(pixel_grid_vertical, speed=0.1, color=AMBER, tail_length=5, bounce=True)
chase_h = Chase(pixel_grid_horizontal, speed=0.1, size=3, spacing=6, color=JADE)
rainbow_chase_v = RainbowChase(
    pixel_grid_vertical, speed=0.1, size=3, spacing=2, step=4
)
rainbow_comet_v = RainbowComet(
    pixel_grid_vertical, speed=0.1, tail_length=5, bounce=True
)
rainbow_v = Rainbow(pixel_grid_vertical, speed=0.1, period=2)
rainbow_chase_h = RainbowChase(pixel_grid_horizontal, speed=0.1, size=3, spacing=3)


animations_grid = [rainbow_v,
                   comet_h,
                   rainbow_comet_v,
                   chase_h,
                   rainbow_chase_v,
                   comet_v,
                   rainbow_chase_h]


solid = Solid(pixels_edge, color=AMBER)
chase = Chase(pixels_edge, speed=0.1, color=WHITE, size=3, spacing=6)
comet = Comet(pixels_edge, speed=0.01, color=PURPLE, tail_length=10, bounce=True)
pulse = Pulse(pixels_edge, speed=0.1, color=AMBER, period=3)
rainbow = Rainbow(pixels_edge, speed=0.1, period=2)
rainbow_chase = RainbowChase(pixels_edge, speed=0.1, size=5, spacing=3)
rainbow_comet = RainbowComet(pixels_edge, speed=0.1, tail_length=7, bounce=True)
rainbow_sparkle = RainbowSparkle(pixels_edge, speed=0.1, num_sparkles=15)
sparkle = Sparkle(pixels_edge, speed=0.05, color=AMBER, num_sparkles=10)
sparkle_pulse = SparklePulse(pixels_edge, speed=0.05, period=3, color=JADE)

animations_edge = [solid, chase, comet, pulse, rainbow, rainbow_chase,
              rainbow_comet, rainbow_sparkle, sparkle, sparkle_pulse]


def startup_animation(pixels):
    animations = AnimationSequence(
                    AnimationGroup(
                        RainbowComet(pixels, speed=0.05, tail_length=12, ring=True),
                        sync=True),
                    advance_interval=3,
                    auto_clear=True)
    
    now = monotonic()
    while monotonic() < now + 2:
        animations.animate()
    pixels.fill((0,0,0))
    pixels.show()

### Touch setup
N = touchio.TouchIn(board.GP12)
R = touchio.TouchIn(board.GP8)
V = touchio.TouchIn(board.GP20)


TESTING = True

def log(s):
    """Print the argument if testing/tracing is enabled."""
    if TESTING:
        print(s)


class StateMachine(object):

    def __init__(self):
        self.state = None
        self.states = {}
        self.pixels_grid = pixels_grid
        self.pixels_edge = pixels_edge
        self.cooldown_timer = 0.2
        self.cooldown = monotonic()
        self.led_stack = [True] * 20
        self.led_status = True
        self.heartbeat = monotonic()

    def read_button(self):
        if monotonic() - self.cooldown < self.cooldown_timer:
            return(None)
        else:
            self.cooldown = monotonic()
            if R.value:
                self.state.handle_center()
            elif N.value:
                self.state.handle_up()
            elif V.value:
                self.state.handle_down()

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            log('Exiting %s' % (self.state.name))
            self.state.exit()
        self.state = self.states[state_name]
        log('Entering %s' % (self.state.name))
        self.state.enter()

    def update(self):
        # check requested on status
        self.led_stack.pop(0)
        self.led_stack.append(led_on.value)
        if boost_on.value:
            # if 5V boost is on, tickle the IC
            if monotonic() - self.heartbeat >= 10:
                print('LED is on, staying awake')
                press_butt(0.1)
                self.heartbeat = monotonic()
        else:
            # if it's off, go to sleep
            print('LED is off, going to sleep')

            boost_on.deinit()
            wake_pin = board.GP27
            pin_alarm = alarm.pin.PinAlarm(pin=wake_pin, value=True, edge=False, pull=False) 

            alarm.exit_and_deep_sleep_until_alarms(pin_alarm)
        if self.state:
            self.state.update()


class State(object):

    def __init__(self):
        self.up = None
        self.center = None
        self.down = None

    @property
    def name(self):
        return ''

    def enter(self):
        pass

    def exit(self):
        pass

    def update(self):
        pass

    def handle_up(self):
        pass

    def handle_down(self):
        pass

    def handle_center(self):
        pass

class WakeState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'grid'
        self.right = None

    @property
    def name(self):
        return 'wake'

    def enter(self):
        machine.pixels_edge.fill((255,255,255))
        machine.pixels_edge.show()
        machine.pixels_grid.fill((255,255,255))
        machine.pixels_grid.show()

    def exit(self):
        super().exit()

    def handle_up(self):
        machine.pixels_grid.brightness = min(1.0, machine.pixels_grid.brightness + 0.1)
        machine.pixels_grid.show()
        machine.pixels_edge.brightness = min(1.0, machine.pixels_edge.brightness + 0.1)
        machine.pixels_edge.show()

    def handle_down(self):
        machine.pixels_grid.brightness = max(0.1, machine.pixels_grid.brightness - 0.1)
        machine.pixels_grid.show()
        machine.pixels_edge.brightness = max(0.1, machine.pixels_edge.brightness - 0.1)
        machine.pixels_edge.show()

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        machine.read_button()


class SelectGridState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'edge'
        self.right = None
        self.ani = 0

    @property
    def name(self):
        return 'grid'

    def enter(self):
        super().enter()

    def exit(self):
        super().exit()

    def handle_up(self):
        self.ani = (self.ani + 1) % len(animations_grid)
        pixels_grid.fill((0,0,0))

    def handle_down(self):
        self.ani = (self.ani - 1) % len(animations_grid)
        pixels_grid.fill((0,0,0))

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        # animate
        animations_grid[self.ani].animate()
        machine.read_button()



class SelectEdgeState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'animate'
        self.right = None
        self.ani = 0

    @property
    def name(self):
        return 'edge'

    def enter(self):
        super().enter()

    def exit(self):
        super().exit()

    def handle_up(self):
        self.ani = (self.ani + 1) % len(animations_edge)
        pixels_edge.fill((0,0,0))

    def handle_down(self):
        self.ani = (self.ani - 1) % len(animations_edge)
        pixels_edge.fill((0,0,0))

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        # animate
        animations_edge[self.ani].animate()
        machine.read_button()

class AnimateState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'grid'
        self.right = None

    @property
    def name(self):
        return 'animate'

    def enter(self):
        self.ani_grid = machine.states['grid'].ani
        self.ani_edge = machine.states['edge'].ani
        super().enter()

    def exit(self):
        super().exit()

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        # animate
        animations_grid[self.ani_grid].animate()
        animations_edge[self.ani_edge].animate()
        machine.read_button()




def startup():
    # check LED status
    
    if not boost_on.value:
        print('started without indicator led on; turning it on now')
        press_butt(0.1)
        print('okay')


startup()

machine = StateMachine()
machine.add_state(WakeState())
machine.add_state(AnimateState())
machine.add_state(SelectGridState())
machine.add_state(SelectEdgeState())
machine.go_to_state('wake')

while True:
    machine.update()


