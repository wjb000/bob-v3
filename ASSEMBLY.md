# Assembly

**STATUS: CAD + simulation only — not yet built**

Build it in this order. Several parts can't go on later: the centre base tile has to drop over the mast foot before the carriage goes in, and each arm's J1 screws have to go in before its J2 motor does.

## Operating envelope

Until the measurements in [VERIFY.md](VERIFY.md) are done on hardware, use the sim limits:

- 400–500 g per hand, continuous. `sim/check.py` holds 0.5 kg. Heavier is not a cleared mode.
- Lift above 200 mm: both arms in, elbows bent. `LIFT_TRAVEL` in `cad/params.py` is 650 mm. The 200 mm line is not `LIMITS["lift"]`.
- First power-up stays on the current-limited bench supply in section 3. Do not stand the robot up with the arms out to check the sag.

Tools you need:

- soldering iron with a heat-set insert tip
- hex keys 1.5, 2, 2.5 and 3 mm, including a long 2.5 mm key for the mast
- 7 mm and 13 mm wrenches
- crimpers, a multimeter, and a bench supply with a current limit for first power-up

## 0. Before printing

1. Measure everything in [VERIFY.md](VERIFY.md), update `cad/params.py`, run `cad/export.py`.
2. Print a `joiner_tab`, one `wheel_bracket` and one GM-5 module first. Check the inserts, the DDSM115 stub fit and the gear mesh before you commit 6 kg of filament.

## 1. Floor pan

1. Press inserts into every Ø4.0 hole in the nine `base_pan_*` tiles. That is about 90 inserts.
2. Lay the tiles ribs-down and join every seam with `joiner_tab`s and M3×10 screws from the top.
3. Wheels: screw each DDSM115 to its `wheel_bracket_l/r` through the stub end (3 × M2.5 × 10 on the Ø15.2 circle), then bolt the brackets to the pan (4 × M3×10 each). Spin the wheels by hand; the tire must clear the pan cut-out.

## 2. Casters and lidar

1. Press two 608ZZ into each `caster_wheel`. Bolt the wheel into its `caster_fork` with an M8×40 and a nyloc, snug but free.
2. Press a 608ZZ into the pocket under each `caster_bridge`. Hang the fork from it with an M8×40, two washers and a nyloc. It should swivel freely.
3. Bolt the bridges onto the pan, 4 × M3×10 each. Put the robot on a flat floor. Both casters and both tires must touch. Shim under a bridge if one caster floats.
4. Bolt `lidar_mount` to the front bridge and the RPLIDAR C1 to the mount.

## 3. Power and base electronics

Follow the wiring diagram on the page.

1. Strap the 36 V pack into the two `battery_cradle` halves.
2. Front shelves (`shelf_front_l/r`): the DDSM Driver HAT (A), the TMC2209, the BNO085, the contactor, the fuse block and the two Pololu regulators.
3. Rear shelves (`shelf_rear_l/r`): the two DROK 12 V 10 A converters, one per arm.
4. Wire the power path: pack → main fuse → main switch → fuse block. The Pololu 5 V regulator is always on and feeds the Pi. The contactor sits between the fuse block and the two arm converters and the Pololu 12 V regulator (wheels and lift). The e-stop's NC contacts are in series with the contactor coil.
5. First power-up on a current-limited bench supply at 36 V, 1 A. Check each rail before connecting any load.

## 4. Mast and lift

1. Bolt `mast_0` to the pan, 8 × M3×10 through the foot flange. Fit the KW12 limit switch on its pad.
2. Drop the centre base tile (`base_shell_mid_c`) over `mast_0`. It just rests there for now.
3. Push the two 12 mm rods into the sockets and lock them with the grub screws.
4. Carriage: press in four LM12UU, screw the TR8 nut on from below, and drop the four M5 nuts into the tongue slots. Slide it down the rods from the top.
5. Stack `mast_1` to `mast_5`. Each joint takes 4 × M3×14 through the inner bosses, reached through the front slot with a long key.
6. Cap: NEMA 17 on the plate (4 × M3×8), coupler on the shaft. Thread the leadscrew through the nut from above. Seat the cap and screw it up from below into its inserts. Tighten the coupler.
7. Drive the lift end to end on the bench supply. It should run smoothly at 25 mm/s and stop on the switch.

## 5. Base shell

