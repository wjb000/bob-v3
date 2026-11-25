"""Torso. It sits on the inner-tube cap, with the column coming up through
the bottom. The shell has a shelf that bolts down onto the cap with four M5.
The back plate holds the yokes and the boards. The column lives in cad/column.py.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import Bought, Part, box, cut, cyl, cyl_between, fuse, hw, rrect
from base import JOIN_OFF, split_one, tab_at

S0 = P.SHOULDER_Z0  # shoulder axis at the zero pose


# ---------------------------------------------------------------- torso

TX0 = P.TORSO_X0
TX1 = TX0 + P.TORSO_D
TCX = (TX0 + TX1) / 2
BP_X0, BP_X1 = TX0 + 4.0, TX0 + 12.0  # back plate
BP_Z = (-146.0, -22.0)  # bottom stays above the belly joiner tabs
YOKE_FACE_X = BP_X1


def _tz(sz, dz):
    return sz + dz


def back_plate(sz=S0) -> cq.Shape:
    z0, z1 = sz + BP_Z[0], sz + BP_Z[1]
    s = cq.Workplane("YZ").workplane(offset=BP_X0).center(0, (z0 + z1) / 2).sketch().rect(140, z1 - z0) \
        .vertices().fillet(8).finalize().extrude(BP_X1 - BP_X0).val()
    tools = []
    # shell screws come in through the back wall into inserts here
    for pt in _shell_back_pts(sz):
        tools.append(cyl_between("x", (pt[0], pt[1]), BP_X0 - 1, BP_X0 + P.M3_INSERT_DEPTH, P.M3_INSERT))
    # yoke webs bolt to the front face
    for pt in _yoke_web_pts(sz):
        tools.append(cyl_between("x", (pt[0], pt[1]), BP_X0 - 1, BP_X1 + 1, P.M3))
        tools.append(cyl_between("x", (pt[0], pt[1]), BP_X0 - 1, BP_X0 + 3, P.M3_HEAD))
    # Jetson / hub grid on the front face, M3 thread-forming on 20 mm
    for y in range(-60, 61, 20):
        for z in range(int(z0 + 20), int(sz - 115), 20):
            if all(abs(y - p[0]) > 7 or abs(z - p[1]) > 7 for p in _shell_back_pts(sz) + _yoke_web_pts(sz)):
                if not (abs(abs(y) - 16) < 10 and min(abs(z - (sz - 52)), abs(z - (sz - 36))) < 10):
                    tools.append(cyl_between("x", (y, z), BP_X1 - 7, BP_X1 + 1, 2.6))
    hw("M3 heat-set insert", len(_shell_back_pts(sz)))
    return cut(s, *tools)


def _shell_back_pts(sz):
    # Outboard of the column (the tube occupies y = ±50).
    return [(sy * 62.0, sz + dz) for sy in (1, -1) for dz in (-142.0, -100.0, -55.0)]


def _yoke_web_pts(sz):
    return [(sy * y, sz + dz) for sy in (1, -1) for y in (30.0, 60.0) for dz in (-100.0, -70.0, -42.0)]


def _dm_rear_holes(center, axis, face, pcd=P.DM_REAR_PCD, n=P.DM_REAR_N, depth=12):
    """Holes for the motor's rear screws, drilled from the rear face outward (axis points out of the motor rear)."""
    out = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        u, v = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        if axis == "y":
            p = (center[0] + u, face, center[2] + v)
            d = (0, 1 if depth > 0 else -1, 0)
        elif axis == "x":
            p = (face, center[1] + u, center[2] + v)
            d = (1 if depth > 0 else -1, 0, 0)
        else:
            p = (center[0] + u, center[1] + v, face)
            d = (0, 0, 1 if depth > 0 else -1)
        out.append(cyl(p, d, P.M3, abs(depth)))
    return out


J1_FRAME = lambda sz: ((P.SHOULDER_X, P.J1_FACE_Y, sz), (0, 1, 0), (-1, 0, 0))  # noqa: E731  STS3095 J1, servo toward the back


