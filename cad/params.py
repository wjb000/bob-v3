"""Bob v3 parameters. Millimetres, degrees, grams.

Robot frame: ground z = 0, +X forward (nose), +Y left, +Z up.
Origin is on the floor, midway between the two hub-motor centres.
The zero pose is arms hanging straight down, lift at the bottom, head level.

Every printed part must fit BED x BED x BED_Z. That is a 200 mm cube, which
fits a Prusa MK4 (250 x 210), an Ender-3 (220), a Bambu A1/P1/X1 (256) and
a Prusa Core One. export.py fails the build if a part does not fit.

Values marked VERIFY come from datasheets or listings, not from a part on the
bench. Each one only touches a small adapter part, so a wrong guess costs a
reprint of that adapter, not of the robot. See VERIFY.md.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------- printer
BED = 200.0
BED_Z = 200.0
DENSITY = 1.27  # PETG g/cm^3
FILL = 0.55  # effective solid fraction at 4 walls, 20% gyroid. Used for mass.

# ---------------------------------------------------------------- fasteners
M3 = 3.4  # clearance
M3_HEAD = 6.2  # socket head counterbore
M3_INSERT = 4.0  # hole for an M3 x 5.7 heat-set insert
M3_INSERT_DEPTH = 6.5
NUT_AF = 5.9  # M3 nut pocket across flats (nut is 5.5)
NUT_T = 2.8
M5 = 5.5
M5_NUT_AF = 8.4
M8 = 8.4

# ---------------------------------------------------------------- bought parts
# Hoverboard 6.5 in hub motor (the Bob v2 wheels). MEASURE before printing axle clamps.
# Waveshare DDSM115 direct-drive hub motor, dimensions from Waveshare's STEP model:
# tire 100.7 x 43, hub 67, stationary stub 19 mm with 3 x M2.5 on a 15.2 circle, 65.5 mm overall.
WHEEL_OD = 100.7
WHEEL_W = 43.0
AXLE_D = 12.0  # VERIFY: most 6.5 in hubs are 12 mm with two flats
AXLE_FLATS = 10.0  # VERIFY: across the flats
HUB_MASS = 765.0
DDSM_STUB_D = 19.0
DDSM_PCD = 15.2
DDSM_STUB_END = 36.5  # stub end face, inboard of the tire centre
DDSM_ROTOR_IN = 21.5  # rotating hub starts this far inboard of the tire centre

# Damiao DM-J4340-2EC (24 V, 40:1, CAN). 9 N·m rated, 27 N·m peak, 362 g.
DM4340_D = 57.0
DM4340_H = 53.3
DM4340_MASS = 362.0
DM4340_TAU_RATED = 9.0
DM4340_TAU_PEAK = 27.0
# Damiao DM-J4310-2EC V1.1 (24 V, 10:1, CAN). 3 N·m rated, 7 N·m peak, 300 g.
DM4310_D = 56.0
DM4310_H = 46.0
DM4310_MASS = 300.0
DM4310_TAU_RATED = 3.0
DM4310_TAU_PEAK = 7.0
# Output flange and rear face bolt patterns. VERIFY against the Damiao drawing.
# Only the hub adapters and the motor cups carry these holes.
DM_OUT_D = 44.0  # rotating output disc diameter
DM_OUT_PCD = 32.0  # VERIFY
DM_OUT_N = 6  # VERIFY
DM_REAR_PCD = 44.0  # VERIFY
DM_REAR_N = 4  # VERIFY

# Feetech STS3215 C018 (12 V, 1/345). 45.2 x 24.7 x 35 mm, 55 g, 30 kg·cm stall.
STS_L = 45.2
STS_W = 24.7
STS_H = 35.0
STS_SHAFT_FROM_END = 11.5  # shaft centre from the near end along L. VERIFY
STS_HORN_D = 22.0  # VERIFY with the horn in the box
STS_HORN_PCD = 14.0  # VERIFY
STS_HOLE_L = 51.0  # tab hole spacing along L. VERIFY
STS_HOLE_W = 10.0  # tab hole spacing across W. VERIFY
STS_MASS = 55.0
STS_TAU_STALL = 2.94  # N·m at 12 V
STS_TAU_RATED = 0.98
# Feetech STS3250 C001: same 45 x 25 x 35 case as the 3215, 75 g, 50 kg·cm stall.
STS3250_MASS = 75.0
STS3250_TAU_STALL = 4.9
STS3250_TAU_RATED = 1.57
# Feetech STS3095 C002 (12 V). A=30 B=65 C=48 mm, 194.5 g, 15T dual shaft OD 7.6.
# Nori A3 uses this grade on the gravity joints. VERIFY holes and shaft-from-end
# on the part; only the printed cups reprint if a number is wrong.
STS3095_L = 65.0
STS3095_W = 30.0
STS3095_H = 48.0
STS3095_SHAFT_FROM_END = 16.5  # VERIFY
STS3095_HORN_D = 24.0  # VERIFY with the 15T horn in the box
STS3095_HORN_PCD = 18.0  # VERIFY, 4 x M3
STS3095_SPLINE_D = 7.6
STS3095_HOLE_L = 56.0  # tab hole spacing along L. VERIFY
STS3095_HOLE_W = 20.0  # across W. VERIFY
STS3095_MASS = 194.5
STS3095_TAU_STALL = 9.32  # 95 kg·cm
STS3095_TAU_RATED = 2.21  # 22.5 kg·cm

# NEMA 17 48 mm in the base, turning a TR8×2 that drives the middle stage.
NEMA_SIZE = 42.3
NEMA_LEN = 48.0
NEMA_BOLT = 31.0
NEMA_PILOT = 22.2
NEMA_MASS = 360.0
NEMA_HOLD = 0.55  # N·m holding torque, 17HS19-2004S1
T8_FLANGE = 22.0
T8_PCD = 16.0
T8_LEAD = 2.0
T8_D = 8.0

# Electronics envelopes (bought). MEASURE the battery.
BATT = (80.0, 200.0, 70.0)  # x, y, z. The 36 V 10S2P hoverboard pack Bob v2 already has. MEASURE yours.
BATT_MASS = 1200.0
JETSON = (103.0, 90.5, 34.8)  # Jetson Orin Nano Super dev kit with heatsink
D435 = (90.0, 25.0, 25.0)  # Intel RealSense D435i
EYE_PCB = 39.0  # GC9A01 1.28 in round TFT module
EYE_GLASS = 32.4
LIDAR_D = 55.6  # Slamtec RPLIDAR C1
LIDAR_H = 41.3
ESTOP_HOLE = 22.5  # 22 mm panel e-stop
CHARGE_XY = (125.0, -110.0)  # GX16 on the base top, front-right, where the right hand reaches
CHARGE_HOLE = 20.0  # clears the GX16 nut (19 mm); the 21 mm flange stays on the skin

# ---------------------------------------------------------------- base
# Rounded rectangle, 440 long x 360 wide, no steel ballast. The width is set by
# the DDSM115 tires tucked in to y = ±150 under the raised battery.
# Without steel, the arms reaching forward are what tips it, so the base is not
# centred on the axle: the front caster sits 192 mm ahead of the axle and the
# rear one 132 mm behind it (as close as the cable trough lets it), and the shell
# centre is 30 mm ahead of the axle. In MuJoCo the front caster has to touch down
# at least 180 mm ahead of the axle before a straight-arm hold with 0.5 kg per
# hand at the top of the lift stops tipping it (sim/check.py hold and tip).
BASE_L = 440.0
BASE_W = 360.0
BASE_CX = 30.0  # shell centre, ahead of the wheel axis
BASE_R = 90.0  # corner radius, not a plan radius
BASE_TOP = 212.0  # top surface of the shell
BASE_WALL = 3.0
SHELL_BOTTOM = 30.0
GRID_X = (-90.0, 90.0)  # tile cuts, clear of the column well (x = ±50). Mid tile is 180 mm.
GRID_Y = (-98.5, 98.5)  # between the two rows of wheel-bracket bolts, so each bracket also ties the side tile to the middle one

PAN_INSET = 8.0  # pan outline sits this far inside the shell
PAN_BOTTOM = 22.0  # rib bottoms (ground clearance)
PAN_TOP = 37.0
PAN_SKIN = 4.0

WHEEL_Y = 150.0  # wheel centre, each side. Tires sit just inside the flat side of the shell, under the battery.
AXLE_Z = WHEEL_OD / 2.0
WHEEL_ARCH_R = 60.0
WHEEL_CUT_X = 58.0  # pan cutout half-length around the tire
WHEEL_CUT_Y = WHEEL_Y - 24.0  # pan cutout starts here, outboard of the axle bolts
CASTER_XF = 192.0  # front caster swivel, on the front flat
CASTER_XR = 132.0  # rear caster swivel, behind the cable trough
CASTER_WHEEL = 40.0
CASTER_WHEEL_W = 22.0
CASTER_TRAIL = 12.0
CASTER_HOLE = 84.0  # pan cutout the fork swings in
CASTER_PLATE_Z = 56.0  # bottom of the swivel bridge plate

LIDAR_X = CASTER_XF  # on the front caster bridge
LIDAR_Z0 = 108.0  # bottom of the lidar
LIDAR_SCAN_Z = 134.0  # optical plane, roughly

# ---------------------------------------------------------------- telescoping column (Nori A3 / Sunday Memo style)
# Four nested rounded-square tubes. Outer is bolted to the pan. A NEMA 17 in
# the base turns a short TR8×2 that drives the middle tube (1×). A GT2 cascade
# on the middle tube drives the upper tube at 2×, and a second cascade on the
# upper tube drives the inner tube at 3×. Collapsed, the torso still sits 40 mm
# above the base so the hands reach the floor. A 2:1 stack cannot do both.
COL_X = 0.0  # under the torso, on the wheel axis
COL_WALL = 4.0
COL_PAD = 2.0  # slide pad thickness in the gap between tubes (5 mm gap, pads on both sides)
COL_OUTER_D = 100.0  # rounded-square outside. Do not grow this: the torso void and the base well are sized to it.
COL_OUTER_R = 32.0
COL_MID_D = 82.0
COL_MID_R = 24.0
COL_UPPER_D = 64.0
COL_UPPER_R = 16.0
COL_INNER_D = 46.0  # bore about 38 mm, enough for the umbilical sleeve
COL_INNER_R = 10.0
COL_Z0 = PAN_TOP  # outer sits on the pan
COL_MID_Z0 = COL_Z0 + 8.0  # middle tube sits on the motor pedestal, not on the pan
COL_UPPER_Z0 = 146.0  # above the T8 nut bridge (bridge top is NUT_Z + 8)
COL_INNER_Z0 = 150.0
COL_OUTER_LEN = 382.0  # 2 × 191 mm prints
COL_MID_LEN = 376.0  # 2 × 188 mm. Top stays under the cap.
COL_UPPER_LEN = 278.0  # 2 × 139 mm
COL_INNER_LEN = 280.0  # 2 × 140 mm. Cap underside stays at 430 so the shoulder does not rise.
STAGE_TRAVEL = 186.0  # middle tube. Upper travels 2×, inner travels 3×.
LIFT_TRAVEL = 3 * STAGE_TRAVEL  # 558 mm, 22.0 in
COL_OVERLAP = 80.0  # minimum tube engagement at full stretch, every stage

# Motor stands on the pan inside the outer tube, shaft up.
NEMA_PEDESTAL = 8.0
NEMA_FACE_Z = COL_Z0 + NEMA_PEDESTAL + NEMA_LEN  # 93 mm, shaft points +z
COUPLER_H = 25.0
SCREW_X = COL_X
SCREW_Z0 = NEMA_FACE_Z + 2.0
SCREW_LEN = STAGE_TRAVEL + 80.0  # 266 mm, cut from a 500 mm TR8×2
NUT_Z = 130.0  # on the middle tube. Bridge is 124–138, clear of the coupler and below the upper tube.

SHOULDER_Z0 = COL_INNER_Z0 + COL_INNER_LEN + 22.0  # 452 mm. Do not raise this or the hands miss the floor.
COL_TOP0 = COL_Z0 + COL_OUTER_LEN  # outer top at lift = 0
COL_INNER_TOP0 = COL_INNER_Z0 + COL_INNER_LEN

# Viewer / leftover aliases. The old mast is gone; these keep base.py hole math
# and the "Mast" layer name working.
MAST_X = COL_X
MAST_DX = COL_OUTER_D
MAST_DY = COL_OUTER_D
MAST_R = COL_OUTER_R
MAST_WALL = COL_WALL
MAST_Z0 = COL_Z0
MAST_TOP = COL_TOP0

# ---------------------------------------------------------------- torso (relative to the shoulder axis in z)
# The column comes up through the bottom of the torso. The torso sits on the
# inner-tube cap. It does not hang off a lip in front of the column.
TORSO_X0 = COL_X - 150.0 / 2.0  # back face; depth is centred on the column
TORSO_D = 150.0
TORSO_HW = 120.0  # half width
TORSO_BELOW = 200.0
TORSO_ABOVE = 50.0
TORSO_SPLIT = -80.0  # upper / lower tier
TORSO_R = 32.0
TORSO_WALL = 3.0
SHOULDER_X = TORSO_X0 + 84.0
SHOULDER_Y = 157.0  # J2/J3 axis line, each side
CAP_BOLT = 22.0  # M5 square that holds the torso shelf down on the cap

# ---------------------------------------------------------------- arm (left; right mirrors y)
UPPER_ARM = 252.0  # shoulder axis to elbow axis
FOREARM = 200.0  # elbow axis to wrist-pitch axis
HAND = 196.0  # wrist-pitch axis to fingertip (arm.py derives the exact value from the gripper stack)
J1_FACE_Y = TORSO_HW - 3.0  # DM4340 output face
J3_FACE = -113.0  # J3 module output face, relative to the shoulder axis
ARM_TUBE_D = 64.0
FOREARM_TUBE_D = 52.0
GRIP_OPEN = 80.0  # max jaw gap

# ---------------------------------------------------------------- head (relative to the shoulder axis in z)
NECK_Z = TORSO_ABOVE
TILT_Z = 100.0
HEAD_W = 176.0
HEAD_D = 120.0
HEAD_H = 144.0
HEAD_CZ = 168.0
HEAD_CX = SHOULDER_X + 18.0  # head centre, ahead of the neck
NECK_X = SHOULDER_X - 4.0  # pan axis

# ---------------------------------------------------------------- joints, rad (lift in m)
LIMITS = {
    "lift": (0.0, LIFT_TRAVEL / 1000.0),
    "head_pan": (-0.8, 0.8),  # column is under the torso, so the head no longer hits a mast
    "head_tilt": (-0.45, 0.55),  # positive looks down; the chin meets the torso top past 0.55
    "shoulder_pitch": (-3.1, 1.0),  # negative swings the arm forward and up
    "shoulder_roll": (-0.20, 1.75),  # positive raises the arm out to the side
    "upper_arm_yaw": (-1.6, 1.6),
    "elbow": (-2.35, 0.0),  # negative bends the forearm forward
    "wrist_pitch": (-2.3, 2.3),  # the J6 sleeve clears the forearm tube to about 2.4 rad
    "wrist_roll": (-2.8, 2.8),
    "gripper": (0.0, 0.040),  # metres per finger, 0 = closed
}


def shoulder_z(lift_mm: float = 0.0) -> float:
    return SHOULDER_Z0 + lift_mm


def col_segments(z0: float, length: float) -> list[tuple[float, float]]:
    """Stack of prints for one tube. No piece taller than the bed."""
    n = max(1, math.ceil(length / (BED_Z - 4.0)))
    step = length / n
    return [(z0 + i * step, z0 + (i + 1) * step) for i in range(n)]


def check() -> None:
    errs = []
    gaps = {
        "outer/mid": (COL_OUTER_D - 2 * COL_WALL - COL_MID_D) / 2,
        "mid/upper": (COL_MID_D - 2 * COL_WALL - COL_UPPER_D) / 2,
        "upper/inner": (COL_UPPER_D - 2 * COL_WALL - COL_INNER_D) / 2,
    }
    for name, gap in gaps.items():
        if gap < COL_PAD + 1.0:
            errs.append(f"{name} pad gap {gap:.1f} mm")
    if abs(COL_MID_Z0 - (NEMA_FACE_Z - NEMA_LEN)) > 0.1:
        errs.append("middle tube does not sit on the motor pedestal")
    if NEMA_SIZE + 8 > COL_OUTER_D - 2 * COL_WALL:
        errs.append("NEMA 17 does not fit inside the outer tube")
    if NUT_Z < SCREW_Z0 + 10:
        errs.append("T8 nut sits on the coupler")
    if NUT_Z + STAGE_TRAVEL > SCREW_Z0 + SCREW_LEN - 20:
        errs.append("T8 nut runs off the screw at the top")
    if COL_UPPER_Z0 < NUT_Z + 10:
        errs.append("upper tube hits the nut bridge")
    if COL_INNER_Z0 < COL_UPPER_Z0:
        errs.append("inner tube starts below the upper tube")
    if COL_MID_Z0 + COL_MID_LEN > COL_INNER_TOP0 - 6:
        errs.append("middle tube hits the cap at lift = 0")
    if COL_UPPER_Z0 + COL_UPPER_LEN > COL_INNER_TOP0 - 4:
        errs.append("upper tube hits the cap at lift = 0")
    # At full stretch, how much of the inner member is still inside the one outside it.
    pairs = (
        ("outer/mid", (COL_Z0 + COL_OUTER_LEN) - (COL_MID_Z0 + STAGE_TRAVEL)),
        ("mid/upper", (COL_MID_Z0 + COL_MID_LEN + STAGE_TRAVEL) - (COL_UPPER_Z0 + 2 * STAGE_TRAVEL)),
        ("upper/inner", (COL_UPPER_Z0 + COL_UPPER_LEN + 2 * STAGE_TRAVEL) - (COL_INNER_Z0 + LIFT_TRAVEL)),
    )
    for name, overlap in pairs:
        if overlap < COL_OVERLAP:
            errs.append(f"{name} overlap at full stretch is {overlap:.0f} mm")
    if SHOULDER_Z0 - TORSO_BELOW < BASE_TOP + 40:
        errs.append("torso hits the base at the bottom of travel")
    if WHEEL_Y + WHEEL_W / 2 > BASE_W / 2 - 4:
        errs.append("tire rubs the shell")
    if CASTER_XF + CASTER_HOLE / 2 + 8 > BASE_CX + BASE_L / 2 - PAN_INSET:
        errs.append("front caster hole breaks the pan rim")
    if CASTER_XR + CASTER_HOLE / 2 + 8 > BASE_L / 2 - BASE_CX - PAN_INSET:
        errs.append("rear caster hole breaks the pan rim")
    if min(CASTER_XF, CASTER_XR) - CASTER_HOLE / 2 < COL_OUTER_D / 2 + 16:
        errs.append("caster hole meets the column foot")
    if BASE_R > min(BASE_L, BASE_W) / 2:
        errs.append("corner radius larger than the base")
    spans = (
        col_segments(COL_Z0, COL_OUTER_LEN)
        + col_segments(COL_MID_Z0, COL_MID_LEN)
        + col_segments(COL_UPPER_Z0, COL_UPPER_LEN)
        + col_segments(COL_INNER_Z0, COL_INNER_LEN)
    )
    for z0, z1 in spans:
        if z1 - z0 > BED_Z:
            errs.append("column segment too tall")
    tx1 = TORSO_X0 + TORSO_D
    if TORSO_X0 + 8 >= COL_X - COL_OUTER_D / 2 or COL_X + COL_OUTER_D / 2 >= tx1 - 8:
        errs.append("column is not inside the torso")
    if COL_INNER_TOP0 + 12 > SHOULDER_Z0 + TORSO_ABOVE:
        errs.append("column cap comes out the top of the torso")
    if errs:
        raise ValueError("; ".join(errs))


check()
