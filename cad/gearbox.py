"""GM-5: Bob's printed joint module. A Feetech STS3250 drives a 5:1 planetary.

Local frame (the same as the Damiao model it replaces): +z is the output, the output face is z = 0,
the output disc is z 0..2 with the Damiao bolt circle, so every link downstream is unchanged.

  sun 12 T, three planets 18 T, ring 48 T cut into the housing, module 1.0, 5:1
  carrier: front plate + hub in a 6807 bearing (35 x 47 x 7), back plate, M3 x 20 planet pins
  housing: front flange that screws to the parent cup's rim, bearing seat, ring gear, rear wall, servo sleeve
  cap: closes the sleeve behind the servo
  homing: a 3 x 2 mm magnet in the carrier rim passes a hall sensor in the housing wall

The servo's own encoder repeats every 72 degrees of output, so each joint homes to its hall index at
power-up and then runs the servo in multi-turn mode.

Output: about 21 N·m peak (STS3250 4.9 N·m stall x 5 x 0.85) and about 6.7 N·m rated, 90 deg/s.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import box, cut, cyl, fuse, tube_between

M = 1.0
ZS, ZP, ZR = 12, 18, 48
RATIO = 1 + ZR / ZS
R_S, R_P, R_R = M * ZS / 2, M * ZP / 2, M * ZR / 2
CD = R_S + R_P  # planet centre distance, 15
D = 57.0  # housing diameter, fits the old Damiao cups
FLANGE_D = 66.0
FLANGE_PCD = 61.0
BEARING = (35.0, 47.0, 7.0)  # 6807
Z_FACE = -0.5  # housing front face
Z_FLANGE = (-3.5, -0.5)
Z_BRG = (-8.0, -1.0)
Z_GEAR = (-25.0, -11.2)
Z_RING = (-26.0, -10.5)
Z_REAR = (-35.5, -28.3)  # rear wall + flange
Z_SERVO = (-71.0, -36.0)  # servo body, shaft up at the axis
Z_SLEEVE = (-71.5, -35.5)
Z_CAP = (-74.5, -71.5)
LENGTH = -Z_CAP[0] + 2.0
SX = P.STS_SHAFT_FROM_END
SERVO_X = (-SX, P.STS_L - SX)
SERVO_Y = P.STS_W / 2

STS3250_MASS = 75.0
STS3250_STALL = 4.9  # N·m at 12 V
STS3250_RATED = 1.57
EFF = 0.85
TAU_PEAK = STS3250_STALL * RATIO * EFF
TAU_RATED = STS3250_RATED * RATIO * EFF
SPEED = (2 * math.pi * 75 / 60) / RATIO  # rad/s at no load


def _teeth(n, r_pitch, r_tip, r_root, z0, z1, backlash=0.15, phase=0.0):
    """Trapezoid-tooth gear outline (20 degree flanks), extruded z0..z1."""
    s_p = math.pi * M / 2 - backlash
    t20 = math.tan(math.radians(20))
    w_tip = max(s_p - 2 * (r_tip - r_pitch) * t20, 0.35)
    w_root = s_p + 2 * (r_pitch - r_root) * t20
    pts = []
    for i in range(n):
        c = phase + 2 * math.pi * i / n
        for r, w, sg in ((r_root, w_root, -1), (r_tip, w_tip, -1), (r_tip, w_tip, 1), (r_root, w_root, 1)):
            a = c + sg * (w / 2) / r
            pts.append((r * math.cos(a), r * math.sin(a)))
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0).val()


def housing() -> cq.Shape:
    body = cyl((0, 0, Z_REAR[0]), "z", D, Z_FACE - Z_REAR[0])
    flange = cyl((0, 0, Z_FLANGE[0]), "z", FLANGE_D, Z_FLANGE[1] - Z_FLANGE[0])  # front flange: screws into the parent cup's rim
    from lib import rrect
    sx_c = (SERVO_X[0] + SERVO_X[1]) / 2
    sleeve = rrect(sx_c, 0, Z_SLEEVE[0], Z_REAR[0] + 0.01, SERVO_X[1] - SERVO_X[0] + 6.6, 2 * SERVO_Y + 6.6, 7.0)
    s = fuse(body, flange, sleeve)
    # the ring gear: cut the tooth spaces as if they were teeth of a 48-tooth gear, phased to mesh with the planets
    ring_space = _teeth(ZR, R_R, R_R + 1.25 * M, R_R - M, Z_RING[0], Z_RING[1], backlash=-0.15, phase=math.radians(3.75))
    tools = [
        ring_space,
        cyl((0, 0, Z_RING[0]), "z", 2 * (R_R - M) - 0.2, Z_RING[1] - Z_RING[0]),
        cyl((0, 0, Z_RING[1] - 0.01), "z", 46.0, Z_BRG[0] - 0.5 - Z_RING[1] + 0.02),
        cyl((0, 0, Z_BRG[0] - 0.5), "z", BEARING[1] + 0.15, Z_FACE - Z_BRG[0] + 0.6),
        cyl((0, 0, -31.8), "z", 2 * R_R - 2, Z_RING[0] - (-31.8) + 0.01),  # back plate and the pin heads
        cyl((0, 0, Z_REAR[0] - 1), "z", 24.0, Z_REAR[1] - Z_REAR[0] + 2),  # sun hub and horn
        box(SERVO_X[0] - 0.3, SERVO_X[1] + 0.3, -SERVO_Y - 0.3, SERVO_Y + 0.3, Z_SLEEVE[0] - 1, Z_REAR[0] + 0.01),
        box(SERVO_X[1] - 4, SERVO_X[1] + 4, -6, 6, Z_SLEEVE[0] - 1, Z_SLEEVE[0] + 12),  # servo cable exit
        box(-3.2, 3.2, D / 2 - 6.5, D / 2 - 1.0, -16.0, -10.0),  # hall sensor pocket
    ]
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        x, y = FLANGE_PCD / 2 * math.cos(a), FLANGE_PCD / 2 * math.sin(a)
        tools.append(cyl((x, y, Z_FLANGE[0] - 1), "z", P.M3, 5))
        tools.append(cyl((x, y, Z_FLANGE[1] - 1.6), "z", P.M3_HEAD, 2))
    for x in (SERVO_X[0] - 1.6, SERVO_X[1] + 1.6):  # cap screws, thread-forming into the sleeve wall
        tools.append(cyl((x, 0, Z_SLEEVE[0] - 1), "z", 2.6, 9))
    return cut(s, *tools)


def cap() -> cq.Shape:
    from lib import rrect
    s = rrect((SERVO_X[0] + SERVO_X[1]) / 2, 0, Z_CAP[0], Z_CAP[1], SERVO_X[1] - SERVO_X[0] + 6.6, 2 * SERVO_Y + 6.6, 7.0, chamfer_bot=1.5)
    tools = [cyl((x, 0, Z_CAP[0] - 1), "z", P.M3, 5) for x in (SERVO_X[0] - 1.6, SERVO_X[1] + 1.6)]
    return cut(s, *tools)


def _pin_xy():
    return [(CD * math.cos(a), CD * math.sin(a)) for a in (0, 2 * math.pi / 3, 4 * math.pi / 3)]


def carrier_front() -> cq.Shape:
    disc = cyl((0, 0, 0), "z", P.DM_OUT_D, 2)
    hub = cyl((0, 0, -9.0), "z", BEARING[0] - 0.05, 9.01)
    plate = cyl((0, 0, -11.0), "z", 44.0, 2.01)
    s = fuse(disc, hub, plate)
    tools = [cyl((0, 0, -12), "z", 12, 20)]
    for i in range(P.DM_OUT_N):
        a = 2 * math.pi * i / P.DM_OUT_N
        tools.append(cyl((P.DM_OUT_PCD / 2 * math.cos(a), P.DM_OUT_PCD / 2 * math.sin(a), -6), "z", 2.6, 9))
    for x, y in _pin_xy():
        tools.append(cyl((x, y, -11.5), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 0.5))
    tools.append(cyl((20.0, 0, -11.5), "z", 3.2, 2.2))  # homing magnet
    return cut(s, *tools)


def carrier_back() -> cq.Shape:
    s = cyl((0, 0, -27.5), "z", 44.0, 2.3)
    tools = [cyl((0, 0, -28), "z", 15, 4)]
    for x, y in _pin_xy():
        tools.append(cyl((x, y, -28), "z", P.M3, 4))
    return cut(s, *tools)


def sun() -> cq.Shape:
    g = _teeth(ZS, R_S, R_S + M, R_S - 1.25 * M, Z_GEAR[0], Z_GEAR[1])
    shaft = cyl((0, 0, Z_REAR[1] - 0.2), "z", 12.0, Z_GEAR[0] - Z_REAR[1] + 0.21)
    hub = cyl((0, 0, -32.0), "z", 21.0, 3.5)
    s = fuse(g, shaft, hub)
    tools = [cyl((0, 0, -40), "z", 3.2, 40)]
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        tools.append(cyl((P.STS_HORN_PCD / 2 * math.cos(a), P.STS_HORN_PCD / 2 * math.sin(a), -33), "z", 2.3, 8))
    return cut(s, *tools)


def planet(k: int) -> cq.Shape:
    x, y = _pin_xy()[k]
    g = _teeth(ZP, R_P, R_P + M, R_P - 1.25 * M, Z_GEAR[0] + 0.2, Z_GEAR[1] - 0.2, phase=math.radians(10))
    g = cut(g, cyl((0, 0, Z_GEAR[0]), "z", 3.4, 20))
    return g.translate((x, y, 0))


def printed():
    """(suffix, solid, look, note) for one module, local frame."""
    return [
        ("housing", housing(), "shell", "Ring gear inside. Prints flange-down; PETG-CF or nylon if you have it."),
        ("cap", cap(), "shell", "Closes the servo sleeve."),
        ("carrier", carrier_front(), "dark", "Output: hub runs in the 6807, disc takes the link's 6 x M3."),
        ("carrier_back", carrier_back(), "dark", "Back plate; the three M3 x 20 pins screw through it."),
        ("sun", sun(), "accent", "12 T on the servo horn. 100% infill."),
        ("planet0", planet(0), "accent", "18 T planet. Print 3 per module, 100% infill."),
        ("planet1", planet(1), "accent", ""),
        ("planet2", planet(2), "accent", ""),
    ]


def bought():
    """(suffix, solid, look, kind) for one module, local frame."""
    import vendor as V

    sts = V.sts3215()
    pieces = [(("servo" if not s else f"servo_{s}"), shp.translate((0, 0, Z_SERVO[1])), "alu" if not s else look, "actuator")
              for s, shp, look in sts]
    brg = tube_between("z", (0, 0), Z_BRG[0], Z_BRG[1], BEARING[1], BEARING[0])
    pieces.append(("bearing", brg, "steel", "metal"))
    pins = fuse(*[cyl((x, y, -27.5 - 2.5), "z", 5.5, 2.5).fuse(cyl((x, y, -27.5), "z", 3.0, 17.5)) for x, y in _pin_xy()])
    pieces.append(("pins", pins, "steel", "metal"))
    hall = box(-3, 3, D / 2 - 6, D / 2 - 4.5, -15.5, -10.5)
    pieces.append(("hall", hall, "black", "electronics"))
    return pieces


# ---------------------------------------------------------------- placing modules in the robot

def _placed(shape, origin, zdir, xdir):
    import vendor as V

    return V.place([("", shape, "")], origin, xdir=xdir, zdir=zdir)[0][1]


def mount(origin, zdir, xdir):
    """For the parent link: (cup to fuse, insert holes to cut, keep-out envelope to cut)."""
    cup = tube_between("z", (0, 0), Z_REAR[0], Z_FLANGE[0], FLANGE_D, D + 0.6)
    inserts = []
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        x, y = FLANGE_PCD / 2 * math.cos(a), FLANGE_PCD / 2 * math.sin(a)
        inserts.append(cyl((x, y, Z_FLANGE[0] - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 0.2))
    keep = fuse(
        cyl((0, 0, Z_REAR[0] - 0.5), "z", D + 0.8, -Z_REAR[0] + 1.0),
        cyl((0, 0, Z_FLANGE[0] - 0.3), "z", FLANGE_D + 1.0, 4.3),
        cyl((0, 0, -0.2), "z", P.DM_OUT_D + 2.0, 2.8),
        box(SERVO_X[0] - 4.0, SERVO_X[1] + 4.0, -SERVO_Y - 4.0, SERVO_Y + 4.0, Z_CAP[0] - 0.8, Z_REAR[0] + 0.2),
    )
    return _placed(cup, origin, zdir, xdir), _placed(fuse(*inserts), origin, zdir, xdir), _placed(keep, origin, zdir, xdir)


PRINT_ROT = {"housing": (180, 0, 0), "cap": (0, 0, 0), "carrier": (180, 0, 0), "carrier_back": (0, 0, 0), "sun": (0, 0, 0),
             "planet0": (0, 0, 0), "planet1": (0, 0, 0), "planet2": (0, 0, 0)}
ON_CHILD = {"carrier", "carrier_back", "pins", "planet0", "planet1", "planet2"}  # the planets orbit with the carrier


def instance(prefix, origin, zdir, xdir, parent, child, group):
    """One placed module: (printed Parts, Bought items)."""
    from lib import Bought, Part
    import vendor as V

    parts, buys = [], []
    for sfx, shp, look, note in printed():
        pa = "gm_planet" if sfx.startswith("planet") else f"gm_{sfx}"
        local = shp if not sfx.startswith("planet") else planet(0).translate((-CD, 0, 0))
        parts.append(Part(f"{prefix}_{sfx}", _placed(shp, origin, zdir, xdir), child if sfx in ON_CHILD else parent, group,
                          color=look, note=note, print_as=pa, print_solid=local, rot=PRINT_ROT[sfx],
                          infill=100 if sfx in ("sun",) or sfx.startswith("planet") else 40, walls=4))
    for sfx, shp, look, kind in bought():
        mass = STS3250_MASS if sfx == "servo" else 28.0 if sfx == "bearing" else 0.0
        key = "sts3250" if sfx == "servo" else "b6807" if sfx == "bearing" else "hall" if sfx == "hall" else ""
        buys.append(Bought(f"{prefix}_{sfx}", _placed(shp, origin, zdir, xdir), child if sfx in ON_CHILD else parent, group,
                           kind, mass, key, look=look))
    return parts, buys


def mirror_frame(origin, zdir, xdir):
    """The same module on the right side: mirror the frame through y = 0 (the module is symmetric about its x-z plane)."""
    m = lambda v: (v[0], -v[1], v[2])  # noqa: E731
    return m(origin), m(zdir), m(xdir)
