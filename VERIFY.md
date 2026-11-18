# Verify before you print

These numbers came from datasheets and store listings, not from parts on a bench. Each one only affects a small part, so if a number is wrong you reprint that adapter, not the robot. Measure each part when it arrives, change `cad/params.py`, and rerun `cad/export.py`.

| What | Value in the CAD | Where it is in `params.py` | Reprint if wrong |
| --- | --- | --- | --- |
| Damiao output flange bolt circle | 6 × M3 on Ø32 | `DM_OUT_PCD`, `DM_OUT_N` | shoulder, clevis, upper arm halves, elbow |
| Damiao rear face bolt circle | 4 × M3 on Ø44 | `DM_REAR_PCD`, `DM_REAR_N` | yokes, shoulder, clevis, upper arm halves |
| DM-J4340 body | Ø57 × 53.3 | `DM4340_D`, `DM4340_H` | yokes, shoulder |
| DM-J4310 V1.1 body | Ø56 × 46 (some listings say 57) | `DM4310_D`, `DM4310_H` | clevis, upper arm halves |
| STS3215 shaft offset from the case end | 11.5 mm | `STS_SHAFT_FROM_END` | forearm halves, wrist, palm, neck parts |
| STS3215 horn screw circle | 4 × M2 on Ø14 | `STS_HORN_PCD` | wrist, palm, pinion, neck yoke, head frame |
| Hoverboard axle | Ø12, 10 mm across the flats | `AXLE_D`, `AXLE_FLATS` | axle blocks and caps |
| Tire diameter and width | 165 × 45 | `WHEEL_OD`, `WHEEL_W` | casters set the ride height: if the tire is smaller, shim the caster bridges |
| Battery pack | 80 × 200 × 70 | `BATT` | battery cradle halves |
| RealSense D435i rear holes | 2 × M3, 45 mm apart | `head.py` | head_frame |
| RPLIDAR C1 base holes | 4 × M2.5 on a 34 mm square | `base.py` `lidar_mount` | lidar_mount |
| GC9A01 module | Ø39 PCB, Ø32.4 glass | `EYE_PCB`, `EYE_GLASS` | eye_plate, visor |
| T8 flange nut | Ø22, 4 × M3 on Ø16 | `T8_FLANGE`, `T8_PCD` | carriage |

Things the sim models but can't prove:

- **Printed gear life.** The pinion is PETG at 100% infill. Grip force is set by the servo torque limit (about 0.5 N·m, roughly 40 N per finger). Above that the teeth wear quickly.
- **Clamping the motor bodies.** The arm cups grip the Damiao housings and also take the rear screws. Use the rear screws. The clamp alone will slip at peak torque.
- **Rod deflection under the torso.** The 12 mm rods are 1 m long and fixed at both ends. The sim treats the lift as rigid. If the torso nods more than you like, an aluminium 2020 extrusion fits behind the rods, inside the mast.
- **Battery runtime.** 158 Wh is about 2 hours of mixed use. With the Jetson at 25 W and the arms holding, it is closer to 1.5 hours.
- **Wrist duty.** J5 sits at 113% of its rated torque with 0.5 kg held straight out. That is fine for a pick. It is not fine for holding the pose for minutes. The STS3250 (50 kg·cm) is listed in the same case size; check that before swapping it in.
