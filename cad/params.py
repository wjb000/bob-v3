"""Bob v3 chassis parameters. Millimetres.

Frame: ground is z = 0, +X is the nose, +Y is left, origin is the deck centre.
Edit this file and rerun export.py. Do not copy SO-101 link meshes into this repo.

Measured from the upstream files (TheRobotStudio/SO-ARM100, Nov 2026):
  Base_SO101.stl bbox 110.93 x 72.0 x 87.0 mm, bottom face has no bolt circle
  we could lock down. The foot is the wide part, about 16 mm tall, then a
  narrower servo tower. The arm is clamped by straps, not by invented holes.
  Seeed mounting plate holes (not used here): Ø3.6 on a 16.5 x 21.0 mm
  rectangle. WaveShare plate: Ø5.0 on (±18.5, ±14.0).

Not measured on the real Bob, so they stay parameters:
  WHEEL_OD, AXLE_D, WHEEL_WIDTH, and the T8 nut pocket.
"""

from __future__ import annotations

import math

# --- deck ---
# 320 x 340. The SO-101 gripper origin reaches about 404 mm forward of the
# arm plate. On the 480 mm deck the plate sat 304 mm behind the nose, so the
# hand cleared the bumper by about 100 mm and could not put 150 mm of reach
# on a counter or on the floor in front. Two 160 mm tiles keep the tower on
# the rear tile and the plate 144 mm behind the nose. Width stays 340 mm:
# the hubs hang outside that, and the whole base still fits a doorway.
DECK_L = 320.0
DECK_W = 340.0
NX = 2
NY = 2
CELL_X = DECK_L / NX  # 160
CELL_Y = DECK_W / NY  # 170
GAP = 0.40  # saw-fit gap between tiles

SKIN = 2.6
RIB_H = 10.0
RIB_T = 3.4
GROUND_CLEAR = 22.0  # underside of the ribs
DECK_TOP = GROUND_CLEAR + RIB_H + SKIN  # 34.6
BOSS_EXTRA = 6.0
BOSS_D = 16.0

# A 220 mm bed. 208 leaves a brim.
BED = 208.0
SEG_Z_MAX = 175.0

# --- fasteners ---
M3 = 3.4
M3_CLOSE = 3.2
NUT_AF = 5.5  # M3 hex nut across flats
NUT_T = 2.4
NUT_POCKET_AF = 5.9
NUT_POCKET_T = 2.7
M25 = 2.9  # M2.5 clearance
M25_NUT_AF = 5.2
M25_NUT_T = 2.2

# --- wheels, unmeasured ---
WHEEL_OD = 165.0  # MEASURE the hub tire
AXLE_Z = WHEEL_OD / 2.0  # assumes the tire sits on the ground
AXLE_D = 8.5  # MEASURE. 8.5 is an M8 clearance; drill to the real axle
WHEEL_WIDTH = 45.0  # MEASURE
POD_T = 6.0

# --- lift ---
# 700 mm so the hand can work a counter. The base has no tray and no vac,
# so the arm is the only way up there. 500 mm leaves the shoulder near 570.
ROD_LEN = 700.0
ROD_D = 8.0
ROD_HOLE = 8.4
ROD_PITCH = 70.0
ROD_X = -6.0  # rod/screw x relative to the tower centre
TW = 140.0  # tower outer width (Y)
TD = 80.0  # tower outer depth (X)
WALL = 3.6
TOWER_COL = 0  # rear tile
TOWER_X = -DECK_L / 2 + (TOWER_COL + 0.5) * CELL_X  # -160
TOWER_Y = 0.0
# Nose tile, right side. The tray is 140 x 104 and sits inside the 160 mm tile.
ELEC_X = -DECK_L / 2 + ((NX - 1) + 0.5) * CELL_X  # 160
ELEC_Y = -90.0
# Just behind the nose, left of centre, clear of the caster bolts.
CAM_X = DECK_L / 2 - 54.0  # 186
CAM_Y = 55.0
CASTER_BOLT_X = DECK_L / 2 - 22.0  # 218
BOTTOM_H = 172.0

MOTOR_SIZE = 42.3
MOTOR_BOLT = 31.0  # NEMA 17 hole square
MOTOR_PILOT = 22.2
MOTOR_LEN = 40.0
# Face points up. Body hangs through a deck window. Bottom of the body is 12 mm up.
MOTOR_FACE_Z = MOTOR_LEN + 12.0
COUPLER_LEN = 20.0
COUPLER_OD = 20.0

