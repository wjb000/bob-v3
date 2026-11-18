"""Mast (fixed to the base), carriage and torso (ride the lift).

Lift: NEMA 17 in the cap turns a TR8x2 screw that hangs down the mast. The
carriage rides two 12 mm rods on four LM12UU. Its tongue leaves through the
mast's front slot and bolts to the torso back plate with four M5.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import (
    Bought, Part, box, cbox, cut, cyl, cyl_between, fuse, hexagon, hw,
    rrect, rrect_shell, tube_between,
)
from base import JOIN_OFF, split_one, tab_at

S0 = P.SHOULDER_Z0  # shoulder axis at the zero pose
MX0, MX1 = P.MAST_X - P.MAST_DX / 2, P.MAST_X + P.MAST_DX / 2
MHY = P.MAST_DY / 2
IN_X0, IN_X1, IN_Y = MX0 + P.MAST_WALL, MX1 - P.MAST_WALL, MHY - P.MAST_WALL
JOINT_BOSSES = [(MX0 + 10, -52.0), (MX0 + 10, 52.0), (MX1 - 10, -47.0), (MX1 - 10, 47.0)]
BOSS_H = 14.0


# ---------------------------------------------------------------- mast

def _mast_tube(z0, z1):
    s = rrect_shell(P.MAST_X, 0, z0, z1, P.MAST_DX, P.MAST_DY, P.MAST_R, P.MAST_WALL, open_top=True, open_bot=True)
    return s.cut(box(MX1 - P.MAST_WALL - 2, MX1 + 2, -P.MAST_SLOT / 2, P.MAST_SLOT / 2, z0 - 1, z1 + 1))


def mast_segment(i, z0, z1, n) -> cq.Shape:
    s = _mast_tube(z0, z1)
    adds, tools = [], []
    top_is_cap = i == n - 1
    for x, y in JOINT_BOSSES:
        adds.append(cyl((x, y, z1 - BOSS_H), "z", 12, BOSS_H))
        if top_is_cap:
            # screw goes up into an insert in the cap; head sits under this boss
            tools.append(cyl((x, y, z1 - BOSS_H - 1), "z", P.M3, BOSS_H + 2))
            tools.append(cyl((x, y, z1 - BOSS_H - 1), "z", P.M3_HEAD, BOSS_H - 6))
        else:
            tools.append(cyl((x, y, z1 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
        if i > 0:
            adds.append(cyl((x, y, z0), "z", 12, BOSS_H))
            tools.append(cyl((x, y, z0 - 1), "z", P.M3, BOSS_H + 2))
            tools.append(cyl((x, y, z0 + 8), "z", P.M3_HEAD, BOSS_H))
    hw("M3 heat-set insert", 4)
    hw("M3x14 socket head", 4)
    if i == 0:
        # foot flange onto the pan
        f = 14.0
        flange = rrect(P.MAST_X, 0, z0, z0 + 6, P.MAST_DX + 2 * f, P.MAST_DY + 2 * f, P.MAST_R + f)
        flange = flange.cut(rrect(P.MAST_X, 0, z0 - 1, z0 + 8, P.MAST_DX - 2, P.MAST_DY - 2, P.MAST_R - 1))
        adds.append(flange)
        # rod sockets
        for sy in (1, -1):
            adds.append(cyl((P.ROD_X, sy * P.ROD_Y, z0), "z", 26, 40))
            adds.append(box(IN_X0 - 1, P.ROD_X, sy * (P.ROD_Y - 5), sy * (P.ROD_Y + 5), z0, z0 + 40))
            adds.append(box(P.ROD_X - 5, P.ROD_X + 5, sy * P.ROD_Y, sy * (IN_Y + 1), z0, z0 + 40))
            tools.append(cyl((P.ROD_X, sy * P.ROD_Y, P.ROD_Z0), "z", P.ROD_HOLE, 60))
            # grub screw to stop the rod turning
            tools.append(cyl_between("x", (sy * P.ROD_Y, z0 + 25), P.ROD_X - 30, P.ROD_X, 2.6))
        # screw tail bushing
        zb = P.SCREW_Z1 - P.SCREW_LEN
        adds.append(box(IN_X0 - 1, P.SCREW_X + 12, -12, 12, zb - 14, zb + 6))
        tools.append(cyl((P.SCREW_X, 0, zb - 10), "z", 8.5, 30))
        # homing switch pad, on the back wall under the carriage
        adds.append(box(IN_X0 - 1, IN_X0 + 8, -10, 10, S0 - P.CARRIAGE_BELOW - 30, S0 - P.CARRIAGE_BELOW - 8))
        for dz in (-4.75, 4.75):
            tools.append(cyl_between("x", (0, S0 - P.CARRIAGE_BELOW - 19 + dz), IN_X0 - 2, IN_X0 + 9, 1.9))
        from base import PAN_PTS
        for x, y in PAN_PTS["mast"]:
            tools.append(cyl((x, y, z0 - 1), "z", P.M3, 10))
        # cable entry from the base
        tools.append(box(MX0 - 2, MX0 + P.MAST_WALL + 2, -22, 22, z0 + 12, z0 + 80))
        hw("M3x10 socket head", len(PAN_PTS["mast"]))
        hw("Micro limit switch (KW12, roller)", 1)
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.MAST_X, 0, z0, z1, P.MAST_DX + 40, P.MAST_DY + 40, P.MAST_R + 20))
    return cut(s, *tools)


def mast_cap() -> cq.Shape:
    z0 = P.MAST_TOP
    z1 = z0 + P.CAP_H
    s = rrect_shell(P.MAST_X, 0, z0, z1, P.MAST_DX, P.MAST_DY, P.MAST_R, P.MAST_WALL, chamfer_top=16, open_bot=True)
    adds = [
        # motor plate, NEMA face down onto its underside? no: face down, body above, plate under the face
        box(IN_X0 - 1, IN_X1 + 1, -IN_Y - 1, IN_Y + 1, P.NEMA_FACE_Z - 8, P.NEMA_FACE_Z),
    ]
    for sy in (1, -1):
        adds.append(cyl((P.ROD_X, sy * P.ROD_Y, z0), "z", 26, P.NEMA_FACE_Z - 8 - z0))
    for x, y in JOINT_BOSSES:
        adds.append(cyl((x, y, z0), "z", 12, 12))
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.MAST_X, 0, z0, z1, P.MAST_DX, P.MAST_DY, P.MAST_R, chamfer_top=16))
    tools = []
    for sy in (1, -1):
        tools.append(cyl((P.ROD_X, sy * P.ROD_Y, z0 - 1), "z", P.ROD_HOLE, P.ROD_Z0 + P.ROD_LEN - z0 + 2))
    for x, y in JOINT_BOSSES:
        tools.append(cyl((x, y, z0 - 1), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    tools.append(cyl((P.SCREW_X, 0, P.NEMA_FACE_Z - 20), "z", P.NEMA_PILOT + 0.4, 30))
    for dx in (-P.NEMA_BOLT / 2, P.NEMA_BOLT / 2):
        for dy in (-P.NEMA_BOLT / 2, P.NEMA_BOLT / 2):
            tools.append(cyl((P.SCREW_X + dx, dy, P.NEMA_FACE_Z - 20), "z", P.M3, 30))
            tools.append(cyl((P.SCREW_X + dx, dy, P.NEMA_FACE_Z - 30), "z", P.M3_HEAD, 22))
    # coupler window so the set screws can be reached through the slot side
    tools.append(cyl((P.SCREW_X, 0, z0 - 1), "z", 26, P.NEMA_FACE_Z - 8 - z0 + 1))
    # light ring groove for an LED strip and a 2 mm diffuser
    ring = rrect(P.MAST_X, 0, z0 + 50, z0 + 58, P.MAST_DX + 2, P.MAST_DY + 2, P.MAST_R + 1).cut(
        rrect(P.MAST_X, 0, z0 + 49, z0 + 59, P.MAST_DX - 3, P.MAST_DY - 3, P.MAST_R - 1.5))
    tools.append(ring)
    hw("M3 heat-set insert", 4)
    hw("M3x8 socket head (NEMA)", 4)
    hw("5 to 8 mm flexible coupler, 25 mm", 1)
    hw("WS2812B strip, 60/m, 0.5 m", 1)
    return cut(s, *tools)


def mast_parts() -> list[Part]:
    segs = P.mast_segments()
    out = []
    for i, (z0, z1) in enumerate(segs):
        out.append(Part(f"mast_{i}", mast_segment(i, z0, z1, len(segs)), "base", "mast", color="shell", rot=(0, 0, 0),
                        note="Prints standing. Inserts in the top bosses." if i else "Foot flange, rod sockets, screw bushing, homing pad."))
    out.append(Part("mast_cap", mast_cap(), "base", "mast", color="dark", rot=(180, 0, 0),
                    note="NEMA 17 plate, rod tops, light ring groove. Prints upside down."))
    return out


# ---------------------------------------------------------------- carriage

def carriage(sz=S0) -> cq.Shape:
    z0 = sz - P.CARRIAGE_BELOW
    z1 = z0 + P.CARRIAGE_H
    lo_c = z0 + 4 + P.LM12_LEN / 2
    hi_c = lo_c + P.BEARING_SPAN
    adds = []
    for sy in (1, -1):
        for zc in (lo_c, hi_c):
            adds.append(cyl((P.ROD_X, sy * P.ROD_Y, zc - P.LM12_LEN / 2 - 4), "z", 30, P.LM12_LEN + 8))
        # side web joining the two housings
        adds.append(box(P.ROD_X - 8, P.ROD_X + 8, sy * (P.ROD_Y - 15), sy * (P.ROD_Y - 9), z0, z1))
    # central spine, nut bridge at the bottom
    adds.append(box(P.ROD_X - 16, P.ROD_X + 16, -P.ROD_Y + 8, P.ROD_Y - 8, z0, z0 + 14))
    adds.append(box(P.ROD_X - 16, P.ROD_X + 16, -P.ROD_Y + 8, P.ROD_Y - 8, hi_c - 18, hi_c + 18))
    adds.append(box(P.ROD_X + 6, P.ROD_X + 16, -P.ROD_Y + 8, P.ROD_Y - 8, z0, z1))
    # tongue out through the slot to the torso back plate
    t0, t1 = sz - 225.0, sz - 155.0
    plate_x = P.TORSO_X0 + 4.0
    adds.append(box(P.ROD_X + 6, plate_x, -26, 26, t0, t1))
    s = fuse(*adds)
    tools = []
    for sy in (1, -1):
        for zc in (lo_c, hi_c):
            tools.append(cyl((P.ROD_X, sy * P.ROD_Y, zc - P.LM12_LEN / 2), "z", P.LM12_OD, P.LM12_LEN))
            tools.append(cyl((P.ROD_X, sy * P.ROD_Y, zc - 40), "z", P.ROD_D + 1.5, 80))
    tools.append(cyl((P.SCREW_X, 0, z0 - 1), "z", 11, P.CARRIAGE_H + 2))
    tools.append(cyl((P.SCREW_X, 0, z0 - 1), "z", P.T8_FLANGE + 0.4, 4.5 + 1))
    for dx, dy in [(P.T8_PCD / 2 * math.cos(a), P.T8_PCD / 2 * math.sin(a)) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]:
        tools.append(cyl((P.SCREW_X + dx, dy, z0 - 1), "z", 2.6, 14))
    # M5 to the back plate, nuts dropped into slots from above / below
    for y in (-16.0, 16.0):
        for zb, up in ((sz - 205.0, False), (sz - 170.0, True)):
            tools.append(cyl_between("x", (y, zb), plate_x - 30, plate_x + 1, P.M5))
            nx = plate_x - 18
            if up:
                tools.append(box(nx - 2.2, nx + 2.2, y - P.M5_NUT_AF / 2, y + P.M5_NUT_AF / 2, zb - 5, t1 + 1))
            else:
                tools.append(box(nx - 2.2, nx + 2.2, y - P.M5_NUT_AF / 2, y + P.M5_NUT_AF / 2, t0 - 1, zb + 5))
    hw("LM12UU linear bearing", 4)
    hw("TR8x2 brass flange nut", 1)
    hw("M3x10 thread-forming (T8 nut)", 4)
    hw("M5x30 socket head + nut (tongue)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- torso

TX0 = P.TORSO_X0
TX1 = TX0 + P.TORSO_D
TCX = (TX0 + TX1) / 2
BP_X0, BP_X1 = TX0 + 4.0, TX0 + 12.0  # back plate
BP_Z = (-212.0, -22.0)
YOKE_FACE_X = BP_X1


def _tz(sz, dz):
    return sz + dz


def back_plate(sz=S0) -> cq.Shape:
    z0, z1 = sz + BP_Z[0], sz + BP_Z[1]
    s = cq.Workplane("YZ").workplane(offset=BP_X0).center(0, (z0 + z1) / 2).sketch().rect(140, z1 - z0) \
        .vertices().fillet(8).finalize().extrude(BP_X1 - BP_X0).val()
    tools = []
    for y in (-16.0, 16.0):
        for zb in (sz - 205.0, sz - 170.0):
            tools.append(cyl_between("x", (y, zb), BP_X0 - 1, BP_X1 + 1, P.M5))
            tools.append(cyl_between("x", (y, zb), BP_X1 - 3, BP_X1 + 1, 9.5))
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
                if not (abs(abs(y) - 16) < 10 and min(abs(z - (sz - 205)), abs(z - (sz - 170))) < 10):
                    tools.append(cyl_between("x", (y, z), BP_X1 - 7, BP_X1 + 1, 2.6))
    hw("M3 heat-set insert", len(_shell_back_pts(sz)))
    return cut(s, *tools)


def _shell_back_pts(sz):
    return [(sy * 52.0, sz + dz) for sy in (1, -1) for dz in (-200.0, -125.0, -55.0)]


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


def yoke(side, sz=S0) -> cq.Shape:
    """Left yoke (side=1). Carries J1 and bolts to the back plate. Right is mirrored."""
    cx, cz = P.SHOULDER_X, sz
    face = P.J1_FACE_Y
    body0 = face - P.DM4340_H
    rear = body0 - 4.0
    cup = tube_between("y", (cx, cz), rear, face - 4.0, P.DM4340_D + 9, P.DM4340_D + 0.6)
    rear_wall = cyl_between("y", (cx, cz), rear, body0, P.DM4340_D + 9)
    beam = box(YOKE_FACE_X, cx, 0.3, body0 - 0.5, cz - 30, cz + 30)
    web = box(YOKE_FACE_X, YOKE_FACE_X + 6, 0.3, 70, cz - 110, cz + 30)
    gusset = box(YOKE_FACE_X, cx - 20, 0.3, 8, cz - 110, cz + 30)
    s = fuse(cup, rear_wall, beam, web, gusset)
    tools = [cyl_between("y", (cx, cz), rear - 14, body0 + 0.5, 22)]  # cable exit, deep enough for the XT30 and CAN plugs
    tools += _dm_rear_holes((cx, 0, cz), "y", body0 + 0.5, depth=-6)
    for y, z in _yoke_web_pts(sz):
        if y > 0:
            tools.append(cyl_between("x", (y, z), YOKE_FACE_X - 1, YOKE_FACE_X + P.M3_INSERT_DEPTH, P.M3_INSERT))
    for x, y in _neck_pts():
        if y > 0:
            tools.append(cyl((x, y, cz + 30 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    # lighten the beam, and leave room for the pan-servo cradle
    tools.append(box(YOKE_FACE_X + 10, cx - 36, 14, body0 - 8, cz - 22, cz + 22))
    tools.append(box(NECK_X - P.STS_SHAFT_FROM_END - 5, NECK_X - P.STS_SHAFT_FROM_END + P.STS_L + 5, -20, 20, cz + 4, cz + 31))
    hw("M3 heat-set insert", 6 + 2)
    hw("M3x12 socket head", 6)
    hw("M3x12 socket head (DM rear)", P.DM_REAR_N)
    s = cut(s, *tools)
    return s if side > 0 else s.mirror("XZ", (0, 0, 0))


def _neck_pts():
    return [(48.0, 24.0), (72.0, 24.0), (48.0, -24.0), (72.0, -24.0)]


NECK_X = P.HEAD_CX


def neck_mount(sz=S0) -> cq.Shape:
    z0 = sz + 30.0
    plate = rrect(98, 0, z0, z0 + 8, 108, 70, 10)
    sx0, sx1 = NECK_X - P.STS_SHAFT_FROM_END - 0.3, NECK_X - P.STS_SHAFT_FROM_END + P.STS_L + 0.3
    cradle = box(sx0 - 3, sx1 + 3, -P.STS_W / 2 - 3.3, P.STS_W / 2 + 3.3, sz + 10, z0 + 8)
    s = fuse(plate, cradle)
    tools = [box(sx0, sx1, -P.STS_W / 2 - 0.3, P.STS_W / 2 + 0.3, sz + 12, z0 + 20),
             box(sx0 + 4, sx1 - 4, -6, 6, sz + 5, sz + 14)]
    for x, y in _neck_pts():
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 12))
        tools.append(cyl((x, y, z0 + 4), "z", P.M3_HEAD, 12))
    for x, y in _torso_top_pts():
        tools.append(cyl((x, y, z0 + 8 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
    hw("M3x10 socket head", 4)
    hw("M3 heat-set insert", 4)
    return cut(s, *tools)


def _torso_top_pts():
    return [(60.0, 30.0), (60.0, -30.0), (140.0, 28.0), (140.0, -28.0)]


def _torso_seam_pairs(sz):
    """(a, b, inward normal) for joiner tabs. Vertical seam y=0, horizontal seam at the tier split."""
    out = []
    zf = TX1 - P.TORSO_WALL
    for dz in (-200.0, -125.0, -40.0, 15.0):
        z = sz + dz
        out.append(((zf, -JOIN_OFF, z), (zf, JOIN_OFF, z), (-1, 0, 0)))
    zs = sz + P.TORSO_SPLIT
    for y in (-110.0, -45.0, 45.0, 110.0):
        out.append(((zf, y, zs - JOIN_OFF), (zf, y, zs + JOIN_OFF), (-1, 0, 0)))
    for sy in (1, -1):
        for x in (75.0, 165.0):
            za, zb_ = zs - JOIN_OFF, zs + JOIN_OFF
            ya = half_width(za, sz) - P.TORSO_WALL
            yb = half_width(zb_, sz) - P.TORSO_WALL
            out.append(((x, sy * ya, za), (x, sy * yb, zb_), (0, -sy, 0)))
    zb = sz - P.TORSO_BELOW + P.TORSO_WALL
    for x in (85.0, 165.0):
        out.append(((x, -JOIN_OFF, zb), (x, JOIN_OFF, zb), (0, 0, 1)))
    return out


WAIST_HW = 122.0  # half width at the bottom of the torso; the lower tier tapers out to TORSO_HW


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
    s = fuse(s, *adds)
    s = s.intersect(outer)
    for x, y in _torso_top_pts():
        tools.append(cyl((x, y, sz + 37), "z", P.M3, 30))
        tools.append(cyl((x, y, z1 - 1.2), "z", P.M3_HEAD, 3))
    for y, z in _shell_back_pts(sz):
        tools.append(cyl_between("x", (y, z), TX0 - 1, TX0 + 5, P.M3))
    # shoulder ports
    for sy in (1, -1):
        tools.append(cyl_between("y", (P.SHOULDER_X, sz), sy * (P.TORSO_HW - 10), sy * (P.TORSO_HW + 5), 64))
    # tongue notch and cable gland at the back
    tools.append(box(TX0 - 1, TX0 + 6, -31, 31, z0 - 1, sz - 148))
    # neck port
    tools.append(cyl((NECK_X, 0, z1 - 10), "z", 36, 20))
    # chest light slot and speaker grille on the front
    tools.append(rrect(TX1, 0, sz - 64, sz - 58, 12, 150, 3))
    for r, n in ((0, 1), (7, 6), (14, 12), (21, 18)):
        for i in range(n):
            a = 2 * math.pi * i / n
            tools.append(cyl_between("x", (r * math.cos(a), sz - 156 + r * math.sin(a)), TX1 - 6, TX1 + 1, 3.2))
    # back vents for the Jetson
    for i in range(6):
        for sy in (1, -1):
            y = sy * (40 + 7 * i)
            tools.append(box(TX0 - 1, TX0 + 5, y - 1.8, y + 1.8, sz - 210, sz - 130))
    hw("M3x10 socket head", 2 * len(_torso_seam_pairs(sz)) + len(_shell_back_pts(sz)) + len(_torso_top_pts()))
    hw("M3 heat-set insert", 2 * len(_torso_seam_pairs(sz)))
    return cut(s, *tools)


def torso_joiners(sz=S0) -> list[cq.Shape]:
    return [tab_at(a, b, n) for a, b, n in _torso_seam_pairs(sz)]


def torso_parts() -> list[Part]:
    out = [Part("carriage", carriage(), "lift", "mast", color="frame", rot=(0, 0, 0),
                note="Four LM12UU press in. T8 nut from below. Tongue nuts drop into the slots.")]
    out.append(Part("torso_back_plate", back_plate(), "lift", "torso", color="frame",
                    note="Takes the lift tongue, the yokes and the Jetson grid."))
    out.append(Part("yoke_l", yoke(1), "lift", "torso", color="frame", rot=(90, 0, 0),
                    note="Holds the left DM-J4340 (J1). Prints on its centre face, cup up. 5 walls, 30% infill."))
    out.append(Part("yoke_r", yoke(-1), "lift", "torso", color="frame", rot=(-90, 0, 0), note="Mirror of yoke_l."))
    out.append(Part("neck_mount", neck_mount(), "lift", "torso", color="frame", note="Pan servo cradle, bridges the yokes."))
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
    for sy in (1, -1):
        out.append(Bought(f"rod_{'l' if sy > 0 else 'r'}", cyl((P.ROD_X, sy * P.ROD_Y, P.ROD_Z0), "z", P.ROD_D, P.ROD_LEN),
                          "base", "mast", "metal", 888, "rod", look="chrome"))
    out.append(Bought("leadscrew", cyl((P.SCREW_X, 0, P.SCREW_Z1 - P.SCREW_LEN), "z", 8, P.SCREW_LEN), "base", "mast", "metal", 350, "screw",
                      look="steel"))
    out += V.boughts("lift_motor", V.place(V.nema17(), (P.SCREW_X, 0, P.NEMA_FACE_Z)), "base", "mast", "actuator", P.NEMA_MASS, "nema")
    out += V.boughts("coupler", V.place(V.coupler(), (P.SCREW_X, 0, P.NEMA_FACE_Z - 27)), "base", "mast", "metal", 20, "coupler")
    lo_c = sz - P.CARRIAGE_BELOW + 4 + P.LM12_LEN / 2
    for sy in (1, -1):
        for zc in (lo_c, lo_c + P.BEARING_SPAN):
            out += V.boughts(f"lm12_{'l' if sy > 0 else 'r'}_{int(zc)}", V.place(V.lm12uu(), (P.ROD_X, sy * P.ROD_Y, zc)),
                             "lift", "mast", "metal", 60, "lm12")
    nz = sz - P.CARRIAGE_BELOW
    out.append(Bought("t8_nut", cut(fuse(cyl((P.SCREW_X, 0, nz), "z", 22, 3.5), cyl((P.SCREW_X, 0, nz - 11.5), "z", 10.2, 11.6)),
                                    cyl((P.SCREW_X, 0, nz - 20), "z", 8.2, 40)),
                      "lift", "mast", "metal", 30, "t8nut", look="brass"))
    for sy, j in ((1, "l"), (-1, "r")):
        pcs = V.place(V.damiao("dm4340"), (P.SHOULDER_X, sy * P.J1_FACE_Y, sz), xdir=(1, 0, 0), zdir=(0, sy, 0))
        out += V.boughts(f"j1_{j}", pcs, "lift", "torso", "actuator", P.DM4340_MASS, "dm4340")
    jx0 = BP_X1 + 4
    out += V.boughts("jetson", V.place(V.jetson(), (jx0, 0, sz - 165), xdir=(0, 1, 0), zdir=(1, 0, 0)), "lift", "torso", "electronics", 280, "jetson")
    for name, (x, y, z), pcs, m, key in (
        ("usb_hub", (110 - 12.5, -95, sz - 170), V.usb_board(70, 50, 25, ports=4), 60, "usbhub"),
        ("can_l", (100 - 10, 80, sz - 170), V.usb_board(30, 50, 20, ports=1), 25, "usbcan"),
        ("can_r", (100 - 10, 80, sz - 210), V.usb_board(30, 50, 20, ports=1), 25, "usbcan"),
        ("servo_bus", (150 - 10, 60, sz - 120), V.usb_board(40, 65, 20, ports=2), 25, "busadapter"),
        ("servo_bus_r", (150 - 10, -60, sz - 120), V.usb_board(40, 65, 20, ports=2), 25, "busadapter"),
    ):
        out += V.boughts(name, V.place(pcs, (x, y, z), xdir=(0, 0, 1), zdir=(1, 0, 0)), "lift", "torso", "electronics", m, key)
    out += V.boughts("speaker", V.place(V.speaker(), (TX1 - 10, 0, sz - 156), xdir=(0, 1, 0), zdir=(1, 0, 0)), "lift", "torso", "electronics", 40, "speaker")
    out += V.boughts("pan_servo", V.place(V.sts3215(), (NECK_X, 0, sz + 47)), "lift", "torso", "actuator", P.STS_MASS, "sts3215")
    return out
