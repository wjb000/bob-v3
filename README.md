# Bob v3

A two-armed home robot you can print on a 200 mm printer. It has a rounded-rectangle base, a four-stage telescoping column that grows out of the base, two seven-axis arms with parallel grippers, and a head with a wide RGB camera and two round "eye" displays. Everything structural and everything you see is printed PETG. There is no ballast. You buy the motors, the electronics, a short leadscrew, GT2 belts and screws.

Page: [wyat.dev/bob-v3](https://www.wyat.dev/bob-v3/). It shows the 3D model, the print files, the wiring, the BOM and the sim results.

This is a design that has been checked in CAD and in physics simulation. It has not been built yet. The things the sim cannot prove are listed in [VERIFY.md](VERIFY.md). Measure those on the real parts before you print the parts that depend on them.

| | |
| --- | --- |
| Size | 360 × 360 mm square base with 70 mm corner radii, set 25 mm forward of the wheel axle (turns in place inside a 488 mm circle), 240 mm wide torso sitting on the column, 344 mm nested column that extends 462 mm (18.2 in). At the bottom of travel the torso sits 40 mm above the base, so the hands still reach the floor. The top of the head shell is 0.660 m stowed and 1.122 m at full lift (measured on the sim meshes). |
| Reach | With the lift down, the hands touch the floor about 0.24 m past the nose. A 0.91 m counter is in reach. Straight overhead the fingertip reaches 1.50 m with no self-collision. A shelf point 0.30 m forward at 1.25 m is in reach; the old 1.55 m point is not. |
| Payload | 0.5 kg (1.1 lb) per hand. A reach-limit interlock in the controller (`sim/interlock.py`) blocks reaching out with a load: with the column at the bottom the hands may go out to the carry pose (0.53 m ahead of the axle); once the column rises they stay within 0.16 m of the axle and no higher than the shoulders, tucked at the chest or down by the sides. A grasp made further out can be lifted and pulled in, never pushed further out. |
| Joints | 19 driven: 2 hub wheels, lift, head pan and tilt, and 7 per arm (six joints plus the gripper). |
| Gripper | Geared parallel jaw, Nori-style TPU fingers, 0–80 mm, about 40 N per finger. |
| Mass | 13.45 kg in the sim: 11.7 kg of parts (the printed parts at their wall and infill settings and the bought parts at their listed mass) plus 1.76 kg the sim adds for wiring, screws and small hardware (1.2 kg in the base, 0.56 kg on the lift stages). No steel ballast. |
| Prints | 157 prints from 94 files, about 5.3 kg of filament, all inside 200 × 200 × 200 mm. |
| Cost | About $2,876 for every part at the linked stores, or $2,601 if you reuse the Bob v2 Pi 5, battery and charger. Four igus polymer ball transfers ($16.94 each at one piece) replace the swivel casters and their six 608ZZ bearings. See [BOM.md](BOM.md). |
| Compute | Raspberry Pi 5 on the robot; big models run on a desktop GPU over Wi-Fi. A wide RGB camera in the head, a USB camera on each wrist, RPLIDAR C1 in the base. |

## This revision

The base is a 360 × 360 mm square with 70 mm corner radii, the cyan light strip in the bottom edge and the red e-stop on the rear of the top. It sits 25 mm forward of the wheel axle, drive wheels at ±150 mm. Four igus xiros BB-515-B180-POM-ES polymer ball transfers (15 mm POM ball on stainless support balls, no metal ball on the floor) press into printed feet under the pan, two 177 mm ahead of the axle and two 127 mm behind it, each pair at ±45 mm. The balls sit 1 mm above the floor with the robot level, so the tires carry most of the weight and a ball only touches when the base leans. A swivel caster needs a swing hole that the square base had no room for; the ball transfers put the front contact 67 mm further forward than a swivel caster could sit, and two per end put a support corner under each side instead of one ball on the centreline. It turns in place inside a 488 mm circle (547 mm on the 440 × 360 base). Every pan and shell tile fits a 200 mm bed and every joint is a screw into an insert or a nut, no glue. The empty rear-right shelf is gone.

The robot is shorter and the proportions closer to square: the collapsed shoulder is 410 mm (was 452), the base top 200 mm, and each tube is shorter, so the lift travels 462 mm (18.2 in, was 558 mm). The top of the head shell is 0.660 m stowed and 1.122 m at full lift. The lift still runs bottom → top → bottom in the sim with 0.5 kg per hand.

The arms are now fully covered. Printed clamshell covers enclose every arm servo, horn and bracket from the shoulder to the wrist: a drum over the shoulder pitch servo (top and bottom halves), a rounded box over the clevis (two halves), and a tapered knuckle over the elbow (two halves that snap together and bolt through the upper arm), with a skirt printed into the wrist. That is 12 cover prints, six per arm, held by 16 M3×10 screws into heat-set inserts and 4 M3×50 bolts with nuts, no glue. Each cover comes off with 2–4 screws for servo service, and the cables enter near each joint axis. A clearance sweep (`tools/arm_clearance.py`, result in `docs/arm_clearance.json`) shows the covers add no new joint limit.

The head shell is one print. It drops over the head frame from above, and four M3×10 screws go up through the frame plate, which is now the head's floor, into inserts in the shell's side walls. That replaces the two-piece shell, its six joiner tabs and the twelve inserts and screws at the seam (7 fewer prints, 12 fewer inserts and 12 fewer M3×10). The shell's bottom edge is straight inside so it clears the eye plate on the way down, and the skirt is 1 mm shorter so the chin clears the torso as before at full tilt down. The head-top height and the head joint limits are unchanged.

## Direct bus servos

The arms use Feetech STS-series servos in printed cups, the same three grades Nori A3 matches to joint load. Gravity joints (shoulder pitch, shoulder roll, elbow) are STS3095 (95 kg·cm, dual shaft, rear shaft in a printed hole). Upper-arm yaw and wrist pitch are STS3250 (50 kg·cm). Wrist roll, gripper and the head are STS3215 (30 kg·cm). No printed planetaries, no 6807 bearings, no hall homing: the servo encoder is the joint encoder. Cups are in `cad/servo.py`. The gripper is a rack-and-pinion parallel jaw with Nori-style TPU 95A fingers; the second finger mimics the first.

## Head limits

The head pans ±0.8 rad and tilts −0.45 to +0.55 rad. The column sits under the torso, so the head no longer hits a mast. The CAD check tests full pan at level gaze, full tilt up and down, and pan with tilt down.

## Actuators

| Joint | Actuator | Rated / peak | Worst gravity load, 0.5 kg in the hand |
| --- | --- | --- | --- |
| Shoulder pitch (J1) | Feetech STS3095 12 V | 2.2 / 9.3 N·m | 5.9 N·m (63% of stall) |
| Shoulder roll (J2) | Feetech STS3095 12 V | 2.2 / 9.3 N·m | 5.5 N·m (59% of stall) |
| Upper-arm yaw (J3) | Feetech STS3250 12 V | 1.57 / 4.9 N·m | 2.8 N·m at the worst pose |
| Elbow (J4) | Feetech STS3095 12 V | 2.2 / 9.3 N·m | 2.9 N·m |
| Wrist pitch (J5) | Feetech STS3250 12 V | 1.57 / 4.9 N·m | 1.1 N·m (71%) |
| Wrist roll (J6) | Feetech STS3215 12 V | 0.98 / 2.94 N·m | ~0 |
| Gripper (J7) | Feetech STS3215 12 V, 12 mm pinion | about 40 N per finger | |
| Head pan, tilt | Feetech STS3215 12 V | | |
| Lift | NEMA 17 48 mm in the base, TR8×2 on the middle tube, GT2 cascade 3:1 | about 380 N at the screw, 25 mm/s at the torso | the torso and the arms |
| Wheels | 2 × Waveshare DDSM115 direct-drive hub motor, 12 V | 0.96 / 2.0 N·m | about 0.6 m/s |

The torques come from `sim/check.py`. It runs MuJoCo inverse dynamics on the CAD masses at the worst pose for each joint.

## What's in here

```
cad/          CadQuery source. params.py holds every dimension; export.py builds and checks everything
  stl/        print-ready STLs, already oriented   (generated)
  step/       STEP per part, plus bob_v3.step for the whole robot at the home pose  (generated)
  scene.json  links, joints, poses, masses: the viewer and the sim both read this  (generated)
sim/          MuJoCo model, checks, gym environments, scripted expert, training
docs/         bom.py (the BOM data), renders
tools/        make_docs.py (BOM.md, PRINT.md), publish.py (website files)
PRINT.md      what to print, colours, settings, support
BOM.md        what to buy, with links and prices
ASSEMBLY.md   build order
VERIFY.md     measure these before printing the parts that depend on them
```

## Build it from source

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-sim.txt
.venv/bin/python cad/export.py          # CAD -> STL, STEP, scene.json; fails on any fit or collision error
.venv/bin/python sim/build_mjcf.py      # scene.json -> sim/bob_v3.xml
.venv/bin/python sim/check.py           # physics checks
.venv/bin/python tools/make_docs.py     # BOM.md, PRINT.md
```

`export.py` fails the build if:

- a part doesn't fit the 200 mm cube, or isn't one solid
- any two parts or bought envelopes intersect at the home or zero pose
- a heat-set insert in the floor pan has no mating hole above it
- the centre of mass comes within 40 mm of the edge of the wheel-and-caster footprint at any named pose

## Simulation

`sim/bob_v3.xml` is generated from the CAD, so the meshes, masses, joint axes and limits are the same ones you print. The actuator models use datasheet torque limits. Numbers below are from `sim/check.py` on this column.

| Check | Result |
| --- | --- |
| Stands at home | drift 0.02 mm, tilt 0.21° (it settles onto the front pair of balls) |
| Arm torque, 0.5 kg in each hand | passes on peak. Shoulder pitch is at 67% of peak, 282% of the continuous rating. |
| Holds 0.5 kg each at the furthest pose the interlock allows (column down) | the base does not tip (0.26°). The shoulder sags 3.9°, so this check fails the 3° tracking limit. No actuator saturated. |
| Lift 0 → 462 mm → 0, hands tucked at the chest (allowed by the interlock at every height), 0.5 kg each | 18.8 s up and 18.5 s down at 25 mm/s. The middle and upper tubes follow at 1/3 and 2/3 within 0.04 mm, nothing on the robot touches anything else, and the base tilts 0.22°. Holds within 1.1 mm at 67 N. |
| Drives 0.6 m/s and stops at 1–6 m/s², torso up, worst allowed pose, 0.5 kg each | passes, max tilt 0.46° |
| Centre of mass inside the wheel-and-ball footprint | passes in four poses (the worst the interlock allows at the bottom, middle and top of the lift, and a floor pick). Worst margin 44.9 mm to the contacts it rests on (the tires and the front pair of balls; the rear pair is 1 mm off the floor until the base leans back). |
| Shove at the head, torso up, worst allowed pose, 0.5 kg each | passes: it tips at 28.7 N forward and 27.5 N back. The check wants 25 N both ways. |
| Steepest ramp in that pose | 16.0° nose down, 20.4° nose up, 13.8° left side down, 16.0° right side down (to the true wheel-to-ball edges; target 20° nose down) |
| Reach-limit interlock | blocks reaching straight out with a load at every lift height. Worst allowed pose, 0.5 kg each: column down 34.6 N forward / 79.1 N back, 20.0° nose down (meets both); lift 0.30 m 32.8 N / 29.9 N, 18.9°; full lift 28.7 N / 27.5 N, 16.0°. The 25 N shove now holds at every lift height; the 20° nose-down ramp holds only with the column down, so the check is marked failing. |
| Workspace sample, 6000 poses | an arms-up pose reaches 1.50 m. A point on the floor in front of the nose is in the samples. |
| Floor, counter, shelf, charge socket by IK | a floor point just past the nose, the 0.91 m counter, a 1.25 m shelf point 0.30 m forward and the charge socket are reached. |
| Scripted pick off a 0.75 m table, interlock on | 97.5% of 40 random placements |

To train your own policy, see [sim/README.md](sim/README.md).

## Safety

The 36 V pack charges through a GX16 socket on top of the base; Bob can plug his own charger in. The e-stop drops a contactor in series with every motor converter. The Pi stays up. The TR8×2 that drives the middle tube is self-locking, so the column stays where it is with the power off. The arm servos go limp when they lose power. Keep the arms in the home pose when you are working near the robot.

## Older versions

The single-arm cart that used to be "Bob v3" is in git history (`git log -- cad/model.py`).
