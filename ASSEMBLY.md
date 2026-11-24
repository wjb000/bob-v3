# Assembly

Build it in this order. Several parts can't go on later: the centre base tile has to drop over the column foot before the middle tube goes in, and each arm's J1 screws have to go in before its J2 motor does.

Tools you need:

- soldering iron with a heat-set insert tip
- hex keys 1.5, 2, 2.5 and 3 mm
- 7 mm and 13 mm wrenches
- crimpers, a multimeter, and a bench supply with a current limit for first power-up

## 0. Before printing

1. Measure everything in [VERIFY.md](VERIFY.md), update `cad/params.py`, run `cad/export.py`.
2. Print a `joiner_tab`, one `wheel_bracket` and one servo cup (a `yoke` or `shoulder`) first. Check the inserts, the DDSM115 stub fit and the STS3095 drop-in before you commit 6 kg of filament.

## 1. Floor pan

1. Press inserts into every Ø4.0 hole in the nine `base_pan_*` tiles.
2. Lay the tiles ribs-down and join every seam with `joiner_tab`s and M3×10 screws from the top.
3. Wheels: screw each DDSM115 to its `wheel_bracket_l/r` through the stub end (3 × M2.5 × 10 on the Ø15.2 circle), then bolt the brackets to the pan (4 × M3×10 each). Spin the wheels by hand; the tire must clear the pan cut-out.

The base is 360 × 360 mm, so every pan and shell tile fits a 200 mm bed. Nothing in the base is glued: every joint is a screw into an insert or a nut.

## 2. Ball casters and lidar

1. Two CY-15A ball transfers (5/8 in steel ball) replace swivel casters: one 177 mm ahead of the wheel axle, one 127 mm behind it. Each one bolts up through the solid pad under the pan with 2 × M3×20 and an M3 nut in the hex pocket on top. No bearings, forks or bridges.
2. Put the robot on a flat floor. Both balls and both tires must touch. Shim under a ball transfer with a washer if one floats.
3. Bolt `lidar_mount` to the pan and the RPLIDAR C1 to the mount.

## 3. Power and base electronics

Follow the wiring diagram on the page.

1. Strap the 36 V pack into the two `battery_cradle` halves.
2. Front shelves (`shelf_front_l/r`): the DDSM Driver HAT (A), the TMC2209, the BNO085, the contactor, the fuse block and the two Pololu regulators.
3. Rear shelf (`shelf_rear_l`): the two DROK 12 V 10 A converters, one per arm. The other rear corner is the battery and the e-stop, so it has no shelf.
4. Wire the power path: pack → main fuse → main switch → fuse block. The Pololu 5 V regulator is always on and feeds the Pi. The contactor sits between the fuse block and the two arm converters and the Pololu 12 V regulator (wheels and lift). The e-stop's NC contacts are in series with the contactor coil.
5. First power-up on a current-limited bench supply at 36 V, 1 A. Check each rail before connecting any load.

## 4. Telescoping column

Four tubes. The screw drives the middle tube. Belt A makes the upper tube travel twice that far. Belt B makes the inner tube travel three times as far, 462 mm, 18.2 in. At the bottom the torso still sits 40 mm above the base.

1. Bolt `cable_trough` down, 2 × M3×12. Pin the six `col_draglink` prints into a short chain in that trough.
2. Bolt `col_outer_0` to the pan, 8 × M3×10 through the foot flange. Fit the lower KW12 on its pad. Bolt the NEMA 17 onto the pedestal (4 × M3×8), shaft up, coupler on the shaft.
3. Drop the centre base tile (`base_shell_mid_c`) over the outer tube. It just rests there for now.
4. Stack `col_outer_1` on `col_outer_0`, 4 × M3×14. Fit the two belt anchors at the top, and the upper KW12 on the left side flat (+Y) so its leaf reaches through the slot. The stop dogs on that piece face inward. The speaker and the belt-anchor bosses occupy the front flat, so the switch does not go there.
5. Middle tube: screw the TR8 nut into `col_mid_0`'s pocket from below (4 × M3 thread-forming). Stack `col_mid_1`. Press a GT2 20T pulley onto each top axle (belt A). Slide the middle tube down the outer tube. Thread the leadscrew (cut to 266 mm) up through the coupler and the nut. Tighten the coupler.
6. Upper tube: stack `col_upper_0` and `col_upper_1`. Clamp belt A on each side of `col_upper_0`, run it up over the middle-tube pulley, and anchor it on the outer tube. Same length both sides. Press the other two GT2 pulleys onto the top of the upper tube (belt B). Slide the upper tube into the middle tube.
7. Inner tube: stack `col_inner_0` and `col_inner_1`. Clamp belt B on each side, run it up over the upper-tube pulley, and anchor it on the middle tube. Slide the inner tube into the upper tube.
8. Bolt `col_cap` onto the inner tube (4 × M3×12). The plate is the seat for the torso. The Ø18 hole is the cable exit.
9. Drive the lift end to end on the bench supply before the sleeve is in. The inner tube should travel three times as far as the middle. It should stop on the switch.

### Column umbilical

One PET sleeve carries the chest power (5 V to the Pi, 12 V to both servo buses) and the lidar USB. Head and wrist camera cables stay in the chest and the arms. Each sliding tube has a shallow zip-tie bar on its rear inner wall, and the trough holds a six-link drag chain so the sleeve pays out instead of rubbing a tube edge.

