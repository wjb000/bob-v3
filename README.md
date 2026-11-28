# Bob v3

**STATUS: CAD + simulation only — not yet built**

*A two-armed home robot you can print on a 200 mm printer*

It has a rounded wheeled base, a torso that rides a 650 mm lift, two seven-axis arms with parallel grippers, and a head with a depth camera and two round "eye" displays. Everything structural and everything you see is printed PETG. You buy the motors, the electronics, two steel rods, a leadscrew, bearings and screws.

[Page: wyat.dev/bob-v3](https://www.wyat.dev/bob-v3/)

## Important Status Notice

**This project is currently in the design phase only.**

- CAD models and physics simulations are complete
- No physical prototype has been built yet
- All specifications and performance data are theoretical
- Actual real-world performance may vary significantly

## Design Overview

This is a design that has been checked in CAD and in physics simulation. It has not been built yet. The things the sim cannot prove are listed in [VERIFY.md](VERIFY.md). Measure those on the real parts before you print the parts that depend on them.

### Key Specifications

| | |
| --- | --- |
| **Size** | Ø480 mm round base (turns in its own footprint), 240 mm wide torso, 1.11 m mast. The head top goes from 0.76 m to 1.41 m. |
| **Reach** | Floor 0.32–0.45 m in front of the nose, a 0.91 m counter, a 1.55 m shelf. The hand reaches 1.74 m up and 0.81 m to the side. |
| **Payload** | 400–500 g per hand, continuous. The sim's checked hold is 0.5 kg. See the envelope below. |
| **Joints** | 19 driven: 2 hub wheels, lift, head pan and tilt, and 7 per arm (six joints plus the gripper). |
| **Gripper** | Rack and pinion parallel jaw, 0–80 mm, about 40 N per finger. |
| **Mass** | 14.2 kg in the CAD. The sim adds 1.7 kg for wiring and screws. |
| **Prints** | 203 prints from 92 files, 6.25 kg of filament, all inside 200 × 200 × 200 mm. |
| **Cost** | About $2,900 for every part at the linked stores, or $2,600 if you reuse the Bob v2 Pi 5, battery and charger. Every BOM line links to a specific product. See [BOM.md](BOM.md). |
| **Compute** | Raspberry Pi 5 on the robot; big models run on a desktop GPU over Wi-Fi. A wide RGB camera in the head, a USB camera on each wrist, RPLIDAR C1 in the base. |

## Safe operating envelope

Nothing in this section has been measured on a built robot. The numbers are the sim and the datasheet ratings. The procedure for checking them on hardware is in [VERIFY.md](VERIFY.md).

- **400–500 g per hand, continuous.** `sim/check.py` uses `PAYLOAD = 0.5` kg. At that load the shoulder pitch sits at 5.8 N·m, 87% of `gearbox.TAU_RATED` (6.7 N·m, from `STS3250_RATED` 1.57 N·m through the 5:1 at 85%). A heavier continuous hold is not checked.
- **Arms in when the lift is above 200 mm.** `LIFT_TRAVEL` is 650 mm and `LIMITS["lift"]` still allows the full stroke. 200 mm is an operating limit, not a joint stop. With the lift at 650 mm and both arms partly out, the current sim tips forward at 14.6 N and stands on only a 6.3° nose-down ramp. Those two checks fail their bars (25 N and 10°). Driving, and anyone standing next to the robot, keeps the elbows bent and the hands near the torso.
- **Printed joints.** The GM-5 suns and the gripper pinion are PETG. The continuous rating assumes the module torque limit stays at 80% of stall, and those gears are a wear item.

## GM-5 Joint Module

The four big joints in each arm use the same printed module. A Feetech STS3250 drives a 12-tooth sun, three 18-tooth planets and a 48-tooth ring cut into the housing (module 1.0, 5:1). The carrier runs in a 6807 bearing and carries the same 6 × M3 output flange as the arm links. A hall sensor in the housing and a magnet in the carrier home each joint at power-up, because the servo's own encoder repeats every 72° of output. Print the gears in PETG-CF or nylon if you can. `cad/gearbox.py` has the geometry and `cad/stl/gm_*.stl` the files.

## Head Limits

The head pans ±0.6 rad and tilts −0.35 to +0.55 rad. Below 0.51 m of lift, the software must not combine full pan with looking up, because the back of the head would reach the mast. The CAD check tests full pan at level gaze, full tilt up and down, and pan with tilt down.

## Actuators

| Joint | Actuator | Rated / peak | Worst gravity load, 0.5 kg in the hand |
| --- | --- | --- | --- |
| Shoulder pitch (J1) | GM-5: STS3250 + printed 5:1 planetary | 6.7 / 20.8 N·m | 5.8 N·m (87% of rated) |
| Shoulder roll (J2) | GM-5 | 6.7 / 20.8 N·m | 5.4 N·m (81%) |
| Upper-arm yaw (J3) | GM-5 with an STS3215 | 4.2 / 12.5 N·m | 2.8 N·m |
| Elbow (J4) | GM-5 with an STS3215 | 4.2 / 12.5 N·m | 2.8 N·m |
| Wrist pitch (J5) | Feetech STS3250 12 V | 1.57 / 4.9 N·m | 1.1 N·m (71%) |
| Wrist roll (J6) | Feetech STS3215 12 V | 0.98 / 2.94 N·m | ~0 |
| Gripper (J7) | Feetech STS3215 12 V, 12 mm pinion | about 40 N per finger | |
| Head pan, tilt | Feetech STS3215 12 V | | |
| Lift | NEMA 17 48 mm, TR8×2 leadscrew | about 380 N, 25 mm/s | 84 N |
| Wheels | 2 × Waveshare DDSM115 direct-drive hub motor, 12 V | 0.96 / 2.0 N·m | about 0.6 m/s |

The torques come from `sim/check.py`. It runs MuJoCo inverse dynamics on the CAD masses at the worst pose for each joint.

## What's in Here

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

## Build It From Source

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

`sim/bob_v3.xml` is generated from the CAD, so the meshes, masses, joint axes and limits are the same ones you print. The actuator models use datasheet torque limits. Push and slope fail their bars. The other checks pass.

| Check | Result |
| --- | --- |
| Stands at home | no drift, no tilt |
| Holds both arms straight out with 0.5 kg each | 2.1° worst sag, no actuator saturated |
| Lift 0 → 650 mm at the stepper's 25 mm/s | 22 s, holds within 1.0 mm, lags 5.4 mm while moving |
| Drives with the torso up and arms out, stops at 1–6 m/s² | reached 0.59 m/s, 0.18° tilt |
| Shove at the head, torso up, arms out, 0.5 kg each | fails: tips at 14.6 N forward, 31.1 N back (bar is 25 N) |
| Steepest ramp in that worst pose | fails: 6.3° nose down, 24.5° up, 15.8° sideways (bar is 10°) |
| Floor, counter, top shelf by IK, no self-collision | all reached |
| Scripted pick off a 0.75 m table | 40/40 on the committed `sim/expert.py` |
| Behaviour cloning on 390 scripted demos (MLP on state) | 39/50 picks on unseen placements |

To train your own policy, see [sim/README.md](sim/README.md).

## Safety

The 36 V pack charges through a GX16 socket on top of the base; Bob can plug his own charger in. The e-stop drops a contactor in series with every motor converter. The Pi stays up. The leadscrew is self-locking, so the torso stays where it is with the power off. The arm servos go limp when they lose power; the 5:1 gearboxes slow the fall but do not stop it. The torso does not move. Keep the arms in, elbows bent, whenever the lift is above 200 mm, and whenever you are working near the robot. The checked continuous load is 400–500 g per hand.

## Older Versions

The single-arm cart that used to be "Bob v3" is in git history (`git log -- cad/model.py`).
```