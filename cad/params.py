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
WHEEL_OD = 165.0  # MEASURE tire
WHEEL_W = 45.0  # MEASURE hub width
AXLE_D = 12.0  # VERIFY: most 6.5 in hubs are 12 mm with two flats
AXLE_FLATS = 10.0  # VERIFY: across the flats
HUB_MASS = 2800.0

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
STS_MASS = 55.0
STS_TAU_STALL = 2.94  # N·m at 12 V
STS_TAU_RATED = 0.98

# NEMA 17 48 mm for the lift. TR8x2 leadscrew 900 mm. 12 mm rods 1000 mm, LM12UU.
NEMA_SIZE = 42.3
NEMA_LEN = 48.0
NEMA_BOLT = 31.0
NEMA_PILOT = 22.2
NEMA_MASS = 360.0
NEMA_HOLD = 0.55  # N·m holding torque, 17HS19-2004S1
ROD_D = 12.0
ROD_HOLE = 12.3
LM12_OD = 21.0
LM12_LEN = 30.0
T8_FLANGE = 22.0
T8_PCD = 16.0
T8_LEAD = 2.0

# Electronics envelopes (bought). MEASURE the battery.
BATT = (80.0, 200.0, 70.0)  # x, y, z. 36 V 10S2P hoverboard pack
BATT_MASS = 1200.0
JETSON = (103.0, 90.5, 34.8)  # Jetson Orin Nano Super dev kit with heatsink
D435 = (90.0, 25.0, 25.0)  # Intel RealSense D435i
EYE_PCB = 39.0  # GC9A01 1.28 in round TFT module
EYE_GLASS = 32.4
LIDAR_D = 55.6  # Slamtec RPLIDAR C1
LIDAR_H = 41.3
ESTOP_HOLE = 22.5  # 22 mm panel e-stop

# ---------------------------------------------------------------- base
BASE_L = 560.0  # x. 560 puts the front caster far enough out for 10+ degrees of forward tip margin.
BASE_W = 440.0  # y
BASE_R = 140.0  # plan corner radius
BASE_TOP = 238.0  # top surface of the shell
BASE_WALL = 3.0
SHELL_BOTTOM = 42.0
GRID_X = (-100.0, 87.0)  # tile cut lines, shell and pan. Clear of the mast hole.
GRID_Y = (-90.0, 90.0)

PAN_INSET = 8.0  # pan outline sits this far inside the shell
PAN_BOTTOM = 34.0  # rib bottoms (ground clearance)
PAN_TOP = 49.0
PAN_SKIN = 4.0

WHEEL_Y = 185.0  # wheel centre, each side
AXLE_Z = WHEEL_OD / 2.0
WHEEL_ARCH_R = 96.0
WHEEL_CUT_X = 96.0  # pan cutout half-length around the tire
WHEEL_CUT_Y = 156.0  # pan cutout starts here
CASTER_X = 215.0  # front and rear
CASTER_WHEEL = 50.0
CASTER_WHEEL_W = 22.0
CASTER_TRAIL = 15.0
CASTER_HOLE = 100.0  # pan cutout the fork swings in
CASTER_PLATE_Z = 66.0  # bottom of the swivel bridge plate

LIDAR_X = 215.0  # on the front caster bridge
LIDAR_Z0 = 108.0  # bottom of the lidar
LIDAR_SCAN_Z = 134.0  # optical plane, roughly

# ---------------------------------------------------------------- mast / lift
MAST_X = -30.0  # mast centre
MAST_DX = 100.0  # depth (x)
MAST_DY = 132.0  # width (y)
MAST_R = 30.0
MAST_WALL = 4.0
MAST_SLOT = 64.0  # front slot width the carriage tongue rides in
ROD_X = MAST_X - 12.0
ROD_Y = 45.0
SCREW_X = ROD_X
MAST_Z0 = PAN_TOP
MAST_TOP = 1035.0  # top of the segment stack, bottom of the cap
CAP_H = 92.0
ROD_Z0 = MAST_Z0 + 6.0
ROD_LEN = 1000.0
SCREW_LEN = 900.0
SCREW_Z1 = 1060.0  # top end of the screw, inside the coupler
NEMA_FACE_Z = 1070.0  # motor face, pointing down, body above

LIFT_TRAVEL = 650.0
SHOULDER_Z0 = 520.0  # shoulder axis at lift = 0
CARRIAGE_BELOW = 300.0  # carriage bottom, below the shoulder axis
CARRIAGE_H = 150.0
BEARING_SPAN = 110.0  # lower to upper LM12UU centres

# ---------------------------------------------------------------- torso (relative to the shoulder axis in z)
TORSO_X0 = MAST_X + MAST_DX / 2 + 6.0  # back face, 6 mm in front of the mast
TORSO_D = 170.0
TORSO_HW = 155.0  # half width
TORSO_BELOW = 230.0
TORSO_ABOVE = 50.0
TORSO_SPLIT = -80.0  # upper / lower tier
TORSO_R = 48.0
TORSO_WALL = 3.0
SHOULDER_X = TORSO_X0 + 84.0
SHOULDER_Y = 195.0  # J2/J3 axis line, each side

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
HEAD_W = 196.0
HEAD_D = 120.0
HEAD_H = 144.0
HEAD_CZ = 168.0
HEAD_CX = SHOULDER_X + 18.0  # head centre, ahead of the neck so it clears the mast
NECK_X = SHOULDER_X - 4.0  # pan axis

# ---------------------------------------------------------------- joints, rad (lift in m)
LIMITS = {
    "lift": (0.0, LIFT_TRAVEL / 1000.0),
    "head_pan": (-0.6, 0.6),  # below 0.51 m of lift, wider and the head's back corners reach the mast
    "head_tilt": (-0.35, 0.55),  # positive looks down; the chin meets the torso top past 0.55, the back meets the mast past -0.35
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


def mast_segments() -> list[tuple[float, float]]:
    """Segment z ranges from the pan to the cap. No piece taller than the bed."""
    h = MAST_TOP - MAST_Z0
    n = math.ceil(h / (BED_Z - 20.0))
    step = h / n
    return [(MAST_Z0 + i * step, MAST_Z0 + (i + 1) * step) for i in range(n)]


def check() -> None:
    errs = []
    if ROD_Y - ROD_D / 2 - NEMA_SIZE / 2 < 3:
        errs.append("rods hit the NEMA 17")
    if ROD_Y + LM12_OD / 2 + 5 > MAST_DY / 2 - MAST_WALL:
        errs.append("bearing housings hit the mast wall")
    car_top_max = SHOULDER_Z0 + LIFT_TRAVEL - CARRIAGE_BELOW + CARRIAGE_H
    if car_top_max > MAST_TOP - 10:
        errs.append(f"carriage top {car_top_max} runs into the cap")
    if SHOULDER_Z0 - CARRIAGE_BELOW < SCREW_Z1 - SCREW_LEN + 30:
        errs.append("carriage nut runs off the bottom of the screw")
    if SHOULDER_Z0 - TORSO_BELOW < BASE_TOP + 40:
        errs.append("torso hits the base at the bottom of travel")
    if ROD_Z0 + ROD_LEN > MAST_TOP + CAP_H - 20:
        errs.append("rods poke through the cap")
    if WHEEL_Y + WHEEL_W / 2 > BASE_W / 2 - 4:
        errs.append("tire rubs the shell")
    if any(b - a > BED_Z for a, b in mast_segments()):
        errs.append("mast segment too tall")
    if errs:
        raise ValueError("; ".join(errs))


check()