def yoke(side, sz=S0) -> cq.Shape:
    """Left yoke (side=1). Holds the J1 STS3095 and bolts to the back plate. Right is mirrored."""
    import servo as G

    cx, cz = P.SHOULDER_X, sz
    cup, inserts, keep = G.mount(*J1_FRAME(sz))
    # Stay outside the column. The tube fills y = ±50 up to the cap.
    upper = box(YOKE_FACE_X, cx + 10, 48, 140, cz + 18, cz + 30)
    lower = box(YOKE_FACE_X, cx + 10, 48, 140, cz - 30, cz - 18)
    side_plate = box(YOKE_FACE_X + 6, 62, 46, 140, cz - 30, cz + 30)
    # Stop under the chest shelf. The shelf spans this x, and the web does not need to reach the neck.
    z_web = P.COL_INNER_TOP0 + 6.0
    web = box(YOKE_FACE_X, YOKE_FACE_X + 6, 0.3, 70, cz - 110, z_web)
    gusset = box(YOKE_FACE_X, cx - 20, 54, 70, cz - 110, cz + 30)
    # Cut keep from the yoke body first, then fuse the cup.
    # Same order as cad/arm.py after PR #3; see cad/servo.py mount().
    s = fuse(cut(fuse(upper, lower, side_plate, web, gusset), keep), cup)
    tools = [inserts]
    for y, z in _yoke_web_pts(sz):
        if y > 0:
            tools.append(cyl_between("x", (y, z), YOKE_FACE_X - 1, YOKE_FACE_X + P.M3_INSERT_DEPTH, P.M3_INSERT))
    for x, y in _neck_pts():
        if y > 0:
            tools.append(cyl((x, y, cz + 30 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    tools.append(box(NECK_X - P.STS_SHAFT_FROM_END - 5, NECK_X - P.STS_SHAFT_FROM_END + P.STS_L + 5, -20, 20, cz + 4, cz + 31))
    hw("M3 heat-set insert", 6 + 2 + 4)
    hw("M3x12 socket head", 6)
    hw("M3x10 socket head (servo tabs)", 4)
    s = cut(s, *tools, _column_void())
    # stay inside the torso's rounded back corners
    s = s.intersect(_torso_solid(sz, P.TORSO_WALL + 1.0))
    return s if side > 0 else s.mirror("XZ", (0, 0, 0))


def j1_modules(sz=S0):
    import servo as G

    parts, buys = [], []
    for side in ("l", "r"):
        fr = J1_FRAME(sz) if side == "l" else G.mirror_frame(*J1_FRAME(sz))
        p, b = G.instance(f"j1_{side}", *fr, "lift", f"{side}_link1", "torso", kind="sts3095")
        parts += p
        buys += b
    return parts, buys


def _neck_pts():
    c = TCX
    return [(c - 24.0, 24.0), (c + 24.0, 24.0), (c - 24.0, -24.0), (c + 24.0, -24.0)]


NECK_X = P.NECK_X


def neck_mount(sz=S0) -> cq.Shape:
    z0 = sz + 30.0
    plate = rrect(TCX, 0, z0, z0 + 8, 108, 70, 10)
    sx0, sx1 = NECK_X - P.STS_SHAFT_FROM_END - 0.3, NECK_X - P.STS_SHAFT_FROM_END + P.STS_L + 0.3
    cradle = box(sx0 - 3, sx1 + 3, -P.STS_W / 2 - 3.3, P.STS_W / 2 + 3.3, sz + 10, z0 + 8)
    s = fuse(plate, cradle)
    tools = [box(sx0, sx1, -P.STS_W / 2 - 0.3, P.STS_W / 2 + 0.3, sz + 12, z0 + 20),
             box(sx0 + 4, sx1 - 4, -6, 6, sz + 5, sz + 14)]
    # neck harness hole behind the pan servo (tilt servo lead + three USB leads, about 8 mm bundle)
    tools.append(cyl((NECK_X - 29.0, 0, z0 - 1), "z", 14.0, 10))
    for x, y in _neck_pts():
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 12))
        tools.append(cyl((x, y, z0 + 4), "z", P.M3_HEAD, 12))
    for x, y in _torso_top_pts():
        tools.append(cyl((x, y, z0 + 8 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    hw("M3x10 socket head", 4)
    hw("M3 heat-set insert", 4)
    return cut(s, *tools)


def _torso_top_pts():
    return [(TCX - 20.0, 30.0), (TCX - 20.0, -30.0), (TCX + 36.0, 28.0), (TCX + 36.0, -28.0)]


def _torso_seam_pairs(sz):
    """(a, b, inward normal) for joiner tabs. Vertical seam y=0, horizontal seam at the tier split."""
    out = []
    zf = TX1 - P.TORSO_WALL
    for dz in (-145.0, -40.0, 15.0):
        z = sz + dz
        out.append(((zf, -JOIN_OFF, z), (zf, JOIN_OFF, z), (-1, 0, 0)))
    zs = sz + P.TORSO_SPLIT
    for y in (-75.0, -30.0, 30.0, 75.0):
        out.append(((zf, y, zs - JOIN_OFF), (zf, y, zs + JOIN_OFF), (-1, 0, 0)))
    for sy in (1, -1):
        for x in (TX0 + 50.0, TX1 - 46.0):
            za, zb_ = zs - JOIN_OFF, zs + JOIN_OFF
            ya = half_width(za, sz) - P.TORSO_WALL
            yb = half_width(zb_, sz) - P.TORSO_WALL
            out.append(((x, sy * ya, za), (x, sy * yb, zb_), (0, -sy, 0)))
    zb = sz - P.TORSO_BELOW + P.TORSO_WALL
    # Rear tabs sit beside the column, forward of the back plate. At |y| = 40 the tube
    # has pulled in, so a 14 mm tab fits between the plate (x = −63) and the tube.
    x_rear = TX0 + 16.0
    for sy in (1, -1):
        out.append(((x_rear, sy * 40.0 - JOIN_OFF, zb), (x_rear, sy * 40.0 + JOIN_OFF, zb), (0, 0, 1)))
    out.append(((TX1 - 16.0, -JOIN_OFF, zb), (TX1 - 16.0, JOIN_OFF, zb), (0, 0, 1)))
    return out


WAIST_HW = 100.0  # half width at the bottom of the torso; the lower tier tapers out to TORSO_HW


def half_width(z, sz=S0):
    zs, z0 = sz + P.TORSO_SPLIT, sz - P.TORSO_BELOW
    if z >= zs:
        return P.TORSO_HW
    t = max(0.0, (z - z0) / (zs - z0))
    return WAIST_HW + (P.TORSO_HW - WAIST_HW) * t


def _torso_solid(sz, inset):
    z0, z1, zs = sz - P.TORSO_BELOW, sz + P.TORSO_ABOVE, sz + P.TORSO_SPLIT
    lx, r = P.TORSO_D - 2 * inset, P.TORSO_R - inset
    ch = max(16.0 - inset * (math.sqrt(2) - 1), 0.0)
    upper = rrect(TCX, 0, zs - 0.01, z1 - inset, lx, 2 * (P.TORSO_HW - inset), r, chamfer_top=ch)
    s0 = cq.Sketch().rect(lx, 2 * (WAIST_HW - inset)).vertices().fillet(r)
    s1 = cq.Sketch().rect(lx, 2 * (P.TORSO_HW - inset)).vertices().fillet(r)
    lower = (cq.Workplane("XY").placeSketch(s0.moved(cq.Location(cq.Vector(TCX, 0, z0 + inset))),
                                            s1.moved(cq.Location(cq.Vector(TCX, 0, zs)))).loft().val())
    return upper.fuse(lower).clean()


def _cap_bolts():
    b = P.CAP_BOLT
    return [(P.COL_X + sx * b, sy * b) for sx in (1, -1) for sy in (1, -1)]


def _column_void():
    """Column and cap, with a gap. Torso parts stay out of this except the shelf."""
    d = P.COL_OUTER_D + 6.0
    return rrect(P.COL_X, 0, 0, P.COL_INNER_TOP0 + 8.6, d, d, P.COL_OUTER_R + 2)


def torso_shell(sz=S0) -> cq.Shape:
    z0, z1 = sz - P.TORSO_BELOW, sz + P.TORSO_ABOVE
    outer = _torso_solid(sz, 0.0)
    s = outer.cut(_torso_solid(sz, P.TORSO_WALL))
    adds, tools = [], []
    for a, b, n in _torso_seam_pairs(sz):
        c = [(a[i] + b[i]) / 2 for i in range(3)]
        for q in (a, b):
            depth = 9.0 + sum((c[i] - q[i]) * n[i] for i in range(3))
            adds.append(cyl((q[0] - n[0], q[1] - n[1], q[2] - n[2]), n, 10, depth + 1))
            p = (q[0] + n[0] * (depth + 0.5), q[1] + n[1] * (depth + 0.5), q[2] + n[2] * (depth + 0.5))
            tools.append(cyl(p, (-n[0], -n[1], -n[2]), P.M3_INSERT, P.M3_INSERT_DEPTH))
    # bosses under the top skin onto the neck plate
    for x, y in _torso_top_pts():
        adds.append(cyl((x, y, sz + 38), "z", 10, z1 - P.TORSO_WALL - sz - 38 + 0.5))
    # shelf across the chest, 0.5 mm above the cap, fused into the front and back walls
    z_cap = P.COL_INNER_TOP0 + 8.0
    shelf = rrect(TCX, 0, z_cap + 0.5, z_cap + 6.0, P.TORSO_D + 2.0, 78, 12)
    shelf = shelf.cut(cyl((P.COL_X, 0, z_cap), "z", 22, 12))
    adds.append(shelf)
    s = fuse(s, *adds)
    s = s.intersect(outer)
    for x, y in _torso_top_pts():
        tools.append(cyl((x, y, sz + 37), "z", P.M3, 30))
        tools.append(cyl((x, y, z1 - 1.2), "z", P.M3_HEAD, 3))
    for y, z in _shell_back_pts(sz):
        tools.append(cyl_between("x", (y, z), TX0 - 1, TX0 + 5, P.M3))
    # neck harness hole in the top skin, over the neck_mount hole; the neck collar covers it
    tools.append(cyl((NECK_X - 29.0, 0, z1 - 6), "z", 14.0, 10))
    # shoulder ports
    for sy in (1, -1):
        tools.append(cyl_between("y", (P.SHOULDER_X, sz), sy * (P.TORSO_HW - 10), sy * (P.TORSO_HW + 5), 64))
    # the column passes through the belly and ends under the shelf
    tools.append(rrect(P.COL_X, 0, z0 - 4, P.COL_INNER_TOP0 - 0.4,
                       P.COL_OUTER_D + 6, P.COL_OUTER_D + 6, P.COL_OUTER_R + 2))
    # Groove for the top-limit switch on the front of the fixed outer tube.
    # It runs the whole lower belly, so the shell clears the switch at every lift.
    tools.append(box(2, 18, P.COL_OUTER_D / 2 - 1, P.COL_OUTER_D / 2 + 16, z0 - 4, P.COL_INNER_TOP0 - 2))
    for x, y in _cap_bolts():
        tools.append(cyl((x, y, z_cap - 1), "z", P.M5, 14))
        tools.append(cyl((x, y, z_cap + 3.0), "z", 9.5, 6))
    # neck port
    tools.append(cyl((NECK_X, 0, z1 - 10), "z", 36, 20))
    # chest light slot and speaker grille on the front
    tools.append(rrect(TX1, 0, sz - 64, sz - 58, 12, 120, 3))
    for r, n in ((0, 1), (7, 6), (14, 12), (21, 18)):
        for i in range(n):
            a = 2 * math.pi * i / n
            tools.append(cyl_between("x", (r * math.cos(a), sz - 114 + r * math.sin(a)), TX1 - 6, TX1 + 1, 3.2))
    # back vents for the Jetson
    for i in range(6):
        for sy in (1, -1):
            y = sy * (40 + 7 * i)
            tools.append(box(TX0 - 1, TX0 + 5, y - 1.8, y + 1.8, sz - 155, sz - 100))
    hw("M3x10 socket head", 2 * len(_torso_seam_pairs(sz)) + len(_shell_back_pts(sz)) + len(_torso_top_pts()))
    hw("M3 heat-set insert", 2 * len(_torso_seam_pairs(sz)))
    return cut(s, *tools)


def torso_joiners(sz=S0) -> list[cq.Shape]:
    return [tab_at(a, b, n) for a, b, n in _torso_seam_pairs(sz)]


def torso_parts() -> list[Part]:
    out = [Part("torso_back_plate", back_plate(), "lift", "torso", color="frame",
                note="Yokes bolt to the front face. The Pi and the bus adapters sit beside the column.")]
    out.append(Part("yoke_l", yoke(1), "lift", "torso", color="frame", rot=(90, 0, 0),
                    note="Holds the left J1 STS3095. Prints on its centre face, cup up. 5 walls, 30% infill."))
    out.append(Part("yoke_r", yoke(-1), "lift", "torso", color="frame", rot=(-90, 0, 0), note="Mirror of yoke_l."))
    out.append(Part("neck_mount", neck_mount(), "lift", "torso", color="frame", note="Pan servo cradle, bridges the yokes."))
    out += j1_modules()[0]
    full = torso_shell()
    zs = S0 + P.TORSO_SPLIT
    for tier, (z0, z1), rot in (("lower", (0, zs), (0, 0, 0)), ("upper", (zs, 2000), (180, 0, 0))):
        for sy, s in ((1, "l"), (-1, "r")):
            region = box(-500, 500, 0, sy * 500, z0, z1)
            out.append(Part(f"torso_{tier}_{s}", split_one(full, region, f"torso_{tier}_{s}"), "lift", "torso",
                            color="shell", rot=rot, walls=3, infill=15,
                            note="Lower tier prints floor-down; upper tier prints top-down."))
    return out


def bought(sz=S0) -> list[Bought]:
    import vendor as V

    out = []
    out += j1_modules(sz)[1]
    # Pi and hub stand on the side walls of the upper chest, thin side toward the wall.
    # Buses lie flat below the yokes, forward of the gusset (that gusset ends at x ≈ −11).
    # Side walls of the upper chest. Offsets follow the shoulder, so a shorter column keeps the boards in the shell.
    out += V.boughts("pi5", V.place(V.pi5(), (0, 78, sz - 60), xdir=(1, 0, 0), zdir=(0, 1, 0)), "lift", "torso", "electronics", 75, "pi5")
    out += V.boughts("usb_hub", V.place(V.usb_board(64, 36, 16, ports=2), (0, -78, sz - 60), xdir=(1, 0, 0), zdir=(0, -1, 0)),
                     "lift", "torso", "electronics", 60, "usbhub")
    for name, y in (("servo_bus", 72), ("servo_bus_r", -72)):
        out += V.boughts(name, V.place(V.usb_board(44, 30, 14, ports=2), (30, y, sz - 126), xdir=(1, 0, 0), zdir=(0, 0, 1)),
                         "lift", "torso", "electronics", 25, "busadapter")
    out += V.boughts("speaker", V.place(V.speaker(), (TX1 - 10, 0, sz - 114), xdir=(0, 1, 0), zdir=(1, 0, 0)), "lift", "torso", "electronics", 40, "speaker")
    out += V.boughts("pan_servo", V.place(V.sts3215(), (NECK_X, 0, sz + 47)), "lift", "torso", "actuator", P.STS_MASS, "sts3215")
    out.append(Bought("light_chest", rrect(TX1 - 2.2, 0, sz - 63.5, sz - 58.5, 3.0, 118, 2.5), "lift", "torso", "electronics", 5, "ledstrip", look="glow"))
    return out
