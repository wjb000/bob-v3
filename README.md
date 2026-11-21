# Bob v3

A two-armed home robot you can print on a 200 mm printer. It has a rounded-square base, a four-stage telescoping column that grows out of the base, two seven-axis arms with parallel grippers, and a head with a depth camera and two round "eye" displays. Everything structural and everything you see is printed PETG, plus three steel ballast pads low in the rear of the base. You buy the motors, the electronics, a short leadscrew, GT2 belts and screws.

Page: [wyat.dev/bob-v3](https://www.wyat.dev/bob-v3/). It shows the 3D model, the print files, the wiring, the BOM and the sim results.

This is a design that has been checked in CAD and in physics simulation. It has not been built yet. The things the sim cannot prove are listed in [VERIFY.md](VERIFY.md). Measure those on the real parts before you print the parts that depend on them.

| | |
| --- | --- |
| Size | 470 mm square base with 104 mm corner radii (turns in a 664 mm diagonal), 240 mm wide torso sitting on the column, 382 mm nested column that extends 558 mm (22 in). At the bottom of travel the torso sits 40 mm above the base, so the hands still reach the floor. The head top goes from about 0.70 m to 1.26 m. |
| Reach | With the lift down, the hands touch the floor about 0.28 m past the nose. A 0.91 m counter is in reach. Straight overhead the fingertip reaches 1.64 m (5 ft 5 in) with no self-collision. A point 0.40 m forward at 1.55 m is beyond the arm. |
| Payload | 0.5 kg (1.1 lb) per hand straight out is past the STS3095 rated torque and near stall. That rating does not change with the base. Keep the arms in, elbow bent, whenever the lift is high. A load held close to the chest is well inside the same servos. There is no stronger STS-series servo in the same cup, and the printed 5:1 modules are not coming back. |
| Joints | 19 driven: 2 hub wheels, lift, head pan and tilt, and 7 per arm (six joints plus the gripper). |
| Gripper | Geared parallel jaw, Nori-style TPU fingers, 0–80 mm, about 40 N per finger. |
| Mass | 17.3 kg with the printed parts at their wall and infill settings and the bought parts at their listed mass. About 5.0 kg of that is the three rear steel pads. |
| Prints | 165 prints from 90 files, about 5.9 kg of filament, all inside 200 × 200 × 200 mm. Still six 1 kg spools. |
| Cost | About $2,751 for every part at the linked stores, or $2,476 if you reuse the Bob v2 Pi 5, battery and charger. The square base, the stop dogs, the drag-chain links and the joint fairings are printed, so this pass does not add a purchased line. The extra over the older $2,686 total is still the second GT2 pulley pack, the PET sleeve, and the 1018 bar. See [BOM.md](BOM.md). |
| Compute | Raspberry Pi 5 on the robot; big models run on a desktop GPU over Wi-Fi. A wide RGB camera in the head, a USB camera on each wrist, RPLIDAR C1 in the base. |

## This revision

The base is a 470 × 470 mm rounded square, corner radius 104 mm, with the cyan light strip in the bottom edge and the red e-stop on the rear of the top. Casters sit at ±176 mm, drive wheels at ±200 mm. Three 1018 pads, about 5 kg together, sit low and aft so a shove at the head has to lift that steel. The turning diagonal is 664 mm.

The lift was already four stages and 558 mm (22 in). This pass finishes the parts that make that travel real: inward and outward stop dogs on every tube, a second KW12 at the top of the outer tube, a zip-tie bar on each sliding stage, and a six-link drag chain in the base trough. Collapsed shoulder height stays 452 mm, so the hands still touch the floor. Full extension puts the fingertip near 1.64 m (5 ft 5 in).

Shoulders, the clevis, the elbow and the wrist sleeve now have a second rib or a rounded bead over the square edge. The added plastic stays inside the joint swing and off the servo bodies. It does not raise the continuous payload. The shoulder still sags a few degrees with 0.5 kg straight out. Bring the arms in when the column is up.

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
| Stands at home | drift 0.4 mm, tilt 0.01° |
| Arm torque, 0.5 kg in each hand | passes on peak. Shoulder pitch is at 64% of peak, 270% of the continuous rating. Keep the load in close when the lift is high. |
| Holds both arms straight out with 0.5 kg each | the base does not tip (0.01°). The shoulder sags 4.3°, so this check fails the 3° tracking limit. No actuator saturated. |
| Lift 0 → 558 mm | 18.6 s at 25 mm/s. The TR8×2 holds with the power off, within 1.1 mm at 64 N. |
| Drives 0.6 m/s, stops at 1–6 m/s² with the torso up and arms out | passes, max tilt 0.12° |
| Shove at the head, torso up, arms out, 0.5 kg each | passes: 31.6 N forward and 29.3 N back before it tips. The check wants 25 N both ways. |
| Steepest ramp in that worst pose | passes: 20.0° nose down, 27.5° nose up, 25.9° sideways |
| Workspace sample, 6000 poses | an arms-up pose reaches 1.64 m. A point on the floor in front of the nose is in the samples. |
| Floor, counter, charge socket by IK | a floor point just past the nose, the counter and the charge socket are reached. The 1.55 m shelf point 0.40 m forward is not: the arm is not long enough, so bring the base closer. |
| Scripted pick off a 0.75 m table | 62% of 40 random placements |

To train your own policy, see [sim/README.md](sim/README.md).

## Safety

The 36 V pack charges through a GX16 socket on top of the base; Bob can plug his own charger in. The e-stop drops a contactor in series with every motor converter. The Pi stays up. The TR8×2 that drives the middle tube is self-locking, so the column stays where it is with the power off. The arm servos go limp when they lose power. Keep the arms in the home pose when you are working near the robot.

## Older versions

The single-arm cart that used to be "Bob v3" is in git history (`git log -- cad/model.py`).
