import os

import board
import neopixel
import time
import alarm
import storage
import audiomp3
import audiopwmio

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

import touchio

from analogio import AnalogIn

from collections import OrderedDict
from adafruit_led_animation.color import RED, PURPLE, WHITE, AMBER, JADE, MAGENTA, ORANGE
VORONRED = 0xD50005

from digitalio import DigitalInOut, Direction, Pull, DriveMode
from time import monotonic, sleep


### Charger interfacing


sw_press = DigitalInOut(board.GP14)
sw_press.direction = Direction.OUTPUT
sw_press.drive_mode = DriveMode.OPEN_DRAIN
sw_press.value = True

led_on = DigitalInOut(board.GP15)
led_on.direction = Direction.INPUT
led_on.pull = None

boost_on = DigitalInOut(board.GP27)

battery_in = AnalogIn(board.A2)

def get_battery_v():
    return (battery_in.value * 3.3 * 2) / 65536

def press_butt(t):
    print('press')
    sw_press.value = False
    time.sleep(t)
    print('unpress')
    sw_press.value = True


### Gnd pins

#gnd_gpios = [board.GP7, board.GP6]
#gnd_pins = [DigitalInOut(x) for x in gnd_gpios]
#for x in gnd_pins:
#    x.direction = Direction.OUTPUT
#    x.drive_mode = DriveMode.OPEN_DRAIN
#    x.value = False

### Badge num read

self_gpios = [board.GP13,
              board.GP12,
              board.GP11,
              board.GP10,
              board.GP9,
              board.GP8,
              board.GP7]

self_pins = [DigitalInOut(x) for x in self_gpios]
for x in self_pins:
    x.direction = Direction.INPUT
    x.pull = Pull.UP
    print(x.value)

### Badge reader

read_gpios = [board.GP0,
              board.GP1,
              board.GP2,
              board.GP3,
              board.GP4,
              board.GP5,
              board.GP6]

read_pins = [DigitalInOut(x) for x in read_gpios]

for x in read_pins:
    x.direction = Direction.INPUT
    x.pull = Pull.UP
    



### Pixel setup

pixels_count = 12

pixels = neopixel.NeoPixel(board.GP18,
                           pixels_count,
                           brightness = 0.1,
                           auto_write=False)

solid = Solid(pixels, color=VORONRED)
chase = Chase(pixels, speed=0.1, color=WHITE, size=3, spacing=6)
comet = Comet(pixels, speed=0.01, color=PURPLE, tail_length=10, bounce=True)
pulse = Pulse(pixels, speed=0.1, color=AMBER, period=3)
rainbow = Rainbow(pixels, speed=0.1, period=2)
rainbow_chase = RainbowChase(pixels, speed=0.1, size=5, spacing=3)
rainbow_comet = RainbowComet(pixels, speed=0.1, tail_length=7, bounce=True)
rainbow_sparkle = RainbowSparkle(pixels, speed=0.1, num_sparkles=15)
sparkle = Sparkle(pixels, speed=0.05, color=AMBER, num_sparkles=10)
sparkle_pulse = SparklePulse(pixels, speed=0.05, period=3, color=JADE)

animations = [solid, chase, comet, pulse, rainbow, rainbow_chase,
              rainbow_comet, rainbow_sparkle, sparkle, sparkle_pulse]

audio = audiopwmio.PWMAudioOut(board.GP22)

decoder = audiomp3.MP3Decoder(open("wilhelm.mp3", "rb"))

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

def read_badge_list(fp):
    badge_list = []
    with open(fp, 'r') as f:
        for line in f:
            i = int(line.rstrip())
            badge_list.append(i)

    return(badge_list)


def read_color_db(fp):
    db = {}
    with open(fp, 'r') as f:
        for line in f:
            values = line.rstrip().split('\t')
            i = int(values.pop(0))
            name = values.pop(0)
            colors = [int(x, 16) for x in values]
            db[i] = colors

    return(db)


color_db = read_color_db('color_db.txt')


### Touch setup
N = touchio.TouchIn(board.GP21)
R = touchio.TouchIn(board.GP20)
V = touchio.TouchIn(board.GP19)


def show_read(display_pixels, read_pins):
    read_array = [x.value for x in read_pins]
    display_pixels.fill((20,0,20))
    for i, p in enumerate(read_array):
        if not p:
            display_pixels[i] = ((255,255,255))
        else:
            display_pixels[i] = ((0,0,255))
    display_pixels.show()
    return()

def read_connector(read_pins):
    read_array = [not x.value for x in read_pins]

    return(list(reversed(read_array)))

def convert_read(estimate):
    return(int(''.join(str(int(i)) for i in estimate[1:]), 2))

self_id = convert_read(read_connector(self_pins))
print('Self: %s' % self_id)

badge_list_fp = 'badge_list.txt'
badge_list = read_badge_list(badge_list_fp)

if self_id not in badge_list:
    badge_list.append(self_id)

TESTING = True

def log(s):
    """Print the argument if testing/tracing is enabled."""
    if TESTING:
        print(s)


