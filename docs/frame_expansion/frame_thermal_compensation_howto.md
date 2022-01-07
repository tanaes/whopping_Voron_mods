# Setting up thermal compensation

# NOTE!
The process for setting this up is changing, and vastly better! See Alch3my's [updated process and documentation here](https://github.com/alchemyEngine/klipper_frame_expansion_comp). I've deleted my old setup notes, but left the results of my testing below for posterity. Happy printing! 

~~wp


## Exploring measurement data

My first measurment run yielded a somewhat non-linear relationship between frame_temp and the observed Z offset:

<img src="./figures/fit_beta.png" width="400">

After some discussion about how Klipper handles thermistors, I thought it would be sensible to see if re-running the measurement using a three-point definition rather than a beta definition would improve the fit. It did!

Thus, I changed from this:

```
[thermistor ntc_50k]
temperature1: 25
resistance1: 50000
beta: 3950
```

To this:

```

[thermistor ntc_50k]
temperature1: 25
resistance1: 50000
temperature2: 65
resistance2: 10095
temperature3: 100
resistance3: 3090
```

Turns out that was the ticket!

<img src="./figures/fit_3pt.png" width="400">

[Doing some calculations](./gantry_factor_calc.html), I was able to derive 2.8 as an approximate gantry factor for continued testing:

<img src="./figures/gantry_factor.png" width="400">

# Print tests

## Test configuration

To actually test the impact of the frame_compensation feature on first-layer printing, I made up a little test object that gives me a top and bottom view of the first layer, while also being easy to pull off the printbed when finished. I  then sliced a print of 25 copies of the model spaced across the bed and set to print each sequentially, rather than layer-by-layer. I also manually set the order, so that it would print row-wise across the plate:

<img src="./figures/test_print_pattern.png" width="400">

I set my slicer start gcode to include a 15-minute heat soak after achieving bed temperature, and then to either disable or enable frame compensation, depending on the run.

I ran the following tests:

- printing from cold, no compensation
- printing from cold, with compensation
- printing from hot, no compensation
- printing from hot, with compensation

"from hot" prints were run as quickly as possible after the "from cold" prints.

## Results: Cold start, no compensation

You can clearly see a decreasing amount of "squish" in the first layer across the first 7 or 8 test samples, representing maybe 20 minutes of print time:

<img src="./figures/test_print-no_comp-lineup.png" width="800">

This is even more apparent if you flip them over and look at the underside:

<img src="./figures/test_print-no_comp-cold-bottom.jpeg" width="800">

## Results: Hot start, no compensation

As we'd predict, the results are more more consistent for the hot start. Presumably, the frame has already reached equilibrium. There may be some variation in squish, but I don't think there's enough to say that the pattern we saw in the cold start is actually the result of a mechanical issue:

<img src="./figures/test_print-no_comp-hot-bottom.jpeg" width="800">

## Results: Cold start, with compensation

This one pretty much seals the deal for me. Despite identical cold-start parameters as the first test print, we see a really consisten first layer across the build plate, start to finish:

<img src="./figures/test_print-si_comp-cold-bottom.jpeg" width="800">

## Results: Hot start, with compensation

Including frame compensation from a hot start didn't seem to have any negative consequences, and the layer looks fairly consistent across the print. I think the overall degree of "squish" ended up being a little greater for both hot starts with and without compensation, but including the compensation didn't send the nozzle crashing into the bed or anything!

<img src="./figures/test_print-si_comp-hot-bottom.jpeg" width="800">

## Results: comparisons

Finally, I pulled out just the 1st, 5th, and 17th (bed center) test pieces from each trial and put them together for a visual comparison.

<img src="./figures/comparison_per-run.jpeg" width="800">

I think this really summarizes things nicely! 

I also hit the bottoms of the pieces with a heat gun and grouped them per-position rather than per-run, to highlight how the test piece printed at the same bed location fared across different trials. 

<img src="./figures/comparison_per-spot.png" width="800">

# Conclusion

This shit absolutely rules, and thanks so much to alchemyEngine for all the hard work!

