# Gantry Bowing

## Measuring gantry deflection at temp

First, download the scripts from this folder. These scripts are derived from alch3my's amazing frame_expansion code, check that out as well!

### Edit script for your printer

You'll need to edit the script (please use a vanilla text editer that doesn't fuck with line endings) to include parameters appropriate for your printer:

```

######### META DATA #################
# For data collection organizational purposes
USER_ID = ''            # e.g. Discord handle
PRINTER_MODEL = ''      # e.g. 'voron_v2_350'
HOME_TYPE = ''          # e.g. 'nozzle_pin', 'microswitch_probe', etc.
PROBE_TYPE = ''         # e.g. 'klicky', 'omron', 'bltouch', etc.
X_RAILS = ''            # e.g. '1x_mgn12_front', '2x_mgn9'
BACKERS = ''            # e.g. 'steel_x_y', 'Ti_x-steel_y', 'mgn9_y'
NOTES = ''              # anything note-worthy about this particular run, no "=" characters
#####################################

######### CONFIGURATION #############
BASE_URL = 'http://127.0.0.1'       # printer URL (e.g. http://192.168.1.15)
                                    # leave default if running locally
BED_TEMPERATURE = 105               # bed temperature for measurements
HE_TEMPERATURE = 100                # extruder temperature for measurements
MEASURE_INTERVAL = 1
N_SAMPLES = 3
HOT_DURATION = 2                   # time after bed temp reached to continue
                                    # measuring, in hours
MEASURE_GCODE = 'G28 Z'             # G-code called on repeated measurements, single line/macro only
QGL_CMD = "QUAD_GANTRY_LEVEL"       # command for QGL; e.g. "QUAD_GANTRY_LEVEL" or None if no QGL.

# chamber thermistor config name. Change to match your own, or "" if none
# will also work with temperature_fan configs
CHAMBER_CONFIG = "temperature_sensor chamber"
#####################################
```

Copy the modified `test_gantry_bowing.py` to the Pi running Klipper/Moonraker.

## Running data collection

Now, with the printer completely at room temp, run the script:

`python3 test_gantry_bowing.py`

You may want to run it using `nohup` so that closing your ssh connection doesn't kill the process:

`nohup python3 test_gantry_bowing.py > out.txt &`

The script will run for about 2 hours. It will home, QGL, home again, then heat the bed up. Once the bed is at temp, it will take the first mesh. Then it will collect z expansion data once per minute for the next two hours. Finally, it will do one more mesh and then cooldown.

## Processing data

The script will write the data to the folder from which it is run. Download that back to your computer.

Ping me on Discord (whoppingpochard#2514) and I'll run the data processing script to generate plots.

Alternatively, you can run the script yourself! It's in the same gist. To run it, you'll need up-to-date installations of matplotlib and numpy. The script `process_meshes.py` will take any number of data output files as positional arguments and write five figures per input.