# Bob v3

A long differential-drive base, one lift, and one SO-101 hand. The base only drives. The hand and the cameras already on Bob v2 do the chores. There is no vacuum shoe, no dish tray, and no laundry bay.

This is a design. Nothing here has been printed, and Bob v2 is still the robot in the house. The page is [wyat.dev/bob-v3](https://www.wyat.dev/bob-v3/).

The shoulder in this model runs from **186 mm to 755 mm**. Travel is **569 mm** on a **700 mm** pair of rods. Those numbers come from `cad/params.py`.

## What you print

Eight deck tiles, the splices, two wheel pods, two casters, two rollers, five tower segments, the carriage, the arm plate, two straps, an electronics tray, a shoe for the existing Pi camera, a cloth clip, and cable clips. The SO-101 links are **not** in this repo. Print those from [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100).

Open the viewer at [site/index.html](site/index.html) (GitHub Pages: `/site/`).

## Rebuild

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python cad/export.py
```

CadQuery 2.8. Edit `cad/params.py` and rerun. Print STLs land in `cad/stl/` already rotated onto a 220 mm bed. `cad/stl/placed/` is the same parts in the robot frame. `cad/step/bob_v3.step` is the assembly. Do not boolean the robot into one solid.

## Before the first print

- Measure the hoverboard axle and drill `AXLE_D` (the model uses 8.5 mm). `WHEEL_OD` is 165 mm until you measure the tire.
- Measure the T8 nut. The carriage pocket is 24 mm square and 4.5 mm deep so a round Ø22 flange or a 22 mm square flange can drop in. Reprint the carriage if yours does not.
- Buy **TR8×2** (2 mm lead). A TR8×8 creeps down under the arm. The screw and the rods are **700 mm**. The $12 and $8 lines are estimates for that length.
- The column is PETG. PLA creeps.
- Nuts are M3 hex traps in the plastic, not heat-set inserts.
- Do not power the servos or the stepper from the Pi 5 V rail. The Pi wants a real 5.1 V 5 A supply. The 12 V rail is a 36 V to 12 V buck, about 10 A.

## Upgrades, not in this print

- A second SO-101 is about $110 and stays off the robot until one hand fails a job.
- A 608ZZ can replace the printed 8.6 mm bushing in the top cap.
- A wrist camera is optional. The eyes are the v2 cameras. `cam_shoe` only moves the existing Pi camera.
- Bought plate casters, if the 30 mm printed rollers are too small.
- A longer `ROD_LEN`, only if 700 mm is still short.