1. Fit the eight outer `base_shell_*` tiles around the centre tile. Join every seam from inside with joiner tabs; there are about 60.
2. Screw the shell lugs down to the pan inserts (12 × M3×10). Fit the e-stop and the main switch, and the GX16 charge socket in the top of the base (front right, where the right hand reaches it). The GX16 is the bench supply. Daily charging is the floor dock.

## 5b. Charge dock

The hoverboard charger stays on the dock. He reverses onto it; he does not plug the GX16 in by hand. The GX16 is only the bench supply, wired in parallel to the same BMS input.

1. Print the six `dock_*` tiles and the two `dock_pad_*` shims (`cad/station.py`). Each one lies flat and fits the bed.
2. Screw each island into a row of three from below. Leave the middle open so the casters stay on the floor, and leave the outside open so the wheels do. The lipped tiles face the wall.
3. Glue a brass shim on each pad. The +Y pad is pack positive. The −Y pad is pack negative. Wire them to the charger output.
4. Epoxy the two `charge_strip_*` stems into the pockets under `base_pan_mid_c`. Run 18 AWG from each strip to the GX16 charge input, in parallel with the bench plug.
5. On the viewer, Dock reverses him onto the pads. The button reads Charging when the strips are on the pads, and the drive stops there.

## 6. Torso

1. Build eight GM-5 modules: STS3250 into the housing sleeve, cap on; sun onto the horn (4 × M2); planets on the M3 × 20 pins between the carrier plates; 6807 into the housing; magnet into the carrier rim; hall sensor into its pocket. Turn each one by hand: it should run smoothly at 5:1.
2. Yokes: a GM-5 into each `yoke` cup, flange screwed to the rim (4 × M3 × 8). Bolt both yokes to `torso_back_plate` (6 × M3×12 each, from behind).
2. `neck_mount` bridges the two yoke beams. Put the pan STS3215 in its cradle.
3. On the back plate grid: Pi 5, USB hub, XIAO ESP32-C3 for the hall sensors, two Waveshare bus adapters.
4. Bolt the back plate to the carriage tongue with 4 × M5×30.
5. Shells: the lower halves, then the upper halves. Join them from inside with joiner tabs, then screw them through the back wall into the plate. Run the umbilical (36 V pair, CAN ×2, servo bus, USB) down the mast with a service loop.

## 7. Arms (left, then mirror for the right)

1. `shoulder` onto the J1 output: 6 × M3×8, reached through the empty J2 cup.
2. J2 into the shoulder cup, rear screws. `clevis` onto the J2 output.
3. J3 into the clevis cup. Screw both `upper_arm` halves to the J3 output, put J4 in the cup, and close the clamshell (6 × M3×16 with nuts).
4. `elbow` onto the J4 output. Put J5 between the `forearm` halves, close them, and bolt the forearm flange to the elbow (4 × M3×16 with nuts).
5. `wrist` clevis onto the J5 horn, with the idler screw on the other side. Put J6 in the wrist sleeve.
6. `palm` onto the J6 horn, with J7 inside it. Centre J7 at mid-travel, press the `pinion` onto the horn, and slide `finger_a` and `finger_b` into their channels so they meet when the servo is at the "closed" end. Screw on the TPU `pad`s.
7. Wiring: CAN runs down the hollow upper arm. The Feetech bus runs down the forearm. Leave slack at every joint.
8. Set the Feetech IDs on each arm's bus: J1–J4 modules are 1–4, J5–J7 are 5–7; the head pan and tilt are 8 and 9 on the left bus. Put the module servos in multi-turn mode.

## 8. Head

1. `neck_yoke` onto the pan horn. Put the tilt STS3215 in its cradle.
2. On the bench, slide `head_frame` into `head_shell` through the face until the tilt cheeks hang out of the neck slot. Screw the floor up into the frame (4 × M3×10). Bolt the camera to the post. Fit the `eye_plate` with both GC9A01 and the ESP32-S3. Press the ears in from the sides. Snap the `visor` in from the front.
3. Lower the head onto the tilt horn and the idler.

## 9. Bring-up

1. Home the lift and check every joint's direction and zero against the viewer (`sim/bob_v3.xml` uses the same conventions).
2. Home every GM-5 to its hall index. Set torque limits: modules at 80% of stall, STS3215 gripper at about 0.5 N·m.
3. Run the pick in sim with `sim/expert.py`. The first hardware checks are the list in [VERIFY.md](VERIFY.md): servo case temperature, the 500 g sag hold, centre of mass, lift friction, wheel traction, and grip force. Record those before treating any payload number as measured.
