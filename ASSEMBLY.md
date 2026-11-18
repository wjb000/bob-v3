# Assembly

Build it in this order. Several parts can't go on later: the centre base tile has to drop over the mast foot before the carriage goes in, and each arm's J1 screws have to go in before its J2 motor does.

Tools you need:

- soldering iron with a heat-set insert tip
- hex keys 1.5, 2, 2.5 and 3 mm, including a long 2.5 mm key for the mast
- 7 mm and 13 mm wrenches
- crimpers, a multimeter, and a bench supply with a current limit for first power-up

## 0. Before printing

1. Measure everything in [VERIFY.md](VERIFY.md), update `cad/params.py`, run `cad/export.py`.
2. Print a `joiner_tab` and one `axle_block` first. Check the inserts and the axle fit before you commit 7 kg of filament.

## 1. Floor pan

1. Press inserts into every Ø4.0 hole in the nine `base_pan_*` tiles. That is about 90 inserts.
2. Lay the tiles ribs-down and join every seam with `joiner_tab`s and M3×10 screws from the top.
3. Clamp the hub axles: `axle_block_l/r` onto the pan (4 × M3×10 each), axle on its flats, then `axle_cap` (2 × M3×16). Spin the wheels by hand. They must not rub the pan cut-out.

## 2. Casters and lidar

1. Press two 608ZZ into each `caster_wheel`. Bolt the wheel into its `caster_fork` with an M8×40 and a nyloc, snug but free.
2. Press a 608ZZ into the pocket under each `caster_bridge`. Hang the fork from it with an M8×40, two washers and a nyloc. It should swivel freely.
3. Bolt the bridges onto the pan, 4 × M3×10 each. Put the robot on a flat floor. Both casters and both tires must touch. Shim under a bridge if one caster floats.
4. Bolt `lidar_mount` to the front bridge and the RPLIDAR C1 to the mount.

## 3. Power and base electronics

Follow the wiring diagram on the page.

1. Strap the 36 V pack into the two `battery_cradle` halves.
2. Front shelves (`shelf_front_l/r`): the two ZS-X11H, the ESP32 and the BNO085.
3. Rear shelves (`shelf_rear_l/r`): the three bucks, the fuse block and the contactor.
4. Wire the power path: pack → main fuse → main switch → fuse block. The 19 V buck is always on and feeds the Jetson. The contactor sits between the fuse block and the 24 V buck and the ZS-X11H. The e-stop's NC contacts are in series with the contactor coil. A 12 V relay on the same loop cuts the servo and stepper branch.
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
2. Screw the shell lugs down to the pan inserts (12 × M3×10). Fit the e-stop, the charge port and the main switch in their holes.

## 6. Torso

1. Yokes: put a DM-J4340 into each `yoke` cup, rear face first. Fit the 4 rear screws. Bolt both yokes to `torso_back_plate` (6 × M3×12 each, from behind).
2. `neck_mount` bridges the two yoke beams. Put the pan STS3215 in its cradle.
3. On the back plate grid: Jetson, USB hub, two USB-CAN adapters, two Waveshare bus adapters.
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
8. Set the Damiao CAN IDs: J1–J4 are 0x01–0x04 on each arm's bus. Set the Feetech IDs: J5–J7 are 1–3, and the head pan and tilt are 7 and 8 on the left bus.

## 8. Head

1. `neck_yoke` onto the pan horn. Put the tilt STS3215 in its cradle.
2. `head_frame` onto the tilt horn and the idler. Bolt the D435i to the post (2 × M3×6). Fit the `eye_plate` with both GC9A01 and the ESP32-S3.
3. Put the `visor` in the front opening of `head_upper`. The eye plate clamps its lip. Close `head_lower` to `head_upper` with joiner tabs, then screw the floor to the frame from below.

## 9. Bring-up

1. Home the lift and check every joint's direction and zero against the viewer (`sim/bob_v3.xml` uses the same conventions).
2. Set torque limits: Damiao at peak, STS3215 gripper at about 0.5 N·m.
3. Run the pick in sim with `sim/expert.py`. Then teleoperate the real robot and record your own demonstrations.
