# Verify before you print

These numbers came from datasheets and store listings, not from parts on a bench. Each one only affects a small part, so if a number is wrong you reprint that adapter, not the robot. Measure each part when it arrives, change `cad/params.py`, and rerun `cad/export.py`.

| What | Value in the CAD | Where it is in `params.py` | Reprint if wrong |
| --- | --- | --- | --- |
| STS3215 / STS3250 case and spline | 45 × 25 × 35, 25 T | `STS_L`, `STS_W`, `STS_H` | forearm halves, J3 cup |
| STS3215 shaft offset from the case end | 11.5 mm | `STS_SHAFT_FROM_END` | forearm halves, wrist, palm, neck parts |
| STS3215 horn screw circle | 4 × M2 on Ø14 | `STS_HORN_PCD` | wrist, palm, pinion, neck yoke, head frame |
| STS3095 case, dual shaft, 15 T horn | 30 × 65 × 48, shaft 16.5 mm from end | `STS3095_*` | yoke, shoulder, elbow cups |
| STS3095 tab holes | 56 × 20 mm | `STS3095_HOLE_L`, `STS3095_HOLE_W` | those cups |
| DDSM115 stub | Ø19, 3 × M2.5 on Ø15.2 (from Waveshare's STEP) | `DDSM_*` | wheel brackets |
| Battery pack | 80 × 200 × 70 | `BATT` | battery cradle halves |
| Head camera board | 38 × 38 mm, M12 lens | `vendor.rgb_cam` | head_frame post |
| RPLIDAR C1 base holes | 4 × M2.5 on a 34 mm square | `base.py` `lidar_mount` | lidar_mount |
| GC9A01 module | Ø39 PCB, Ø32.4 glass | `EYE_PCB`, `EYE_GLASS` | eye_plate, visor |
| T8 flange nut | Ø22, 4 × M3 on Ø16 | `T8_FLANGE`, `T8_PCD` | col_mid_0 |

Things the sim models but can't prove:

- **Printed gear life.** The gripper pinion is PETG at 100% infill. Grip force is set by the servo torque limit (about 0.5 N·m, roughly 40 N per finger). Above that the teeth wear quickly.
- **STS3095 hold.** Rated torque is 22.5 kg·cm (2.2 N·m). There is no stronger Feetech STS in this 30 × 65 × 48 mm case. The STS3250 is 50 kg·cm and a smaller case, so it is not a drop-in upgrade. A 0.5 kg payload straight out sits past the rated torque and near stall. Bend the elbow and keep the load near the chest when the lift is up. Expect the thermal cut to trip if you hold the straight-out pose.
- **Column stiffness.** Four printed tubes. At full stretch the engagement is about 190 mm at the base, 90 mm at the middle stage and 90 mm at the top. The sim treats the lift as rigid. If the torso nods more than you like, print the tubes at 6 walls / 50% or sleeve the middle tube with a thin aluminium square tube.
- **Ballast.** The three steel pads are about 5.0 kg together. The port pad is on the negative-y side of the pan. The keel is just behind the column, clear of the cable trough, the buck, and the rear caster hole. The aft pad sits above the rear caster bridge. Keep all three out of the caster swing. If a pad rocks, stick it down with a strip of foam tape. Do not move it forward.
- **Battery runtime.** 158 Wh is about 3 hours of mixed use with the Pi 5. Holding both arms out under load cuts that roughly in half.
- **Homing.** The servos run in multi-turn mode. If one loses power on its own, re-home that joint before moving it.
