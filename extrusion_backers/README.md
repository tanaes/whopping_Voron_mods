# Gantry Backing Plates

## The theory
Due to different thermal coefficients of linear expansion between steel (rails) and aluminum (extrusions), the Voron V2 gantry forms a sort of giant bimetal temperature sensor element. This causes a warping of the gantry as it heats up with increasing chamber temperature.

## The evidence
While exploring [frame expansion behavior](https://github.com/tanaes/whopping_Voron_mods/tree/main/docs/frame_expansion), a number of us were noticing empirical values several times what we'd predict simply due to linear expansion of the Z extrusions alone. Although plugging those empirical values in to the compensation code has given me great first layers, the difference from expectation was still bothering me. Maybe, I thought, there was some sort of warping happening? Checking out a table of thermal expansion coefficients, I saw that indeed aluminum expands quite a bit more than steel with temperature.

### Bottom X rail increases frame thermal compensation value

After some discussion on Discord, it appeared that people running the BOM double X rail, with an MGN9 rail on the front and bottom of the X extrusion, by and large seemed to be needing higher compensation values than those who only had a single X rail on the front face of the extrusion.

So I tried loosening the screws on the bottom X rail of my V2.4 350, and re-ran the thermal expansion measurment. Wouldn't you know it, my observed compensation factor went from around 2.8 to about 1.5:

<img src="./images/gantry_factor_loose.png" width="400">

### Bed mesh changes as predicted with frame temperature

To confirm, I decided to go ahead an loosen *all* the rails on both X and Y, heat soak the machine for a couple hours, and then tighten them down; this should ensure that the gantry is as flat as possible when at temperature, but will bow downwards when it is cold as the aluminum contracts more than the stell rail beneath.

And that's indeed what I saw. After hot-tightening the rails, I took a bed mesh while everything was still hot. I then allowed the printer to cool for a couple hours, reheated the heat bed, and took another mesh while the bed was hot but the frame was still cold.

What I saw was just what we'd predict, with the "hot frame" measurement (left) being quite flat, but the "cold frame" measurement appearing as if the center of the bed were closer to the probe:

<img src="./images/bed_mesh_comparison.png" width=600>

### Shitty modeling is consistent with observation

Finally, I put together a *very simplistic* FEA model in Fusion360. It did the thing with the bendy bendy:

<img src="./images/no_backer.png" width=500>

 ***Caveat: I am a biologist, not an engineer!*** I only barely know what I'm doing with this shit. But with the rail material set to 440C stainless and the extrusion to 6061 aluminum, with them bonded at the interface, a temperature delta of 40° C led to this 250mm-sized X gantry member deflecting 0.17 mm upwards in the center! That's definitely not trivial, and it's certainly consistent with our empirical observations.
 
## The (a) solution (maybe??)
 
Why have *bi*metal when you can have *tri*metal?!

At one extreme, bolting another MGN9 rail on top of the extrusion seems certain to cancel out the bending moment imparted by the one on the bottom. 

As a cheaper alternative, I've designed some laser-cut steel extrusion backing plates that weigh less and are lower-profile than rails, but which should at least do a reasonable job at counteracting the thermal defection.

<img src="./images/fusion_y_backer.png" width=600>

These are sized to fit along the top of the Y extrusion and on the top or back of the X extrusion, with a few mm of clearance to printed endpieces:

<img src="./images/fusion_y_chainmount.png" width=600>

They also have pilot holes for the cable chain end link to attach. They are sized to be drilled out with a 2.5 mm bit and then M3 tapped. (Laser cutting hardens the steel at the cut, so the cut holes are undersized for drilling out to be a bit gentler on your taps.)

<img src="./images/fusion_x_chainmount.png" width=600>

To attach them most optimally, you'll also need to countersink the holes so they can be installed with 6mm flat head M3 screws.

### Simulation results

Plugging these into the FEA model shows some serious improvements with a 1.9 mm steel backer:

<img src="./images/steel_1.9mm.png" width=500>

A 1.5 mm titanium backer does even better:

<img src="./images/ti_1.5mm.png" width=500>


### Sourcing

A set of 3 backers in 1.9 mm steel can be bought at [SendCutSend](www.sendcutsend.com) for somewhere in the neighborhood of $10 (presuming you've met their minimum order of $29). 

If you're feeling spendy, even the Ti backers still cost about the same as cheapo linear rails, with a set of three costing around $60.

