import os

import board
import neopixel
import time


from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.sequence import AnimationSequence, AnimateOnce
from adafruit_led_animation.group import AnimationGroup

import touchio

from analogio import AnalogIn

analog_in = AnalogIn(board.A2)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

from collections import OrderedDict
from adafruit_led_animation.color import RED, PURPLE, WHITE, AMBER, JADE, MAGENTA, ORANGE

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
    print(x.value)



### Pixel setup

pixels_count = 12

pixels = neopixel.NeoPixel(board.GP18,
                           pixels_count,
                           brightness = 0.1,
                           auto_write=False)


### Touch setup
touch0 = touchio.TouchIn(board.GP21)
touch1 = touchio.TouchIn(board.GP20)
touch2 = touchio.TouchIn(board.GP19)


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



animation = RainbowChase(pixels, speed=0.1, size=5, spacing=3)
now = monotonic()
watchdog_s = 10
watchdog = monotonic()
led_on_buffer = [False]*10
while True:
    led_on_buffer.pop(0)
    led_on_buffer.append(led_on.value)

    if monotonic() - watchdog > watchdog_s:
        print('tick')
        print(sum(led_on_buffer))
        print(led_on_buffer)
        if sum(led_on_buffer) > 5:
            press_butt(0.1)
        watchdog = monotonic()
    if touch0.value:
        animation.animate()
    elif touch1.value:
        pixels.fill((0,255,0))
        pixels.show()
    elif touch2.value:
        battery_level = (get_voltage(analog_in)*2 - 2.8) / (4.3 - 2.8)
        pixels.fill((0,0,0))
        battery_fill = int(battery_level*10)
        for i in range(battery_fill):
            color = (int(255*(1-battery_level)),
                     int(255*battery_level),
                     0)
            pixels[i] = color
        remainder = battery_level*10 % 1
        pixels[i] = (int(color[0] * remainder),
                     int(color[1] * remainder),
                     int(color[2] * remainder))
        pixels.show()
    else:
        pixels.fill((0,0,255))
        show_read(pixels, read_pins)





