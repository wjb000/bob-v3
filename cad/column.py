"""Three-stage telescoping column, Nori A3 / Sunday Memo style.

The outer tube is bolted to the pan. A NEMA 17 in the base turns a short
TR8×2 that drives the middle tube. A GT2 belt on each side, anchored on
the outer tube and the inner tube and running over a pulley on the middle
tube, makes the inner tube travel twice as far. The torso sits on a cap
on the inner tube, so the column grows out of the base instead of a
carriage riding an exposed mast.

Links
  outer  -> base
  mid    -> lift_mid   (slide 0.5 × lift)
  inner  -> lift       (slide 1.0 × lift)
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import Bought, Part, box, cbox, cut, cyl, cyl_between, fuse, hw, rrect, rrect_shell

S0 = P.SHOULDER_Z0
BOSS_H = 12.0
PAD_L, PAD_W = 50.0, 10.0


def _tube(d, r, z0, z1, wall=P.COL_WALL):
    return rrect_shell(P.COL_X, 0, z0, z1, d, d, r, wall, open_top=True, open_bot=True)


def _boss_pts(d):
    """Four splice-boss centres, in the middle of the wall of a tube of outside size d."""
    h = d / 2 - 2.0
    return [(P.COL_X + h, 0), (P.COL_X - h, 0), (P.COL_X, h), (P.COL_X, -h)]


def _pads_inside(d, z0, z1):
    """Four pads on the inner flats, overlapping the wall 1 mm so they fuse."""
    face = d / 2 - P.COL_WALL
    t, w, o = P.COL_PAD, PAD_W, 1.2
    cx = P.COL_X
    return [
        box(cx + face - t, cx + face + o, -w / 2, w / 2, z0, z1),
        box(cx - face - o, cx - face + t, -w / 2, w / 2, z0, z1),
        box(cx - w / 2, cx + w / 2, face - t, face + o, z0, z1),
        box(cx - w / 2, cx + w / 2, -face - o, -face + t, z0, z1),
    ]


def _pads_outside(d, z0, z1):
    """Four pads on the outer flats, overlapping the wall 1 mm so they fuse."""
    face = d / 2
    t, w, o = P.COL_PAD, PAD_W, 1.2
    cx = P.COL_X
    return [
        box(cx + face - o, cx + face + t, -w / 2, w / 2, z0, z1),
        box(cx - face - t, cx - face + o, -w / 2, w / 2, z0, z1),
        box(cx - w / 2, cx + w / 2, face - o, face + t, z0, z1),
        box(cx - w / 2, cx + w / 2, -face - t, -face + o, z0, z1),
    ]


def _wall_boss(d, z0, z1, x, y):
    """A 16 x 12 mm block in the wall, only 2 mm into the cavity so nested tubes still fit."""
    w = 16.0
    face_out = d / 2
    face_in = d / 2 - P.COL_WALL - 2.0
    cx = P.COL_X
    if abs(x - cx) > abs(y):
        sx = 1.0 if x > cx else -1.0
        return box(cx + sx * face_in, cx + sx * (face_out + 0.3), y - w / 2, y + w / 2, z0, z1)
    sy = 1.0 if y > 0 else -1.0
    return box(x - w / 2, x + w / 2, sy * face_in, sy * (face_out + 0.3), z0, z1)


def _splice_tools(d, z0, z1, i, n, insert_top, cap_top=False):
    """Bosses and holes that stack two segments. cap_top keeps inserts on the last piece for the inner cap."""
    adds, tools = [], []
    pts = _boss_pts(d)
    top_is_last = i == n - 1 and not cap_top
    for x, y in pts:
        if not top_is_last:
            adds.append(_wall_boss(d, z1 - BOSS_H, z1, x, y))
            if insert_top:
                tools.append(cyl((x, y, z1 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
            else:
                tools.append(cyl((x, y, z1 - BOSS_H - 1), "z", P.M3, BOSS_H + 2))
                tools.append(cyl((x, y, z1 - BOSS_H - 1), "z", P.M3_HEAD, BOSS_H - 5))
        if i > 0:
            adds.append(_wall_boss(d, z0, z0 + BOSS_H, x, y))
            tools.append(cyl((x, y, z0 - 1), "z", P.M3, BOSS_H + 2))
            tools.append(cyl((x, y, z0 + 7), "z", P.M3_HEAD, BOSS_H))
    hw("M3 heat-set insert", 0 if top_is_last else 4)
    hw("M3x14 socket head", 0 if i == 0 else 4)
    return adds, tools


# ---------------------------------------------------------------- outer (fixed to the pan)

def outer_segment(i, z0, z1, n) -> cq.Shape:
    s = _tube(P.COL_OUTER_D, P.COL_OUTER_R, z0, z1)
    adds, tools = _splice_tools(P.COL_OUTER_D, z0, z1, i, n, insert_top=True)
    if i == 0:
        f = 12.0
        flange = rrect(P.COL_X, 0, z0, z0 + 6, P.COL_OUTER_D + 2 * f, P.COL_OUTER_D + 2 * f, P.COL_OUTER_R + f)
        flange = flange.cut(rrect(P.COL_X, 0, z0 - 1, z0 + 8, P.COL_OUTER_D - 2, P.COL_OUTER_D - 2, P.COL_OUTER_R - 1))
        adds.append(flange)
        # motor pedestal, overlapping the inner wall so it fuses
        ped_d = P.COL_OUTER_D - 2 * P.COL_WALL + 2.0
        ped = rrect(P.COL_X, 0, z0, P.NEMA_FACE_Z - P.NEMA_LEN, ped_d, ped_d, max(P.COL_OUTER_R - P.COL_WALL, 2))
        adds.append(ped)
        tools.append(cyl((P.SCREW_X, 0, z0 - 1), "z", P.NEMA_PILOT + 0.6, 80))
        for dx in (-P.NEMA_BOLT / 2, P.NEMA_BOLT / 2):
            for dy in (-P.NEMA_BOLT / 2, P.NEMA_BOLT / 2):
                tools.append(cyl((P.SCREW_X + dx, dy, z0 - 1), "z", P.M3, 20))
                tools.append(cyl((P.SCREW_X + dx, dy, z0 + 4), "z", P.M3_HEAD, 16))
        from base import PAN_PTS
        for x, y in PAN_PTS["col"]:
            tools.append(cyl((x, y, z0 - 1), "z", P.M3, 10))
        # cable / belt exits at the back
        tools.append(box(P.COL_X - P.COL_OUTER_D / 2 - 2, P.COL_X - P.COL_OUTER_D / 2 + P.COL_WALL + 2,
                         -16, 16, z0 + 14, z0 + 70))
        # homing pad on the back inner wall; 2 mm into the cavity so the mid tube still fits
        face = P.COL_X - (P.COL_OUTER_D / 2 - P.COL_WALL)
        adds.append(box(face - 0.2, face + 1.0, -12, 12, z0 + 80, z0 + 100))
        for dz in (-4.75, 4.75):
            tools.append(cyl_between("x", (0, z0 + 90 + dz), face - 3, face + 3, 1.9))
        hw("M3x10 socket head", len(PAN_PTS["col"]))
        hw("M3x8 socket head (NEMA)", 4)
        hw("Micro limit switch (KW12, roller)", 1)
    if i == n - 1:
        adds.extend(_pads_inside(P.COL_OUTER_D, z1 - 8 - PAD_L, z1 - 8))
        for sy in (1, -1):
            adds.append(cbox(P.COL_X, sy * (P.COL_OUTER_D / 2 - 2), z1 - 18, 16, 12, 12))
            tools.append(cyl_between("y", (P.COL_X, z1 - 18), sy * (P.COL_OUTER_D / 2 - 14), sy * (P.COL_OUTER_D / 2 + 2), 3.4))
        hw("M3x10 socket head (belt anchor)", 2)
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.COL_X, 0, z0, z1 + 1, P.COL_OUTER_D + 40, P.COL_OUTER_D + 40, P.COL_OUTER_R + 16))
    return cut(s, *tools)


# ---------------------------------------------------------------- middle

def mid_segment(i, z0, z1, n) -> cq.Shape:
    s = _tube(P.COL_MID_D, P.COL_MID_R, z0, z1)
    adds, tools = _splice_tools(P.COL_MID_D, z0, z1, i, n, insert_top=True)
    if i == 0:
        # T8 nut pocket: a bridge across the inside, overlapping the walls
        bridge = rrect(P.COL_X, 0, P.NUT_Z - 6, P.NUT_Z + 8, P.COL_MID_D - 2, 28, 6)
        adds.append(bridge)
        tools.append(cyl((P.SCREW_X, 0, P.NUT_Z - 20), "z", 11, 50))
        tools.append(cyl((P.SCREW_X, 0, P.NUT_Z - 1), "z", P.T8_FLANGE + 0.4, 5))
        for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
            tools.append(cyl((P.SCREW_X + P.T8_PCD / 2 * math.cos(a), P.T8_PCD / 2 * math.sin(a), P.NUT_Z - 1), "z", 2.6, 12))
        adds.extend(_pads_outside(P.COL_MID_D, z0 + 8, z0 + 8 + PAD_L))
        hw("TR8x2 brass flange nut", 1)
        hw("M3x10 thread-forming (T8 nut)", 4)
    if i == n - 1:
        adds.extend(_pads_inside(P.COL_MID_D, z1 - 8 - PAD_L, z1 - 8))
        for sy in (1, -1):
            adds.append(cbox(P.COL_X, sy * (P.COL_MID_D / 2 - 5), z1 - 16, 14, 8, 14))
            tools.append(cyl_between("y", (P.COL_X, z1 - 16), sy * (P.COL_MID_D / 2 - 12), sy * (P.COL_MID_D / 2 + 4), 5.2))
        hw("GT2 20T pulley, 5 mm bore", 2)
        hw("M5x20 shoulder screw (pulley)", 2)
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.COL_X, 0, min(z0, P.NUT_Z - 8), z1 + 1, P.COL_MID_D + 20, P.COL_MID_D + 20, P.COL_MID_R + 8))
    return cut(s, *tools)


# ---------------------------------------------------------------- inner

def inner_segment(i, z0, z1, n) -> cq.Shape:
    s = _tube(P.COL_INNER_D, P.COL_INNER_R, z0, z1)
    adds, tools = _splice_tools(P.COL_INNER_D, z0, z1, i, n, insert_top=True, cap_top=True)
    if i == 0:
        adds.extend(_pads_outside(P.COL_INNER_D, z0 + 8, z0 + 8 + PAD_L))
        for sy in (1, -1):
            adds.append(cbox(P.COL_X, sy * (P.COL_INNER_D / 2 - 2), z0 + 20, 14, 10, 12))
            tools.append(cyl_between("y", (P.COL_X, z0 + 20), sy * (P.COL_INNER_D / 2 - 12), sy * (P.COL_INNER_D / 2 + 2), 3.4))
        hw("M3x10 socket head (belt clamp)", 2)
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.COL_X, 0, z0, z1 + 1, P.COL_INNER_D + 20, P.COL_INNER_D + 20, P.COL_INNER_R + 8))
    return cut(s, *tools)


def inner_cap() -> cq.Shape:
    """Plate on the inner tube. A front lip takes the torso back plate on four M5."""
    z0 = P.COL_INNER_TOP0
    z1 = z0 + 8.0
    plate = rrect(P.COL_X, 0, z0, z1, P.COL_INNER_D + 8, P.COL_INNER_D + 8, P.COL_INNER_R + 2)
    x0 = P.COL_X + P.COL_OUTER_D / 2 + 2
    x1 = P.TORSO_X0 + 4.0  # meets the back-plate face; screws continue through the plate
    bridge = box(P.COL_X, x1, -24, 24, z0, z1)
    lip_z0 = min(S0 - 58.0, P.COL_TOP0 - 40.0)
    lip = box(x0, x1, -30, 30, lip_z0, z1)
    s = fuse(plate, bridge, lip)
    tools = []
    for x, y in _boss_pts(P.COL_INNER_D):
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 12))
        tools.append(cyl((x, y, z1 - 3), "z", P.M3_HEAD, 4))
    # M5 through the lip into the back plate
    for y in (-16.0, 16.0):
        for zb in (S0 - 52.0, S0 - 36.0):
            tools.append(cyl_between("x", (y, zb), x0 - 1, x1 + 1, P.M5))
            tools.append(cyl_between("x", (y, zb), x1 - 3, x1 + 1, 9.5))
    hw("M3x12 socket head", 4)
    hw("M5x20 socket head + nut (torso)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- parts / bought

def parts() -> list[Part]:
    out = []
    segs = P.col_segments(P.COL_Z0, P.COL_OUTER_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "Foot flange, motor pedestal, homing pad." if i == 0 else (
            "Top of the outer tube. Slide pads and belt anchors." if i == len(segs) - 1 else "Prints standing. Inserts in the top bosses.")
        out.append(Part(f"col_outer_{i}", outer_segment(i, z0, z1, len(segs)), "base", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=30, note=note))
    segs = P.col_segments(P.COL_MID_Z0, P.COL_OUTER_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "T8 nut pocket and outer slide pads." if i == 0 else (
            "Pulleys and inner slide pads." if i == len(segs) - 1 else "Prints standing. Inserts in the top bosses.")
        out.append(Part(f"col_mid_{i}", mid_segment(i, z0, z1, len(segs)), "lift_mid", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=30, note=note))
    segs = P.col_segments(P.COL_INNER_Z0, P.COL_INNER_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "Belt clamps and outer slide pads." if i == 0 else "Prints standing. Inserts in the top bosses."
        out.append(Part(f"col_inner_{i}", inner_segment(i, z0, z1, len(segs)), "lift", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=30, note=note))
    out.append(Part("col_cap", inner_cap(), "lift", "mast", color="dark", rot=(180, 0, 0), walls=5, infill=30,
                    note="Sits on the inner tube. Front lip takes the torso back plate, 4 × M5."))
    return out


def bought() -> list[Bought]:
    import vendor as V

    out = []
    # motor: face at NEMA_FACE_Z, body toward -z (down onto the pedestal), shaft +z
    out += V.boughts("lift_motor", V.place(V.nema17(), (P.SCREW_X, 0, P.NEMA_FACE_Z), zdir=(0, 0, -1)),
                     "base", "mast", "actuator", P.NEMA_MASS, "nema")
    out += V.boughts("coupler", V.place(V.coupler(), (P.SCREW_X, 0, P.NEMA_FACE_Z + 1), zdir=(0, 0, 1)),
                     "base", "mast", "metal", 20, "coupler")
    out.append(Bought("leadscrew", cyl((P.SCREW_X, 0, P.SCREW_Z0), "z", P.T8_D, P.SCREW_LEN),
                      "base", "mast", "metal", 160, "screw", look="steel"))
    nz = P.NUT_Z
    out.append(Bought("t8_nut", cut(fuse(cyl((P.SCREW_X, 0, nz), "z", 22, 3.5),
                                         cyl((P.SCREW_X, 0, nz - 11.5), "z", 10.2, 11.6)),
                                    cyl((P.SCREW_X, 0, nz - 20), "z", 8.2, 40)),
                      "lift_mid", "mast", "metal", 30, "t8nut", look="brass"))
    # pulleys on the middle tube top
    z_pul = P.COL_MID_Z0 + P.COL_OUTER_LEN - 16
    for sy, s in ((1, "l"), (-1, "r")):
        out.append(Bought(f"gt2_pulley_{s}",
                          cyl_between("y", (P.COL_X, z_pul), sy * (P.COL_MID_D / 2 - 8), sy * (P.COL_MID_D / 2 + 4), 16),
                          "lift_mid", "mast", "metal", 8, "gt2pulley", look="alu"))
        belt = box(P.COL_X - 1.5, P.COL_X + 1.5,
                   sy * (P.COL_MID_D / 2 + 2), sy * (P.COL_MID_D / 2 + 5),
                   P.COL_Z0 + 20, z_pul)
        out.append(Bought(f"gt2_belt_{s}", belt, "lift_mid", "mast", "metal", 12, "gt2belt", look="black"))
    return out