# Round-flange brass TR8 nut is Ø22 x ~15, 4x M3 on a 16 mm circle.
# A 22 mm square flange also drops into this pocket. Measure before printing
# the carriage; it is the one part the nut depends on.
T8_POCKET = 24.0
T8_POCKET_D = 4.5
T8_HOLE = 12.0  # screw clearance through the carriage
T8_PCD = 16.0
T8_LEAD = 2.0  # buy TR8x2 (2 mm lead). TR8x8 creeps down under the arm.
SW_PITCH = 9.5

BEARING_OD = 15.0  # LM8UU
BEARING_LEN = 24.0
BEARING_BORE = 15.6
BEARING_SPAN = 46.0  # lower-centre to upper-centre
HOUSING = 32.0

SHOULDER_ABOVE_PLATE = 62.4  # SO-101 MJCF shoulder z, metres -> mm
CARRIAGE_ABOVE_LOWER = 36.0  # lower bearing centre to the top of the arm plate
PLATE_T = 4.0
PLATE_L = 172.0
PLATE_W = 120.0
PLATE_DX = 96.0  # arm-plate centre, forward of the tower centre. Clears the rods.

STRAP_Y = 34.0
STRAP_W = 12.0
STRAP_LEN = 156.0
STRAP_CLEAR = 16.2  # underside of the strap above the plate
STRAP_T = 4.0

# Printed nose/tail roller. It lives ahead of the deck so it can touch the floor.
CASTER_ROLLER_OD = 30.0
CASTER_ROLLER_W = 14.0
CASTER_AXLE_Z = CASTER_ROLLER_OD / 2.0

# --- derived, do not edit ---
ROD_Z0 = DECK_TOP + 4.0
ROD_Z1 = DECK_TOP + ROD_LEN - 12.0
LOWER_BEARING_MIN = MOTOR_FACE_Z + COUPLER_LEN + 16.0
# 20 mm keeps the upper LM8UU and its housing on the rod at full height.
LOWER_BEARING_MAX = ROD_Z1 - 20.0 - BEARING_SPAN
PLATE_TOP_LO = LOWER_BEARING_MIN + CARRIAGE_ABOVE_LOWER
PLATE_TOP_HI = LOWER_BEARING_MAX + CARRIAGE_ABOVE_LOWER
SHOULDER_LO = PLATE_TOP_LO + SHOULDER_ABOVE_PLATE
SHOULDER_HI = PLATE_TOP_HI + SHOULDER_ABOVE_PLATE
TRAVEL = LOWER_BEARING_MAX - LOWER_BEARING_MIN

M3_NUT_AF_POCKET = NUT_POCKET_AF
JOINT_OFF = 8.0  # splice bolt, each side of a tile joint


def segment_heights() -> list[float]:
    """Stack that sums to ROD_LEN. No piece taller than SEG_Z_MAX."""
    rest = ROD_LEN - BOTTOM_H
    if rest <= 0:
        raise ValueError("ROD_LEN shorter than the motor segment")
    n = max(1, math.ceil(rest / SEG_Z_MAX))
    step = rest / n
    return [BOTTOM_H] + [step] * n


def segment_zs() -> list[tuple[float, float]]:
    z = DECK_TOP
    out = []
    for h in segment_heights():
        out.append((z, z + h))
        z += h
    return out


def plate_center() -> tuple[float, float]:
    return (TOWER_X + PLATE_DX, TOWER_Y)


def check() -> None:
    motor = MOTOR_SIZE
    gap = ROD_PITCH / 2 - ROD_D / 2 - motor / 2
    if gap < 4:
        raise ValueError(f"rods collide with the NEMA 17 (gap {gap:.1f} mm)")
    inner_y = TW / 2 - WALL
    if ROD_PITCH / 2 + HOUSING / 2 + 2 > inner_y:
        raise ValueError("bearing housing hits the tower wall")
    back = -TD / 2 + WALL
    if ROD_X - motor / 2 < back + 3:
        raise ValueError("motor hits the back wall")
    if LOWER_BEARING_MAX <= LOWER_BEARING_MIN + 50:
        raise ValueError("lift travel collapsed; check ROD_LEN and the coupler")
    heights = segment_heights()
    if abs(sum(heights) - ROD_LEN) > 0.1:
        raise ValueError("segment stack does not match ROD_LEN")
    if max(heights) > SEG_Z_MAX + 0.1:
        raise ValueError("a tower segment is taller than the print limit")
    if CELL_X > BED or CELL_Y > BED:
        raise ValueError("a deck tile does not fit the bed")


check()