1. Zip-tie the sleeve to the closed end of `cable_trough` and through the drag-chain links. The coil in the trough is the service loop for the 462 mm of travel. Do not leave a loose loop in the bore.
2. The tongue of the trough leads into the rear window of `col_outer_0` (left of the centre, y about 14 to 30 mm). The middle tube has a matching notch that is open at its bottom edge, so the rising wall cannot shear the sleeve.
3. From there the sleeve goes up inside the bores. Zip-tie it to the bar on the middle tube, the upper tube, and the inner tube. Keep it on the left of the T8 nut bridge (the bridge only spans the middle 28 mm). The slide pads and the stop dogs are on the flats and do not cross this lane.
4. The top KW12, on the left flat, is the full-stroke home. The lower KW12 is the collapsed home. StallGuard on the TMC2209 is the backup if a switch fails. The printed dogs are the hard stops, about 3 mm before the tubes pull apart.
5. Zip-tie the sleeve to the bar inside `col_inner_0`, and again through the two holes beside the cap hole. Those two ties are the strain relief. The cap tie is the one that moves with the torso.
6. After the torso is on, the sleeve comes through the hole in the chest shelf and splits to the Pi, the two bus adapters, and the lidar USB going back down.

## 5. Base shell

1. Fit the eight outer `base_shell_*` tiles around the centre tile. Join every seam from inside with joiner tabs; there are about 60.
2. Screw the shell lugs down to the pan inserts (12 × M3×10). Fit the e-stop and the main switch, and the GX16 charge socket in the top of the base (front right, where the right hand reaches it).

## 6. Torso

1. Yokes: drop an STS3095 into each `yoke` cup, horn outboard. Four M3×10 through the servo tabs into the inserts. Bolt both yokes to `torso_back_plate` (6 × M3×12 each, from behind).
2. `neck_mount` bridges the two yoke beams. Put the pan STS3215 in its cradle.
3. On the back plate grid: Pi 5, USB hub, two Waveshare bus adapters.
4. Set the torso on the cap. Bolt the shelf down with 4 × M5×16. The column passes through the hole in the belly.
5. Shells: the lower halves, then the upper halves. Join them from inside with joiner tabs, then screw them through the back wall into the plate. Bring the column sleeve through the shelf hole and tie it off as in section 4.

## 7. Arms (left, then mirror for the right)

1. `shoulder` onto the J1 horn: 4 × M3×8, reached through the empty J2 cup.
2. J2 STS3095 into the shoulder cup, tab screws. `clevis` onto the J2 horn.
3. J3 STS3250 into the clevis cup. Screw both `upper_arm` halves to the J3 horn, put the J4 STS3095 in the cup (its tab screws hold the two cup halves together), and close the clamshell (3 × M3×16 with nuts). The two bolt holes left on the inner side, just above the elbow, take the elbow cover's M3×50 bolts in step 7.
4. `elbow` onto the J4 horn. Put the J5 STS3250 between the `forearm` halves, close them, and bolt the forearm flange to the elbow (4 × M3×16 with nuts).
5. `wrist` clevis onto the J5 horn, with the idler screw on the other side. Put J6 in the wrist sleeve.
6. `palm` onto the J6 horn, with J7 inside it. Centre J7 at mid-travel, press the `pinion` onto the horn, slide the PETG `rack`s into their channels so they meet when the servo is at the "closed" end, and bolt on the TPU `finger`s.
7. Wiring: the Feetech bus runs down the hollow upper arm and the forearm. Cables cross each covered joint next to its axis (the open torso side of the shoulder drum, the hole under the clevis box, the ring on the outer face of the elbow knuckle). Leave slack at every joint.
8. Covers, after the wiring is checked:
   - `shoulder_cover_top` and `shoulder_cover_bot`: a drum round the J2 roll axis. Each half takes 2 × M3×10 into heat-set inserts in the shoulder tabs. The side facing the torso is open for the J2 cable.
   - `clevis_cover_a` and `clevis_cover_b`: a rounded box over the J3 cup. 2 × M3×10 each, into inserts in the clevis span.
   - `elbow_cover_a` and `elbow_cover_b`: slide the halves on from front and back, press the bottom snap shut, and put the two M3×50 bolts through the collar and the upper arm (nuts in the pockets on the front half).
   - The wrist skirt is printed on the wrist. Nothing to fit.
   To reach a servo, take off only that joint's cover: two or four screws, or for the elbow two bolts and the snap.
9. Set the Feetech IDs on each arm's bus: J1–J7 are 1–7; the head pan and tilt are 8 and 9 on the left bus. Multi-turn mode on every arm servo.

## 8. Head

1. `neck_yoke` onto the pan horn. Put the tilt STS3215 in its cradle.
2. `head_frame` onto the tilt horn and the idler. Bolt the head camera to the post. Press the ears into the side walls. Fit the `eye_plate` with both GC9A01 and the ESP32-S3.
3. Put the `visor` in the front opening of `head_upper`. The eye plate clamps its lip. Close `head_lower` to `head_upper` with joiner tabs, then screw the floor to the frame from below.

## 9. Bring-up

1. Home the lift and check every joint's direction and zero against the viewer (`sim/bob_v3.xml` uses the same conventions).
2. Set torque limits: STS3095 and STS3250 at 80% of stall, STS3215 gripper at about 0.5 N·m. The servos home from their own encoders.
3. Run the pick in sim with `sim/expert.py`. Then teleoperate the real robot and record your own demonstrations.