class StateMachine(object):

    def __init__(self):
        self.state = None
        self.states = {}
        self.pixels = pixels
        self.color_db = color_db
        self.cooldown_timer = 0.2
        self.cooldown = monotonic()
        self.led_stack = [True] * 20
        self.led_status = True
        self.heartbeat = monotonic()
        self.collection = badge_list

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

    def add_to_collection(self, number):
        if number not in self.collection:
            self.collection.append(number)
        # need to remount filesystem to allow write
        storage.remount("/", readonly=False, disable_concurrent_write_protection=True)
        with open(badge_list_fp, 'w') as f:
            for i in self.collection:
                f.write('%s\n' % i)
        # now go back to readonly
        storage.remount("/", readonly=True, disable_concurrent_write_protection=False)

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
        self.center = 'animate'
        self.right = None

    @property
    def name(self):
        return 'wake'

    def enter(self):
        machine.pixels.fill((255,255,255))
        machine.pixels.show()

    def exit(self):
        super().exit()

    def handle_up(self):
        machine.pixels.brightness = min(1.0, machine.pixels.brightness + 0.1)
        machine.pixels.show()

    def handle_down(self):
        machine.pixels.brightness = max(0.1, machine.pixels.brightness - 0.1)
        machine.pixels.show()

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        machine.read_button()


class AnimateState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'pairing'
        self.right = None
        self.ani = 0

    @property
    def name(self):
        return 'animate'

    def enter(self):
        super().enter()

    def exit(self):
        super().exit()

    def handle_up(self):
        self.ani = (self.ani + 1) % len(animations)
        pixels.fill((0,0,0))

    def handle_down(self):
        self.ani = (self.ani - 1) % len(animations)
        pixels.fill((0,0,0))

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        # animate
        animations[self.ani].animate()
        machine.read_button()


class PairingState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'display'
        self.right = None
        self.status_pixels = PixelMap(machine.pixels, [(0, 3), (9, 12)])
        self.pairing_pixels = PixelSubset(machine.pixels, 3, 9)
        self.waiting_ani = Pulse(self.status_pixels,
                                 speed=0.1, 
                                 color=(255,255,255), 
                                 period=3)
        self.pairing_ani = Comet(self.status_pixels, 
                                 speed=0.1,
                                 color=(255,255,255),
                                 tail_length=3, bounce=True)
        self.fail_ani = Blink(self.status_pixels,
                              speed=0.5,
                              color=(255,0,0))
        self.succ_ani = Solid(self.status_pixels,
                              color=0x00FF00)
        self.pairing_start = None

    @property
    def name(self):
        return 'pairing'

    def enter(self):
        # start out each pairing indicator pixel as purple
        self.status = 'waiting'
        self.pairing_pixels.fill((128,0,128))
        self.pairing_pixels.show()
        # start with neutral prior on each pin
        self.read = [128] * 7

    def handle_center(self):
        machine.go_to_state(self.center)

    def check_result_good(self):
        # first convert posteriors to bool
        estimate = [False] * 7
        threshold = 30
        for i, x in enumerate(self.read):
            if x < threshold:
                estimate[i] = False
            elif x > 255-threshold:
                estimate[i] = True
            else:
                estimate[i] = None

        if None in estimate:
            return(False, estimate)
        elif estimate[0] != estimate[6]:
            return(False, estimate)
        else:
            return(True, estimate)




    def update(self):
        machine.read_button()

        this_read = read_connector(read_pins)

        if self.status == 'waiting':
            if sum(this_read) != 0:
                audio.play(decoder)
                while audio.playing:
                    pass
                self.status = 'pairing'
                self.pairing_start = monotonic()
            else:
                self.waiting_ani.animate()
        elif self.status == 'pairing':
            for i, x in enumerate(this_read):
                # update each pin by decrementing prior if 0, increasing if 1
                update = self.read[i] + [-1, 1][int(x)]

                # constrain posterior to 0:255. posterior is thus sliding window.
                self.read[i] = min(max(update, 0), 255)

                # skip parity bit and update pixels
                if i > 0:
                    self.pairing_pixels[i - 1] = (255-self.read[i],
                                                  0,
                                                  self.read[i])

            self.pairing_ani.animate()
            self.pairing_pixels.show()

            # do this for five seconds, but then call it done
            if monotonic() - self.pairing_start > 5:
                self.status = 'paired'
        elif self.status == 'paired':
            # check our result
            good, estimate = self.check_result_good()
            print(estimate)

            

            for i, x in enumerate(self.pairing_pixels):
                if estimate[i + 1] == True:
                    x = (0,0,255)
                elif estimate[i + 1] == False:
                    x = (255,0,0)
                elif estimate[i + 1] == None:
                    x = (128,0,128)
            
            self.pairing_pixels.show()


            if good:
                read_number = convert_read(estimate)

                if read_number not in machine.color_db:
                    self.status = 'failure'
                else:
                    self.status = 'success'
                    machine.add_to_collection(read_number)

                    now = monotonic()
                    while monotonic() - now < 2:
                        self.succ_ani.animate()
                    machine.go_to_state('display')
            else:
                self.status = 'failure'


        elif self.status == 'success':
            self.status_pixels.fill((255,255,255))
            self.status_pixels.show()
        elif self.status == 'failure':
            self.fail_ani.animate()


        
class DisplayState(State):

    def __init__(self):
        super().__init__()
        self.left = None
        self.center = 'animate'
        self.right = None
        self.display_idx = -1

    @property
    def name(self):
        return 'display'

    def enter(self):
        super().enter()

    def exit(self):
        super().exit()

    def handle_up(self):
        self.display_idx = (self.display_idx + 1) % len(machine.collection)

    def handle_down(self):
        self.display_idx = (self.display_idx - 1) % len(machine.collection)

    def handle_center(self):
        machine.go_to_state(self.center)

    def update(self):
        # show current index
        pixel_colors = machine.color_db[machine.collection[self.display_idx]]
        for i, x in enumerate(pixel_colors):
            machine.pixels[i] = x
        machine.pixels.show()
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
machine.add_state(PairingState())
machine.add_state(DisplayState())
machine.go_to_state('wake')

while True:
    machine.update()


