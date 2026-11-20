# Print list

86 unique files, 132 prints, about 5.0 kg of filament at the settings below.
Every part fits a 200 x 200 x 200 mm volume (Prusa MK4, Ender-3, Bambu A1/P1/X1, Core One).
The STLs in `cad/stl/` are already oriented: flat face down, no rotating. Grams are at 4 walls and 20% gyroid.

## Settings

- PETG, 0.4 mm nozzle, 0.2 mm layers, 4 walls, 5 top/bottom layers, 20% gyroid unless the table says otherwise.
- Shell tiles (`base_shell_*`, `torso_*`, `head_*`): 3 walls, 15%. They print top-down; the lugs and the lidar slot want a little support.
- Structural parts (`yoke_*`, `clevis_*`, `elbow_*`, `col_*`): 5 walls, 30%.
- `pinion_*`: 100% infill. `pad_*`: TPU 95A, 100%.
- Heat-set inserts: M3 x 5.7. Every Ø4.0 hole is an insert. Ø3.4 is clearance, Ø2.6 is thread-forming.
- Supports: the Support column is measured from each oriented STL (faces steeper than 45° not on the bed).
  'none' means under 5 cm². Use tree supports, touching the build plate only where you can.

## Base (1.61 kg)

| File | Qty | Colour | Bed mm | g each | Support | Note |
| --- | ---: | --- | --- | ---: | --- | --- |
| `base_shell_rear_r.stl` | 1 | white PETG | 89 x 89 x 182 | 56 | 16 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_rear_c.stl` | 1 | white PETG | 110 x 180 x 182 | 107 | 22 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_rear_l.stl` | 1 | white PETG | 89 x 89 x 182 | 56 | 16 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_mid_r.stl` | 1 | white PETG | 180 x 110 x 182 | 90 | 13 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_mid_c.stl` | 1 | white PETG | 180 x 180 x 12 | 51 | none | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_mid_l.stl` | 1 | white PETG | 180 x 110 x 182 | 90 | 13 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_front_r.stl` | 1 | white PETG | 89 x 89 x 182 | 51 | 18 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_front_c.stl` | 1 | white PETG | 110 x 180 x 182 | 101 | 24 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_shell_front_l.stl` | 1 | white PETG | 89 x 89 x 182 | 52 | 18 cm² | Print top-down. Heat-set inserts in the seam bosses. |
| `base_pan_rear_r.stl` | 1 | grey PETG | 80 x 80 x 15 | 20 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_rear_c.stl` | 1 | grey PETG | 102 x 180 x 15 | 62 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_rear_l.stl` | 1 | grey PETG | 80 x 80 x 15 | 22 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_mid_r.stl` | 1 | grey PETG | 180 x 93 x 15 | 60 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_mid_c.stl` | 1 | grey PETG | 180 x 180 x 15 | 130 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_mid_l.stl` | 1 | grey PETG | 180 x 93 x 15 | 59 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_front_r.stl` | 1 | grey PETG | 80 x 80 x 15 | 21 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_front_c.stl` | 1 | grey PETG | 102 x 180 x 15 | 62 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `base_pan_front_l.stl` | 1 | grey PETG | 80 x 80 x 15 | 20 | none | Structure. Skin down on the bed, ribs up. 4 walls. |
| `wheel_bracket_l.stl` | 1 | grey PETG | 52 x 30 x 37 | 33 | 5 cm² | Holds a DDSM115 by its stub (3 x M2.5 x 10). 5 walls, 40% infill. |
| `wheel_bracket_r.stl` | 1 | grey PETG | 52 x 30 x 37 | 33 | 5 cm² | Holds a DDSM115 by its stub (3 x M2.5 x 10). 5 walls, 40% infill. |
| `caster_bridge_front.stl` | 1 | grey PETG | 66 x 136 x 29 | 64 | none | Swivel 608ZZ pocket underneath. Inserts on top for the lidar mount. |
| `caster_bridge_rear.stl` | 1 | grey PETG | 66 x 136 x 29 | 64 | none |  |
| `lidar_mount.stl` | 1 | black PETG | 74 x 74 x 42 | 34 | 11 cm² | Lifts the RPLIDAR C1 to the slot in the shell. |
| `caster_fork_front.stl` | 1 | black PETG | 46 x 46 x 36 | 18 | none |  |
| `caster_wheel_front.stl` | 1 | black PETG | 40 x 40 x 22 | 15 | none | Two 608ZZ pressed in. TPU 95A if your printer does it, PETG otherwise. |
| `caster_fork_rear.stl` | 1 | black PETG | 46 x 46 x 36 | 18 | none |  |
| `caster_wheel_rear.stl` | 1 | black PETG | 40 x 40 x 22 | 15 | none | Two 608ZZ pressed in. TPU 95A if your printer does it, PETG otherwise. |
| `battery_cradle_l.stl` | 1 | grey PETG | 115 x 83 x 94 | 34 | 40 cm² | Two halves meet under the pack; the strap holds them together. |
| `battery_cradle_r.stl` | 1 | grey PETG | 115 x 83 x 94 | 34 | 40 cm² | Two halves meet under the pack; the strap holds them together. |
| `shelf_front_l.stl` | 1 | grey PETG | 70 x 75 x 109 | 28 | none | Motor drivers and the ESP32 on the 20 mm grid. |
| `shelf_rear_l.stl` | 1 | grey PETG | 47 x 54 x 109 | 18 | none | Bucks, fuse block, contactor. |
| `shelf_front_r.stl` | 1 | grey PETG | 60 x 75 x 109 | 26 | none | Motor drivers and the ESP32 on the 20 mm grid. |
| `shelf_rear_r.stl` | 1 | grey PETG | 50 x 60 x 109 | 21 | none | Bucks, fuse block, contactor. |
| `joiner_tab.stl` | 47 | grey PETG | 30 x 14 x 4 | 1 | none | Joins shell and pan tiles from inside. M3x10 into heat-set inserts. |

## Column (0.94 kg)

| File | Qty | Colour | Bed mm | g each | Support | Note |
| --- | ---: | --- | --- | ---: | --- | --- |
| `col_outer_0.stl` | 1 | white PETG | 124 x 124 x 191 | 234 | none | Foot flange, motor pedestal, homing pad. |
| `col_outer_1.stl` | 1 | white PETG | 101 x 108 x 191 | 182 | none | Top of the outer tube. Slide pads and belt anchors. |
| `col_mid_0.stl` | 1 | white PETG | 86 x 86 x 191 | 168 | 25 cm² | T8 nut pocket and outer slide pads. |
| `col_mid_1.stl` | 1 | white PETG | 83 x 83 x 191 | 149 | none | Pulleys and inner slide pads. |
| `col_inner_0.stl` | 1 | white PETG | 68 x 70 x 141 | 90 | none | Belt clamps and outer slide pads. |
| `col_inner_1.stl` | 1 | white PETG | 65 x 65 x 141 | 86 | none | Prints standing. Inserts in the top bosses. |
| `col_cap.stl` | 1 | black PETG | 76 x 76 x 8 | 29 | none | Sits on the inner tube. The torso shelf bolts down onto this plate, 4 × M5. |

## Torso (1.29 kg)

| File | Qty | Colour | Bed mm | g each | Support | Note |
| --- | ---: | --- | --- | ---: | --- | --- |
| `torso_back_plate.stl` | 1 | grey PETG | 154 x 140 x 8 | 118 | none | Yokes bolt to the front face. The Pi and the bus adapters sit beside the column. |
| `yoke_l.stl` | 1 | grey PETG | 125 x 146 x 116 | 318 | 123 cm² | Holds the left J1 STS3095. Prints on its centre face, cup up. 5 walls, 30% infill. |
| `yoke_r.stl` | 1 | grey PETG | 125 x 146 x 116 | 318 | 123 cm² | Mirror of yoke_l. |
| `neck_mount.stl` | 1 | grey PETG | 108 x 70 x 28 | 42 | 8 cm² | Pan servo cradle, bridges the yokes. |
| `torso_lower_l.stl` | 1 | white PETG | 150 x 120 x 120 | 106 | 6 cm² | Lower tier prints floor-down; upper tier prints top-down. |
| `torso_lower_r.stl` | 1 | white PETG | 150 x 120 x 120 | 106 | 6 cm² | Lower tier prints floor-down; upper tier prints top-down. |
| `torso_upper_l.stl` | 1 | white PETG | 150 x 120 x 130 | 143 | 68 cm² | Lower tier prints floor-down; upper tier prints top-down. |
| `torso_upper_r.stl` | 1 | white PETG | 150 x 120 x 130 | 143 | 68 cm² | Lower tier prints floor-down; upper tier prints top-down. |

## Head (0.36 kg)

| File | Qty | Colour | Bed mm | g each | Support | Note |
| --- | ---: | --- | --- | ---: | --- | --- |
| `ear_l.stl` | 1 | black PETG | 50 x 50 x 12 | 6 | 17 cm² | Press-fits into the head's left side. Speaker grille. |
| `ear_r.stl` | 1 | black PETG | 50 x 50 x 12 | 6 | 17 cm² | Mic grille. |
| `neck_collar.stl` | 1 | black PETG | 70 x 58 x 21 | 7 | none | Clips around the neck yoke and hides the pan servo. |
| `neck_yoke.stl` | 1 | black PETG | 54 x 42 x 64 | 28 | 20 cm² | Pan horn below, tilt servo cradle above. |
| `head_frame.stl` | 1 | grey PETG | 92 x 128 x 124 | 70 | 82 cm² | Tilt horn and idler, camera post, eye plate. |
| `eye_plate.stl` | 1 | grey PETG | 46 x 110 x 25 | 15 | 17 cm² | Two GC9A01 round TFTs. |
| `visor.stl` | 1 | black PETG | 88 x 136 x 5 | 23 | none | Black PETG, face down. Eye and camera windows. |
| `head_lower.stl` | 1 | white PETG | 120 x 176 x 24 | 57 | 9 cm² | Floor down. |
| `head_upper.stl` | 1 | white PETG | 120 x 176 x 120 | 147 | 14 cm² | Top down. Visor fits from inside. |

## Arms (0.79 kg)

| File | Qty | Colour | Bed mm | g each | Support | Note |
| --- | ---: | --- | --- | ---: | --- | --- |
| `shoulder_l.stl` | 1 | white PETG | 52 x 72 x 67 | 13 | none | J1 output to the J2 cup. Screw it to J1 before J2 goes in. |
| `clevis_l.stl` | 1 | grey PETG | 137 x 66 x 68 | 69 | 12 cm² | J2 output, holds J3. |
| `upper_arm_a_l.stl` | 1 | white PETG | 36 x 64 x 165 | 30 | 6 cm² | Clamshell half. Prints on the split face. |
| `upper_arm_b_l.stl` | 1 | white PETG | 36 x 64 x 165 | 34 | 6 cm² | Clamshell half with the nut traps. |
| `elbow_l.stl` | 1 | grey PETG | 54 x 91 x 60 | 33 | none | J4 output to the forearm flange. |
| `forearm_a_l.stl` | 1 | white PETG | 162 x 54 x 27 | 51 | 54 cm² |  |
| `forearm_b_l.stl` | 1 | white PETG | 162 x 54 x 27 | 51 | 52 cm² |  |
| `wrist_l.stl` | 1 | black PETG | 57 x 98 x 64 | 39 | 54 cm² | J5 horn and idler, holds J6. |
| `palm_l.stl` | 1 | black PETG | 62 x 110 x 58 | 52 | 36 cm² | J6 horn on top, J7 inside, rack channels underneath. |
| `pinion_l.stl` | 1 | grey PETG | 27 x 27 x 8 | 2 | none | 16T module 1.5 on the J7 horn. 100% infill. |
| `rack_a_l.stl` | 1 | black PETG | 22 x 70 x 31 | 4 | none | PETG rack and drop. Slides in from the +y end. |
| `rack_b_l.stl` | 1 | black PETG | 22 x 70 x 31 | 4 | none | PETG rack and drop. Slides in from the -y end. |
| `finger_a_l.stl` | 1 | TPU 95A | 24 x 48 x 8 | 6 | none | Nori-style TPU 95A finger. Bolts to the rack. |
| `finger_b_l.stl` | 1 | TPU 95A | 24 x 48 x 8 | 6 | none | Nori-style TPU 95A finger. |
| `shoulder_r.stl` | 1 | white PETG | 52 x 72 x 67 | 13 | none | J1 output to the J2 cup. Screw it to J1 before J2 goes in. |
| `clevis_r.stl` | 1 | grey PETG | 137 x 66 x 68 | 69 | 12 cm² | J2 output, holds J3. |
| `upper_arm_a_r.stl` | 1 | white PETG | 36 x 64 x 165 | 30 | 6 cm² | Clamshell half. Prints on the split face. |
| `upper_arm_b_r.stl` | 1 | white PETG | 36 x 64 x 165 | 34 | 6 cm² | Clamshell half with the nut traps. |
| `elbow_r.stl` | 1 | grey PETG | 54 x 91 x 60 | 33 | none | J4 output to the forearm flange. |
| `forearm_a_r.stl` | 1 | white PETG | 162 x 54 x 27 | 51 | 54 cm² |  |
| `forearm_b_r.stl` | 1 | white PETG | 162 x 54 x 27 | 51 | 52 cm² |  |
| `wrist_r.stl` | 1 | black PETG | 57 x 98 x 64 | 39 | 54 cm² | J5 horn and idler, holds J6. |
| `palm_r.stl` | 1 | black PETG | 62 x 110 x 58 | 52 | 36 cm² | J6 horn on top, J7 inside, rack channels underneath. |
| `pinion_r.stl` | 1 | grey PETG | 27 x 27 x 8 | 2 | none | 16T module 1.5 on the J7 horn. 100% infill. |
| `rack_a_r.stl` | 1 | black PETG | 22 x 70 x 31 | 4 | none | PETG rack and drop. Slides in from the +y end. |
| `rack_b_r.stl` | 1 | black PETG | 22 x 70 x 31 | 4 | none | PETG rack and drop. Slides in from the -y end. |
| `finger_a_r.stl` | 1 | TPU 95A | 24 x 48 x 8 | 6 | none | Nori-style TPU 95A finger. Bolts to the rack. |
| `finger_b_r.stl` | 1 | TPU 95A | 24 x 48 x 8 | 6 | none | Nori-style TPU 95A finger. |

