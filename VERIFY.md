# Verify before you print

These numbers came from datasheets and store listings, not from parts on a bench. Each one only affects a small part, so if a number is wrong you reprint that adapter, not the robot. Measure each part when it arrives, change `cad/params.py`, and rerun `cad/export.py`.

| What | Value in the CAD | Where it is in `params.py` | Reprint if wrong |
| --- | --- | --- | --- |
| STS3250 case and spline | 45 × 25 × 35, 25 T | `STS_L`, `STS_W`, `STS_H` | GM-5 housing and cap, forearm halves |
| 6807 bearing | 35 × 47 × 7 | `gearbox.BEARING` | GM-5 housing, carrier |
| GM-5 gear backlash | 0.15 mm per flank | `gearbox._teeth` | sun, planets; print one module and turn it by hand first |
| STS3215 shaft offset from the case end | 11.5 mm | `STS_SHAFT_FROM_END` | forearm halves, wrist, palm, neck parts |
| STS3215 horn screw circle | 4 × M2 on Ø14 | `STS_HORN_PCD` | wrist, palm, pinion, neck yoke, head frame |
| DDSM115 stub | Ø19, 3 × M2.5 on Ø15.2 (from Waveshare's STEP) | `DDSM_*` | wheel brackets |
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

## First physical prototype checklist

None of these have been measured. The robot has not been built. Each row says which constant a bad measurement should change. Do not invent a new parameter for a result the CAD does not have.

| Check | How | Constant it can change |
| --- | --- | --- |
| Servo continuous torque | Hold 40–50% of rated torque for 5 minutes. On a bare servo that is the shaft: STS3250 rated is 1.57 N·m (0.63–0.79 N·m), STS3215 rated is 0.98 N·m (0.39–0.49 N·m). On a GM-5, apply it at the flange: 40–50% of `TAU_RATED` is 2.7–3.4 N·m on J1/J2, and 40–50% of `TAU_RATED_S` is 1.7–2.1 N·m on J3/J4. | `gearbox.STS3250_RATED`, `gearbox.STS3250_STALL` (4.9 N·m), `params.STS_TAU_RATED`, `params.STS_TAU_STALL` (2.94 N·m). Module output is the servo rating times `RATIO` (5) times `EFF` (0.85): `TAU_RATED` 6.7 N·m on J1/J2, `TAU_RATED_S` 4.2 N·m on J3/J4. |
| Servo case temperature | Same hold. Probe the case, not the air next to it. Target ≤ 65 °C. There is no temperature constant today. | If the case exceeds 65 °C, lower the continuous payload in the README envelope. Do not raise `STS3250_RATED` to make the sim agree. |
| Centre of mass | Weigh the finished robot and find the balance point at the named poses. | `cad/export.py` already fails a pose whose CoM is within 40 mm of the wheel-and-caster polygon (`WHEEL_Y` 185 mm, `CASTER_X` 185 mm, `BASE_R` 240 mm). Update masses, not that margin, if the real robot is heavier in one corner. |
| Lift friction | Pull the carriage along the full `LIFT_TRAVEL` (650 mm) and note the extra force above the torso weight. The sim treats the screw as rigid. | `T8_LEAD` (2 mm) and `NEMA_HOLD` (0.55 N·m) if the screw or motor is not the one in the CAD. Friction itself is not a parameter. |
| Wheel traction | Drive and stop on wood and on carpet. The sim does not model slip. | `WHEEL_OD` (100.7 mm) if the tire is a different size. Hub rated torque in the sim is 0.96 N·m. |
| Grip force | Spring scale on one finger, jaws nearly closed. | Pinion pitch radius is 12 mm in `cad/arm.py`. The sim caps gripper torque near 0.5 N·m (`sts3215g` in `sim/build_mjcf.py`), about 40 N per finger. `GRIP_OPEN` is 80 mm. |

There is no STS3095 in this CAD. J1, J2 and J5 are STS3250. J3, J4, J6, J7 and the head are STS3215. An older note that said to probe an STS3095 was describing a servo this robot does not use.

## Servo thermal note

Measure the STS3250 and STS3215 case temperature under a steady 40–50% of rated shaft torque, as in the table above. Target ≤ 65 °C on the case.

The GM-5 joints (J1–J4) are the ones that sit near their rating: at 0.5 kg in the hand, shoulder pitch is already 87% of `TAU_RATED`. Run that thermal hold on a J1 module and on a J3 module, not only on a bare servo on the bench, because the printed housing is what blocks the airflow. J5 is a bare STS3250 and can be checked on its own.

This is a wear item. The sun gears are printed PETG. The 6.7 N·m rated output puts about 11 MPa on the sun teeth, and the 20.8 N·m peak puts about 35 MPa, near PETG's limit. A case that stays under 65 °C does not mean the teeth will last. Keep the module torque limit at 80% of stall.

## Hold 500 g for 5 minutes

This is the sag check the 4-second sim does not cover. The sim has no heat and no creep.

Clamp the base to the bench, or leave the robot free-standing only with the lift at or below 200 mm. Do not run this pose free-standing with the lift up: the envelope in README.md and ASSEMBLY.md keeps the arms in above 200 mm, because the tip checks are for arms-out with the torso raised.

Pose, matching `test_hold` in `sim/check.py`: both arms straight forward (`shoulder_pitch` −90°, elbow and wrist pitch at 0), 500 g in each hand, lift at 0.4 m if the base is clamped. Hold for 5 minutes.

What the sim did: `PAYLOAD = 0.5` kg, 4 seconds, worst joint error 2.1° (shoulder pitch), and the check fails at 3°. That 2.1° is the last `test_hold` result in `sim/reports/check.json`, not a bench measurement. Write down the joint error at 30 seconds and at 5 minutes, and the J1 and J3 case temperatures. If the error grows past 3°, or a case passes 65 °C, the 400–500 g continuous envelope does not hold and the README number has to come down. Do not edit `PAYLOAD` upward from a shorter hold.