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
| Head camera board | 38 × 38 mm, M12 lens, 4 × M2 on a 34 mm square | `vendor.rgb_cam`, `HEAD_CAM_HOLE` | head_frame post |
| RPLIDAR C1 base holes | 4 × M2.5 on a 34 mm square | `base.py` `lidar_mount` | lidar_mount |
| GC9A01 module | Ø39 PCB, Ø32.4 glass | `EYE_PCB`, `EYE_GLASS` | eye_plate, visor |
| T8 flange nut | Ø22, 4 × M3 on Ø16 | `T8_FLANGE`, `T8_PCD` | col_mid_0 |

Things the sim models but can't prove:

- **Gripper gears and force.** Pitch radius is 12 mm (16T module 1.5 involute, 0.1 mm backlash, covered by `palm_lid`). Rated STS3215 torque 0.98 N·m gives 40.8 N per finger; stall 2.94 N·m would be 122 N per finger (not for continuous use). A bought metal 16T module-1.5 pinion is the intended wear part and can use the rated 40.8 N. A printed PETG pinion at 100% infill should be torque-limited to about 0.5 N·m (~20.8 N per finger) or the teeth wear quickly. Travel is 50 mm per finger (100 mm opening, 239° of servo).
- **Gripper sensing.** On the real arm, use the STS3215 present-current register as the grasp and payload signal for the reach-limit interlock (a load in the hand raises holding current). In the sim, `grip_frc_l_gripper` / `grip_frc_r_gripper` are the per-finger actuator forces, a current proxy; the touch pads still report contact. Each TPU finger has an 18 × 18 × 0.6 mm pocket for an optional Interlink FSR 402 under the pad.
- **STS3095 hold.** The hold check's 3° tracking error was a position-loop sag, not stall: at the furthest allowed pose the shoulder needs 5.4 N·m of its 9.3 N·m peak, and with kp = 80 N·m/rad that is 3.87°. `sim/check.py` now commands a gravity-compensating goal offset, `ctrl = q_des + tau_g / kp`, computed from the MuJoCo model. A real STS3095 can be given the same position offset (from a gravity model or from measured load). This is not a higher kp. Rated torque is 22.5 kg·cm (2.2 N·m). There is no stronger Feetech STS in this 30 × 65 × 48 mm case. The STS3250 is 50 kg·cm and a smaller case, so it is not a drop-in upgrade. A 0.5 kg payload straight out sits past the rated torque and near stall. Bend the elbow and keep the load near the chest when the lift is up. Expect the thermal cut to trip if you hold the straight-out pose.
- **Column stiffness.** Four printed tubes. At full stretch the engagement is about 190 mm at the base, 90 mm at the middle stage and 90 mm at the top. The sim treats the lift as rigid. If the torso nods more than you like, print the tubes at 6 walls / 50% or sleeve the middle tube with a thin aluminium square tube.
- **No ballast, ball transfers.** There is no steel in the base. Two igus polymer ball transfers sit 177 mm ahead of the axle and two 127 mm behind it, at ±45 mm. igus lists no noise figure and no rolling-friction coefficient for them; they are chosen for the POM ball (no steel ball on the floor) and the 180 N static rating. The flange thickness in the CAD is drawn (1.5 mm), not from the catalogue; measure yours and set `BALL_XFER_FLANGE_T` so each ball sits 1 mm off the floor. Ball transfers roll well on hard floors and drag on thick carpet; try one on your floors. The reach-limit interlock needs a payload signal: the sim can use the gripper touch pads or the `grip_frc_*` actuator-force sensors; the real arm should read gripper present-current. Test the interlock with a 0.5 kg weight before trusting it with the column up.
- **Battery runtime.** 158 Wh is about 3 hours of mixed use with the Pi 5. Holding both arms out under load cuts that roughly in half.
- **Homing.** The servos run in multi-turn mode. If one loses power on its own, re-home that joint before moving it.
