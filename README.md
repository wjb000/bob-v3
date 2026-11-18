# Bob v3

A two-armed home robot you can print on a 200 mm printer. It has a rounded wheeled base, a torso that rides a 650 mm lift, two seven-axis arms with parallel grippers, and a head with a depth camera and two round "eye" displays. Everything structural and everything you see is printed PETG. You buy the motors, the electronics, two steel rods, a leadscrew, bearings and screws.

Page: [wyat.dev/bob-v3](https://www.wyat.dev/bob-v3/). It shows the 3D model, the print files, the wiring, the BOM and the sim results.

This is a design that has been checked in CAD and in physics simulation. It has not been built yet. The things the sim cannot prove are listed in [VERIFY.md](VERIFY.md). Measure those on the real parts before you print the parts that depend on them.

| | |
| --- | --- |
| Size | 560 × 440 mm base, 1.13 m mast. The head top goes from 0.77 m to 1.42 m. |
| Reach | Floor 0.32–0.45 m in front of the nose, a 0.91 m counter, a 1.55 m shelf. The hand reaches 1.74 m up and 0.81 m to the side. |
| Payload | 0.5 kg per hand at full reach for short holds. About 0.4 kg continuous; the wrist servo is the limit. |
| Joints | 19 driven: 2 hub wheels, lift, head pan and tilt, and 7 per arm (six joints plus the gripper). |
| Gripper | Rack and pinion parallel jaw, 0–80 mm, about 40 N per finger. |
| Mass | 21.3 kg (printed parts at 4 walls / 20%, bought parts at listed mass, 1.7 kg of wiring and screws). |
| Prints | 164 prints from 86 files, about 7 kg of PETG, all inside 200 × 200 × 200 mm. |
| Cost | About $3,000 for everything, or $2,830 if you reuse the Bob v2 hubs, pack and drivers. See [BOM.md](BOM.md). |
| Compute | Jetson Orin Nano Super. RealSense D435i in the head, a USB camera on each wrist, RPLIDAR C1 in the base. |

## Actuators

| Joint | Actuator | Rated / peak | Worst gravity load, 0.5 kg in the hand |
| --- | --- | --- | --- |
| Shoulder pitch (J1) | Damiao DM-J4340-2EC | 9 / 27 N·m | 6.1 N·m (68% of rated) |
| Shoulder roll (J2) | Damiao DM-J4340-2EC | 9 / 27 N·m | 5.7 N·m (63%) |
| Upper-arm yaw (J3) | Damiao DM-J4310-2EC V1.1 | 3 / 7 N·m | 2.8 N·m (93%) |
| Elbow (J4) | Damiao DM-J4310-2EC V1.1 | 3 / 7 N·m | 2.8 N·m (95%) |
| Wrist pitch (J5) | Feetech STS3215 12 V | 0.98 / 2.94 N·m | 1.1 N·m (113%, 38% of stall) |
| Wrist roll (J6) | Feetech STS3215 12 V | 0.98 / 2.94 N·m | ~0 |
| Gripper (J7) | Feetech STS3215 12 V, 12 mm pinion | about 40 N per finger | |
| Head pan, tilt | Feetech STS3215 12 V | | |
| Lift | NEMA 17 48 mm, TR8×2 leadscrew | about 380 N, 25 mm/s | 84 N |
| Wheels | 6.5 in hoverboard hubs, ZS-X11H | 0.8 m/s | |

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

`sim/bob_v3.xml` is generated from the CAD, so the meshes, masses, joint axes and limits are the same ones you print. The actuator models use datasheet torque limits. Every check currently passes:

| Check | Result |
| --- | --- |
| Stands at home | no drift, no tilt |
| Holds both arms straight out with 0.5 kg each | 1.6° worst sag, no actuator saturated |
| Lift 0 → 650 mm at the stepper's 25 mm/s | 22 s, holds within 1.4 mm |
| Drives 0.8 m/s, stops at 1–6 m/s² with the torso up and arms out | 0.2° tilt |
| Shove at the head, torso up, arms out, 0.5 kg each | tips at 30 N forward, 45 N back |
| Steepest ramp in that worst pose | 11.5° nose down, 27.9° up, 17.5° sideways |
| Floor, counter, top shelf by IK, no self-collision | all reached |
| Scripted pick off a 0.75 m table | 95% of 40 random placements |
| Behaviour cloning on 390 scripted demos (MLP on state) | 39/50 picks on unseen placements |

To train your own policy, see [sim/README.md](sim/README.md).

## Safety

The base drives a 21 kg robot on 36 V. The e-stop on the base drops a contactor in series with the 24 V arm rail, the 12 V servo and stepper rail, and the hub controllers. The Jetson stays up. The leadscrew is self-locking, so the torso stays where it is with the power off. The Damiao motors go limp when they lose power. The arms fall but the torso doesn't. Keep the arms in the home pose when you are working near the robot.

## Older versions

The single-arm cart that used to be "Bob v3" is in git history (`git log -- cad/model.py`).
