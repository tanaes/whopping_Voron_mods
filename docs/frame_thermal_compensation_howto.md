# Setting up thermal compensation

## Hardware

There needs to be some way to measure the temperature of the frame. I took a little bead thermistor I had laying around and shoved it about halfway up the inside of one of my vertical extrusions, using the bottom blind joint access hole to get into the center channel. I connected this thermistor to the T2 thermistor input on my mainboard.

## Installing Software

### Measurement script

Clone alchemyEngine's measurement script from the [Gist](https://gist.github.com/alchemyEngine/6d42bb1ea391bf5d587625d64e5acfe7):

```
cd ~
git clone https://gist.github.com/alchemyEngine/6d42bb1ea391bf5d587625d64e5acfe7
mv 6d42bb1ea391bf5d587625d64e5acfe7 frame_expansion
```

### Update Klipper version

Because the changes haven't yet been merged into the main Klipper fork, we will need to check out alchemyEngine's work-in-progress fork.

Checkout alchemyEngine's Klipper fork:

```
cd ~/klipper
git remote add alchemyEngine https://github.com/alchemyEngine/klipper.git
git fetch alchemyEngine
git checkout -b frame_expansion alchemyEngine/work-frame-expansion-20210410
```

This creates a new branch called `frame_expansion` and updates it to match alchemyEngine's. Our starting Klipper software remains in the `main` branch. 

### Flash updated firmware

Now, we need to update the firmware on our MCU to match our new Klipper software.

```
cd ~/klipper
make menuconfig
make clean
```

This will recompile the firmware. Flashing to the MCU will be different depending on your particular board. I'm running a FYSETC Spider in UART mode, and here is what worked for me:

```
sudo service klipper stop
./scripts/flash-sdcard.sh /dev/ttyAMA0 fysetc-spider
sudo service klipper start
```

### Update Klipper config

Our new branch now recognizes a config section called `[frame_expansion_compensation]`. We'll need to fill in some details. 

Because I am using a non-standard thermistor, I also needed to define a custom thermistor type (in my case, an NTC 50K B3950). 


```
[thermistor ntc_50k]
temperature1: 25
resistance1: 50000
beta: 3950

[frame_expansion_compensation]
coeff: 23.4
#   Coefficient of linear expansion for the frame material [μm/m·°C].
#   E.g. 23.4 μm/m·°C for Misumi A6N01SS-T5 6005A-T5 aluminum alloy.
frame_z_length: 530
#   Total length of vertical extrusions [mm].
gantry_factor: 1
#   Relationship between gantry expansion and toolhead Z movement.
#   Examples:
#      if 1mm expansion moves toolhead up 1mm, gantry_factor: 1.0
#      if 1mm expansion moves toolhead up 0.5mm, gantry_factor: 0.5
#      if 1mm expansion moves toolhead down 1mm, gantry_factor: -1.0
#   The default is 1.0.
#max_comp_z:
#   Disables compensation above this Z height [mm]. The last computed correction
#   will remain applied until the toolhead moves below the specified Z position
#   again. The default is 0.0mm (always on).
#max_z_offset:
#   Maximum absolute compensation that can be applied to the Z axis [mm]. The
#   default is 99999999.0mm (unlimited).
sensor_type: ntc_50k
sensor_pin: PC2
min_temp: 0
max_temp: 100
#   See the "extruder" section for the definition of the above
#   parameters.
gcode_id: frame
#   See the "heater_generic" section for the definition of this
#   parameter.
z_stepper: stepper_z
#   The Z stepper motor linked with the Z endstop, as written in printer.cfg.
#   Used for triggering reference temperature measurement. Usually 'stepper_z'
#   unless otherwise defined.
```

There are also some other changes I made to my config to match the measurement script's assumptions. It is looking for a temperature sensor called `chamber`, and I had mine set up as a heater; so I went ahead and redefined it as just a sensor, and commented out the heater code block:

```
#####################################################################
#   Chamber Heater
#####################################################################
# [heater_generic chamber]
# ##  24V heated bed mosfet
# heater_pin: PB4
# sensor_type: NTC 100K MGB18-104F39050L32
# sensor_pin: PC1
# ##  Adjust Max Power so your heater doesn't warp your bed
# max_power: 1
# min_temp: 0
# max_temp: 70
# control: pid
# pid_kp: 10
# pid_ki: 1
# pid_kd: 900


[temperature_sensor chamber]
sensor_type: NTC 100K MGB18-104F39050L32
sensor_pin: PC1
min_temp: 0
max_temp: 70
gcode_id: chamber
#   See the "heater_generic" section for the definition of this
#   parameter.
```

## Run measurement script

Now we can actually measure the thermal expansion!

I verified that everything started up as expected, then I SSH'd into the Pi and ran the script:

```
cd ~/frame_expansion
python measure_expansion.py
```

It's running now!