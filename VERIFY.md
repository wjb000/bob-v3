# Verify before you print

These numbers came from datasheets and store listings, not from parts on a bench. Each one only affects a small part, so if a number is wrong you reprint that adapter, not the robot. Measure each part when it arrives, change `cad/params.py`, and rerun `cad/export.py`.

| What | Value in the CAD | Where it is in `params.py` | Reprint if wrong |
| --- | --- | --- | --- |
| STS3250 case and spline | 45 × 25 × 35, 25 T | `STS_L`, `STS_W`, `STS_H` | GM-5 housing and cap, forearm halves |
| 6807 bearing | 35 × 47 × 7 | `gearbox.BEARING` | GM-5 housing, carrier |
| GM-5 gear backlash | 0.15 mm per flank | `gearbox._teeth` | sun, planets; print one module and turn it by hand first |
| STS3215 shaft offset from the case end | 11.5 mm | `STS_SHAFT_FROM_END` | forearm halves, wrist, palm, neck parts |
| STS3215 horn screw circle | 4 × M2 on Ø14 | `STS_HORN_PCD` | wrist, palm, pinion, neck yoke, head frame |
| Hoverboard axle | Ø12, 10 mm across the flats | `AXLE_D`, `AXLE_FLATS` | axle blocks and caps |
| Tire diameter and width | 165 × 45 | `WHEEL_OD`, `WHEEL_W` | casters set the ride height: if the tire is smaller, shim the caster bridges |
| Battery pack | 80 × 200 × 70 | `BATT` | battery cradle halves |
| Head camera board | 38 × 38 mm, M12 lens | `vendor.rgb_cam` | head_frame post |
| RPLIDAR C1 base holes | 4 × M2.5 on a 34 mm square | `base.py` `lidar_mount` | lidar_mount |
| GC9A01 module | Ø39 PCB, Ø32.4 glass | `EYE_PCB`, `EYE_GLASS` | eye_plate, visor |
| T8 flange nut | Ø22, 4 × M3 on Ø16 | `T8_FLANGE`, `T8_PCD` | carriage |

Things the sim models but can't prove:

- **Printed gear life.** The pinion is PETG at 100% infill. Grip force is set by the servo torque limit (about 0.5 N·m, roughly 40 N per finger). Above that the teeth wear quickly.
- **Printed gears.** The GM-5 gears are PETG at 100% infill, or PETG-CF. At the 6.7 N·m rated output the sun teeth see about 11 MPa; at the 20.8 N·m peak about 35 MPa, near PETG's limit. Keep the servo torque limit at 80% and expect to reprint suns after heavy use.
- **Rod deflection under the torso.** The 12 mm rods are 1 m long and fixed at both ends. The sim treats the lift as rigid. If the torso nods more than you like, an aluminium 2020 extrusion fits behind the rods, inside the mast.
- **Battery runtime.** 158 Wh is about 3 hours of mixed use with the Pi 5. Holding both arms out under load cuts that roughly in half.
- **Homing.** The servos run in multi-turn mode after homing to the hall index. If one loses power on its own, re-home that joint before moving it.
