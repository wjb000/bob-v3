"""Torso. It sits on the inner-tube cap, with the column coming up through
the bottom. The shell has a shelf that bolts down onto the cap with four M5.
The back plate holds the yokes. The Pi and the USB hub screw to bosses on the
upper side walls; the 5 V regulator (b5) and the two 12 V arm converters (b12a)
have printed mounts in the lower bay; the bus adapters sit on shelves forward
of those converters. A Ø16 pass in each yoke takes the column-cap umbilical
into the bay, and a shoulder pass at (20, ±100, 436) takes the arm cables.
The column lives in cad/column.py.
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

# Electronics mounts (printed bosses / shelves, existing M3 inserts, no new bought parts)
PI_BOSS = 7.0  # feet plane, inward of the inner side wall
PI_HOLES = [(sx * 29.0, sy * 24.5) for sx in (-1, 1) for sy in (-1, 1)]
HUB_HOLES = [(sx * 28.0, sy * 14.0) for sx in (-1, 1) for sy in (-1, 1)]  # 64 x 36 board, 4 mm inset
# Bus boards are rotated (44 mm along Y, 30 mm along X) so they sit forward of the 74 mm Daygreens.
BUS_X, BUS_Y, BUS_Z = 55.0, 92.0, 126.0  # origin of each bus board, z is below the shoulder

# Electronics-check poses, robot frame mm at lift 0 (+X forward, +Y left, +Z up).
CAP_PASS_X, CAP_PASS_Z, CAP_PASS_D = -40.0, 436.0, 16.0  # yoke: cap region → electronics bay
SHOULDER_PASS_X, SHOULDER_PASS_Y, SHOULDER_PASS_Z = 20.0, 100.0, 436.0
B5_POS = (-40.0, 84.0, 290.0)  # Pololu D36V50F5, wiring b5 / vendor reg_5v
# b12a is two Daygreen 74×74×31 mm converters. The right one is at the requested
# (0, −80, 276). The left one would overlap b5 and the yoke at that height, so it
# sits under the yoke lower beam at z=341.
B12A_POS_R = (0.0, -80.0, 276.0)
B12A_POS_L = (0.0, 80.0, 341.0)
POLOLU_HOLES = [(sx * 8.9, sy * 8.9) for sx in (-1, 1) for sy in (-1, 1)]  # D36V50F5, 0.7 in spacing
BUCK_L, BUCK_H = 74.0, 32.0
BUCK_HOLES = [(sx * 33.0, sy * 28.0) for sx in (-1, 1) for sy in (-1, 1)]  # flange holes, 8 mm end flanges


def _side_board_origin(sz, side, boss=PI_BOSS):
    """Feet plane against bosses on the inner side wall. +z (parts) points inward."""
    y = side * (P.TORSO_HW - P.TORSO_WALL - boss)
    return (0.0, y, sz - 60.0)


def _side_board_frame(sz, side, boss=PI_BOSS):
    # zdir inward; xdir forward; ydir = z × x
    return _side_board_origin(sz, side, boss), (0.0, -side, 0.0), (1.0, 0.0, 0.0)


def _side_board_holes(sz, side, holes, boss=PI_BOSS):
    ox, oy, oz = _side_board_origin(sz, side, boss)
    # ydir = z × x: side=+1 (left wall) -> (0,0,1); side=-1 -> (0,0,-1)
    return [(ox + lx, oy, oz + side * ly) for lx, ly in holes]


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
    # Cable passes are cut after the cup is fused so they cannot subtract cup material.
    # Ø16 from the column-cap region (z 400–450) through the gusset/upper into the bay.
    tools.append(cyl_between("y", (CAP_PASS_X, CAP_PASS_Z), 48.0, 80.0, CAP_PASS_D))
    # Shoulder pass near (20, +100, 436), inboard of the J1 flange (flange starts at y ≈ 112).
    tools.append(cyl_between("y", (SHOULDER_PASS_X, SHOULDER_PASS_Z), 80.0, 108.0, 14.0))
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
    cradle = box(sx0 - 3, sx1 + 3, -P.STS_W / 2 - 3.3, P.STS_W / 2 + 3.3, sz + 4, z0 + 8)
    s = fuse(plate, cradle)
    tools = [box(sx0, sx1, -P.STS_W / 2 - 0.3, P.STS_W / 2 + 0.3, sz + 12, z0 + 20),
             box(sx0 + 4, sx1 - 4, -6, 6, sz + 5, sz + 14)]
    for x, y in _neck_pts():
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 12))
        tools.append(cyl((x, y, z0 + 4), "z", P.M3_HEAD, 12))
    for x, y in _torso_top_pts():
        tools.append(cyl((x, y, z0 + 8 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    # Pan STS3215 tab inserts in a thickened cradle floor (the old 2 mm floor was too thin).
    cx = NECK_X + (P.STS_L / 2 - P.STS_SHAFT_FROM_END)
    for dx in (-P.STS_HOLE_L / 2, P.STS_HOLE_L / 2):
        for dy in (-P.STS_HOLE_W / 2, P.STS_HOLE_W / 2):
            tools.append(cyl((cx + dx, dy, sz + 12.2 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 0.4))
    hw("M3x10 socket head", 4)
    hw("M3x10 socket head (servo tabs)", 4)
    hw("M3 heat-set insert", 8)
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
    # Zip-tie holes beside the umbilical, same idea as the cap strain relief.
    for sy in (1, -1):
        tools.append(cyl((P.COL_X + 18.0, sy * 12.0, z_cap - 1), "z", 3.2, 10))
    hw("4 in zip tie (torso umbilical)", 2)
    for x, y in _torso_top_pts():
        tools.append(cyl((x, y, sz + 37), "z", P.M3, 30))
        tools.append(cyl((x, y, z1 - 1.2), "z", P.M3_HEAD, 3))
    for y, z in _shell_back_pts(sz):
        tools.append(cyl_between("x", (y, z), TX0 - 1, TX0 + 5, P.M3))
    # shoulder ports
    for sy in (1, -1):
        tools.append(cyl_between("y", (P.SHOULDER_X, sz), sy * (P.TORSO_HW - 10), sy * (P.TORSO_HW + 5), 64))
    # Dedicated shoulder cable pass through torso_upper near (20, ±100, 436).
    # The 64 mm port already opens this neighbourhood; this marks a Ø16 cable path.
    for sy in (1, -1):
        tools.append(cyl_between("y", (SHOULDER_PASS_X, SHOULDER_PASS_Z),
                                 sy * (SHOULDER_PASS_Y - 10.0), sy * (P.TORSO_HW + 5), 16.0))
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
    # Inner retaining lip around the speaker so it seats against the grille.
    adds.append(cyl((TX1 - P.TORSO_WALL, 0, sz - 114), "-x", 44, 4).cut(
        cyl((TX1 - P.TORSO_WALL + 1, 0, sz - 114), "-x", 34, 6)))
    # Back vents for the Pi and the hub
    for i in range(6):
        for sy in (1, -1):
            y = sy * (40 + 7 * i)
            tools.append(box(TX0 - 1, TX0 + 5, y - 1.8, y + 1.8, sz - 155, sz - 100))
    # Pi (left) and USB hub (right): four insert bosses on each inner side wall.
    for side, holes in ((1, PI_HOLES), (-1, HUB_HOLES)):
        inner = side * (P.TORSO_HW - P.TORSO_WALL)
        for x, y, z in _side_board_holes(sz, side, holes):
            adds.append(cyl_between("y", (x, z), inner, inner - side * PI_BOSS, 10))
            tools.append(cyl_between("y", (x, z), inner - side * (PI_BOSS + 1), inner - side * (PI_BOSS - P.M3_INSERT_DEPTH), P.M3_INSERT))
        hw("M3 heat-set insert", 4)
        hw("M3x10 socket head (electronics)", 4)
    # Bus-adapter shelves, forward of the Daygreens, 30 mm in X by 44 mm in Y.
    z_bus = sz - BUS_Z
    for sy in (1, -1):
        y0, y1 = sy * (BUS_Y - 24), sy * (half_width(z_bus, sz) - P.TORSO_WALL)
        if y0 > y1:
            y0, y1 = y1, y0
        adds.append(box(BUS_X - 16, BUS_X + 16, y0, y1, z_bus - 3.5, z_bus))
        tools.append(box(BUS_X - 10, BUS_X - 6, sy * BUS_Y - 8, sy * BUS_Y + 8, z_bus - 5, z_bus + 1))
        hw("4 in zip tie (bus adapter)", 1)
    # b5: Pololu D36V50F5 shelf at (−40, 84, 290), four M3 inserts, rib to the left wall and back.
    bx, by, bz = B5_POS
    adds.append(box(TX0 + P.TORSO_WALL - 1, bx + 16.0, by - 16.0,
                    half_width(bz, sz) - P.TORSO_WALL + 2.0, bz - 6.0, bz))
    for lx, ly in POLOLU_HOLES:
        tools.append(cyl((bx + lx, by + ly, bz - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    hw("M3 heat-set insert", 4)
    hw("M3x10 socket head (electronics)", 4)
    # b12a: wall pads for the two Daygreen 74×74 converters. Origin is the body centre;
    # the feet plane is toward the wall by half the 32 mm case height.
    for (ox, oy, oz), side in ((B12A_POS_L, 1), (B12A_POS_R, -1)):
        feet = oy + side * (BUCK_H / 2.0)
        wall = side * (half_width(oz, sz) + 8.0)
        y0, y1 = (feet, wall) if feet < wall else (wall, feet)
        adds.append(box(ox - 39.0, ox + 39.0, y0, y1, oz - 39.0, oz + 39.0))
        for lx, lz in BUCK_HOLES:
            tools.append(cyl_between("y", (ox + lx, oz + lz),
                                     feet + side * 1.0, feet - side * P.M3_INSERT_DEPTH, P.M3_INSERT))
        hw("M3 heat-set insert", 4)
        hw("M3x10 socket head (electronics)", 4)
    hw("M3x10 socket head", 2 * len(_torso_seam_pairs(sz)) + len(_shell_back_pts(sz)) + len(_torso_top_pts()))
    hw("M3 heat-set insert", 2 * len(_torso_seam_pairs(sz)))
    s = fuse(s, *adds)
    s = s.intersect(outer)
    return cut(s, *tools)


def torso_joiners(sz=S0) -> list[cq.Shape]:
    return [tab_at(a, b, n) for a, b, n in _torso_seam_pairs(sz)]


def torso_parts() -> list[Part]:
    out = [Part("torso_back_plate", back_plate(), "lift", "torso", color="frame",
                note="Yokes bolt to the front face. Thread-forming grid for extras; the Pi, hub, b5 and b12a have printed mounts.")]
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
    # Pi (left wall) and USB hub (right wall) screw into the side-wall bosses; parts face inward.
    # Buses sit on shelves forward of the Daygreens, 44 mm along Y and 30 mm along X.
    po, pz, px = _side_board_frame(sz, 1)
    out += V.boughts("pi5", V.place(V.pi5(), po, xdir=px, zdir=pz), "lift", "torso", "electronics", 75, "pi5")
    ho, hz, hx = _side_board_frame(sz, -1)
    out += V.boughts("usb_hub", V.place(V.usb_board(64, 36, 16, ports=2), ho, xdir=hx, zdir=hz),
                     "lift", "torso", "electronics", 60, "usbhub")
    for name, sy in (("servo_bus", 1), ("servo_bus_r", -1)):
        out += V.boughts(name, V.place(V.usb_board(44, 30, 14, ports=2),
                                       (BUS_X, sy * BUS_Y, sz - BUS_Z),
                                       xdir=(0, sy, 0), zdir=(0, 0, 1)),
                         "lift", "torso", "electronics", 25, "busadapter")
    out += V.boughts("reg_5v_torso", V.place(V.small_board(22, 22, (8, 8, 3), look="pcb_blue"), B5_POS),
                     "lift", "torso", "electronics", 8, "pololu5")
    for name, (ox, oy, oz), side in (("buck_12v_arm_l", B12A_POS_L, 1), ("buck_12v_arm_r", B12A_POS_R, -1)):
        feet = (ox, oy + side * (BUCK_H / 2.0), oz)
        out += V.boughts(name, V.place(V.finned_buck(74, 74, 32), feet, xdir=(1, 0, 0), zdir=(0.0, -side, 0.0)),
                         "lift", "torso", "electronics", 280, "buck12")
    out += V.boughts("speaker", V.place(V.speaker(), (TX1 - 10, 0, sz - 114), xdir=(0, 1, 0), zdir=(1, 0, 0)), "lift", "torso", "electronics", 40, "speaker")
    out += V.boughts("pan_servo", V.place(V.sts3215(), (NECK_X, 0, sz + 47)), "lift", "torso", "actuator", P.STS_MASS, "sts3215")
    out.append(Bought("light_chest", rrect(TX1 - 2.2, 0, sz - 63.5, sz - 58.5, 3.0, 118, 2.5), "lift", "torso", "electronics", 5, "ledstrip", look="glow"))
    return out
