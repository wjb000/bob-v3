# Print and assembly

PETG, 0.2 mm layers, 15% gyroid. The solid mesh is 3.74 kg (`cad/reports/manifest.json`, volume × 1.27 g/cm³). Infill makes the printed mass lower. Buy enough PETG for the solid number.

| Parts | Walls | Notes |
| --- | --- | --- |
| Tower segments, carriage, pods | 4 | These carry the arm. |
| Deck tiles, splices, plate, straps | 3 | Skin is 2.6 mm. |
| Casters, rollers, clips, shoe, tray | 3 | Rollers are a stabilizer, not the drive wheels. |

The STLs in `cad/stl/` are already in print orientation, with the bounding box on the origin. Pods and casters are rotated so the axle bore is vertical. Do not rotate them again. Every part is under 208 mm in X and Y. The tallest tower piece is the 172 mm bottom segment.

No support is required on the deck, the plate, or the straps. The tower prints open-side up, the way the STL sits. The carriage nut traps open toward the bed; pause is not required if the traps bridge.

## Order

1. Print the eight `deck_c*_r*` tiles and the splices. Bolt the deck with M3 screws from above and nuts in the splices and the bosses. The motor window straddles the centre joint of column 1. The long splice under that column is the two short `splice_tower_*` bars, one on each side of the window.
2. Hang the v2 hubs in `pod_left` and `pod_right`. Drill the bore to the real axle. Confirm the deck still drives straight before the column goes on.
3. Print the five tower segments. Bolt them ear to ear. The nut sits in the cup on the top of each ear. On the bottom segment, screw the NEMA 17 to the plate from inside the tower, shaft up, before the carriage is on the rods. The motor body hangs through the deck window. Its face is at 52 mm.
4. Drop the two 8 mm rods into the bottom collars. They stop on the blind floor. Slide the carriage on from the top, LM8UU in the four housings, caps on after. Then the top segment. The T8 nut drops into the pocket from underneath the bridge. Four M3 screws thread into that nut. Use a TR8×2.
5. Bolt `arm_plate` to the carriage. The SO-101 base is clamped by the two straps, not by a bolt pattern copied off the servo. The slots let you clock the base until the servo tower sits between the straps. Print the official SO-101 links separately.
6. `elec_tray` takes the Pi (58 × 49 mm, M2.5) and zip-ties the buck and the TMC2209. `cam_shoe` is only for the camera you already have. `pad_clip` stays in a drawer until the gripper pinches it. `cable_clip` is for the servo lead up the tower.

## Stop

Cutting wheel power is still the v2 stop. Also drop the stepper enable and torque the servo bus off. The leadscrew holds the carriage when the stepper is off. A TR8×8 will not.
