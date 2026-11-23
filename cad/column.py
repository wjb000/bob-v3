"""Four-stage telescoping column, Nori A3 / Sunday Memo style.

The outer tube is bolted to the pan. A NEMA 17 in the base turns a short
TR8×2 that drives the middle tube. Two GT2 cascades make the tubes above
travel further: belt A (pulley on the middle) drives the upper tube at
2× the screw, belt B (pulley on the upper) drives the inner tube at 3×.
The torso sits on a cap on the inner tube. Collapsed, that cap is low
enough for the hands to reach the floor. Extended, travel is 558 mm.

Links, all sliding on the base (meshes are drawn in the world frame):
  outer  -> base
  mid    -> lift_mid    (slide 1/3 × lift)
  upper  -> lift_upper  (slide 2/3 × lift)
  inner  -> lift        (slide 1 × lift)
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


def _flat_dogs(d, z0, z1, outward):
    """Four stop blocks on the flats, beside the slide pads (pads are only 10 mm wide at centre).

    An outward dog grows off the tube. An inward dog grows into the bore from the wall.
    They overlap in radius and are placed so they meet with about 1 mm of axial gap at full stroke.
    """
    depth = 3.3
    # On the flat, beside the 10 mm pad. The inner tube's flat only runs out to about 13 mm.
    a, b = -12.0, -6.0
    cx = P.COL_X
    face = d / 2 if outward else d / 2 - P.COL_WALL
    lo, hi = (face - 0.7, face + depth) if outward else (face - depth, face + 0.7)
    return [
        box(cx + lo, cx + hi, a, b, z0, z1),
        box(cx - hi, cx - lo, a, b, z0, z1),
        box(cx + a, cx + b, lo, hi, z0, z1),
        box(cx + a, cx + b, -hi, -lo, z0, z1),
    ]


def _tie_bar(d, z):
    """Shallow zip-tie bridge on the rear inner wall. 2.4 mm deep, so it stays in the slide gap."""
    face = d / 2 - P.COL_WALL
    cx = P.COL_X
    bar = box(cx - face - 0.8, cx - face + 2.4, 8, 22, z, z + 8)
    hole = cyl_between("x", (15, z + 4), cx - face - 2, cx - face + 4, 3.2)
    return bar, hole


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
        # Cable lane on the rear wall, +y side, matching the trough and the mid-tube notch.
        # The homing pad stays on the centre of the same wall.
        tools.append(box(P.COL_X - P.COL_OUTER_D / 2 - 2, P.COL_X - P.COL_OUTER_D / 2 + P.COL_WALL + 2,
                         14, 30, z0 + 20, z0 + 70))
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
        adds.extend(_flat_dogs(P.COL_OUTER_D, z1 - 19, z1 - 13, outward=False))
        # Slot on the front flat, beside the pad. The rear flat is the yoke web.
        tools.append(box(9, 17, P.COL_X + P.COL_OUTER_D / 2 - P.COL_WALL - 0.3, P.COL_X + P.COL_OUTER_D / 2 + 2,
                         z1 - 36, z1 - 26))
        hw("Micro limit switch (KW12, top of travel)", 1)
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
        # Open at the bottom, beside the rear pad, so the rising wall cannot shear the
        # umbilical against the fixed window in the outer tube.
        tools.append(box(P.COL_X - P.COL_MID_D / 2 - 2, P.COL_X - P.COL_MID_D / 2 + P.COL_WALL + 6,
                         14, 30, z0 - 1, z0 + 80))
        hw("TR8x2 brass flange nut", 1)
        hw("M3x10 thread-forming (T8 nut)", 4)
        # Outward dogs and the top-limit flag. At full stroke these sit just under the outer stops.
        dz = P.COL_Z0 + P.COL_OUTER_LEN - 30 - P.STAGE_TRAVEL - P.COL_MID_Z0  # 5 mm under the outer stops at full stroke
        adds.extend(_flat_dogs(P.COL_MID_D, z0 + dz, z0 + dz + 6, outward=True))
        face = P.COL_MID_D / 2
        adds.append(box(9, 17, face - 0.8, face + 2.4, z0 + dz - 6, z0 + dz))
        bar, hole = _tie_bar(P.COL_MID_D, z0 + 96)
        adds.append(bar)
        tools.append(hole)
        hw("4 in zip tie (column umbilical)", 1)
    if i == n - 1:
        adds.extend(_pads_inside(P.COL_MID_D, z1 - 8 - PAD_L, z1 - 8))
        for sy in (1, -1):
            # Between the upper slide pads (out to 34 mm) and the outer belt anchors (in to 42 mm).
            adds.append(cbox(P.COL_X, sy * (P.COL_MID_D / 2 - 2.5), z1 - 16, 14, 4, 14))
            tools.append(cyl_between("y", (P.COL_X, z1 - 16), sy * (P.COL_MID_D / 2 - 12), sy * (P.COL_MID_D / 2 + 4), 5.2))
            # Belt B fixed end, in the wall, below the inner slide pads.
            adds.append(_wall_boss(P.COL_MID_D, z1 - 78, z1 - 66, P.COL_X, sy * (P.COL_MID_D / 2 - 2)))
            tools.append(cyl_between("y", (P.COL_X, z1 - 72),
                                     sy * (P.COL_MID_D / 2 - 14), sy * (P.COL_MID_D / 2 + 2), 3.4))
        hw("GT2 20T pulley, 5 mm bore", 2)
        hw("M5x20 shoulder screw (pulley)", 2)
        hw("M3x10 socket head (belt anchor)", 2)
        k = (P.COL_MID_Z0 + P.COL_MID_LEN) - (P.COL_UPPER_Z0 + 16 + P.STAGE_TRAVEL)  # 4 mm over the upper dogs at full stroke
        adds.extend(_flat_dogs(P.COL_MID_D, z1 - k, z1 - k + 6, outward=False))
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.COL_X, 0, min(z0, P.NUT_Z - 8), z1 + 1, P.COL_MID_D + 20, P.COL_MID_D + 20, P.COL_MID_R + 8))
    return cut(s, *tools)


# ---------------------------------------------------------------- upper (2× the screw)

def upper_segment(i, z0, z1, n) -> cq.Shape:
    s = _tube(P.COL_UPPER_D, P.COL_UPPER_R, z0, z1)
    adds, tools = _splice_tools(P.COL_UPPER_D, z0, z1, i, n, insert_top=True)
    if i == 0:
        adds.extend(_pads_outside(P.COL_UPPER_D, z0 + 8, z0 + 8 + PAD_L))
        for sy in (1, -1):
            # Stay outside the inner tube's pads (they reach y = 25) and inside the mid bore.
            adds.append(cbox(P.COL_X, sy * (P.COL_UPPER_D / 2 - 1), z0 + 20, 12, 8, 12))
            tools.append(cyl_between("y", (P.COL_X, z0 + 20),
                                     sy * (P.COL_UPPER_D / 2 - 10), sy * (P.COL_UPPER_D / 2 + 2), 3.4))
        hw("M3x10 socket head (belt clamp)", 2)
        adds.extend(_flat_dogs(P.COL_UPPER_D, z0 + 6, z0 + 12, outward=True))
        bar, hole = _tie_bar(P.COL_UPPER_D, z0 + 78)
        adds.append(bar)
        tools.append(hole)
        hw("4 in zip tie (column umbilical)", 1)
    if i == n - 1:
        adds.extend(_pads_inside(P.COL_UPPER_D, z1 - 8 - PAD_L, z1 - 8))
        for sy in (1, -1):
            # Inner pads reach y = 25. The mid's inside pads start at y = 35.
            adds.append(cbox(P.COL_X, sy * (P.COL_UPPER_D / 2 - 2.5), z1 - 16, 14, 4, 14))
            tools.append(cyl_between("y", (P.COL_X, z1 - 16),
                                     sy * (P.COL_UPPER_D / 2 - 12), sy * (P.COL_UPPER_D / 2 + 4), 5.2))
        hw("GT2 20T pulley, 5 mm bore", 2)
        hw("M5x20 shoulder screw (pulley)", 2)
        k = (P.COL_UPPER_Z0 + P.COL_UPPER_LEN) - (P.COL_INNER_Z0 + 14 + P.STAGE_TRAVEL)  # 3 mm over the inner dogs at full stroke
        adds.extend(_flat_dogs(P.COL_UPPER_D, z1 - k, z1 - k + 6, outward=False))
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.COL_X, 0, z0, z1 + 1, P.COL_UPPER_D + 20, P.COL_UPPER_D + 20, P.COL_UPPER_R + 8))
    return cut(s, *tools)


# ---------------------------------------------------------------- inner

def inner_segment(i, z0, z1, n) -> cq.Shape:
    s = _tube(P.COL_INNER_D, P.COL_INNER_R, z0, z1)
    adds, tools = _splice_tools(P.COL_INNER_D, z0, z1, i, n, insert_top=True, cap_top=True)
    if i == 0:
        adds.extend(_pads_outside(P.COL_INNER_D, z0 + 8, z0 + 8 + PAD_L))
        for sy in (1, -1):
            # On the tube wall, above the upper tube's belt clamp, so the two clamps do not meet.
            adds.append(cbox(P.COL_X, sy * (P.COL_INNER_D / 2 - 5), z0 + 44, 12, 8, 12))
            tools.append(cyl_between("y", (P.COL_X, z0 + 44),
                                     sy * (P.COL_INNER_D / 2 - 14), sy * (P.COL_INNER_D / 2 - 1), 3.4))
        # Strain-relief bar inside the bore, above the pads, for a zip tie on the sleeve.
        face = P.COL_INNER_D / 2 - P.COL_WALL
        adds.append(box(P.COL_X - face - 1.2, P.COL_X - face + 8, 8, 22, z0 + 64, z0 + 72))
        tools.append(cyl_between("x", (15, z0 + 68), P.COL_X - face - 2, P.COL_X - face + 10, 4.2))
        hw("M3x10 socket head (belt clamp)", 2)
        hw("4 in zip tie (column umbilical)", 1)
        adds.extend(_flat_dogs(P.COL_INNER_D, z0 + 5, z0 + 11, outward=True))
    s = fuse(s, *adds)
    s = s.intersect(rrect(P.COL_X, 0, z0, z1 + 1, P.COL_INNER_D + 20, P.COL_INNER_D + 20, P.COL_INNER_R + 8))
    return cut(s, *tools)


def _cap_bolts():
    b = P.CAP_BOLT
    return [(P.COL_X + sx * b, sy * b) for sx in (1, -1) for sy in (1, -1)]


def inner_cap() -> cq.Shape:
    """Plate on the inner tube. The torso shelf sits on this face and bolts down.

    The plate stays 76 mm, wider than the 46 mm tube, so the M5 square at ±22 mm
    still lands in material. The Ø18 hole is the umbilical exit, with zip-tie holes beside it.
    """
    z0 = P.COL_INNER_TOP0
    z1 = z0 + 8.0
    plate = rrect(P.COL_X, 0, z0, z1, 76, 76, 20)
    tools = [cyl((P.COL_X, 0, z0 - 1), "z", 18, 14)]
    for x, y in _boss_pts(P.COL_INNER_D):
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 12))
        tools.append(cyl((x, y, z1 - 3), "z", P.M3_HEAD, 4))
    for x, y in _cap_bolts():
        tools.append(cyl((x, y, z0 - 1), "z", P.M5, 14))
        tools.append(cyl((x, y, z0 - 1), "z", 9.2, 4.5))  # nut pocket under the plate
    for y in (-14.0, 14.0):
        tools.append(cyl((P.COL_X, y, z0 - 1), "z", 4.2, 14))
    hw("M3x12 socket head", 4)
    hw("M5x16 socket head + nut (torso to cap)", 4)
    hw("4 in zip tie (column umbilical)", 1)
    return cut(plate, *tools)


# ---------------------------------------------------------------- parts / bought

def parts() -> list[Part]:
    out = []
    segs = P.col_segments(P.COL_Z0, P.COL_OUTER_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "Foot flange, motor pedestal, homing pad." if i == 0 else (
            "Top of the outer tube. Slide pads and belt anchors." if i == len(segs) - 1 else "Prints standing. Inserts in the top bosses.")
        out.append(Part(f"col_outer_{i}", outer_segment(i, z0, z1, len(segs)), "base", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=40, note=note))
    segs = P.col_segments(P.COL_MID_Z0, P.COL_MID_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "T8 nut pocket, cable notch, outer slide pads." if i == 0 else (
            "Belt A pulleys, belt B anchors, inner slide pads." if i == len(segs) - 1 else "Prints standing. Inserts in the top bosses.")
        out.append(Part(f"col_mid_{i}", mid_segment(i, z0, z1, len(segs)), "lift_mid", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=40, note=note))
    segs = P.col_segments(P.COL_UPPER_Z0, P.COL_UPPER_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "Belt A clamps and outer slide pads." if i == 0 else (
            "Belt B pulleys and inner slide pads." if i == len(segs) - 1 else "Prints standing. Inserts in the top bosses.")
        out.append(Part(f"col_upper_{i}", upper_segment(i, z0, z1, len(segs)), "lift_upper", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=40, note=note))
    segs = P.col_segments(P.COL_INNER_Z0, P.COL_INNER_LEN)
    for i, (z0, z1) in enumerate(segs):
        note = "Belt B clamps, sleeve tie, outer slide pads." if i == 0 else "Prints standing. Inserts in the top bosses."
        out.append(Part(f"col_inner_{i}", inner_segment(i, z0, z1, len(segs)), "lift", "mast", color="shell", rot=(0, 0, 0),
                        walls=5, infill=40, note=note))
    out.append(Part("col_cap", inner_cap(), "lift", "mast", color="dark", rot=(180, 0, 0), walls=5, infill=30,
                    note="Sits on the inner tube. Umbilical exits the Ø18 hole. The torso shelf bolts down, 4 × M5."))
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
    # Belt A: pulley on the middle tube, envelope in the outer/mid gap. Drives the upper tube at 2×.
    z_a = P.COL_MID_Z0 + P.COL_MID_LEN - 16
    for sy, s in ((1, "l"), (-1, "r")):
        out.append(Bought(f"gt2_pulley_a_{s}",
                          cyl_between("y", (P.COL_X, z_a), sy * (P.COL_MID_D / 2 - 8), sy * (P.COL_MID_D / 2 + 4), 16),
                          "lift_mid", "mast", "metal", 8, "gt2pulley", look="alu"))
        belt = box(P.COL_X - 1.5, P.COL_X + 1.5,
                   sy * (P.COL_MID_D / 2 + 2), sy * (P.COL_MID_D / 2 + 5),
                   P.COL_Z0 + 20, z_a)
        out.append(Bought(f"gt2_belt_a_{s}", belt, "lift_mid", "mast", "metal", 8, "gt2belt", look="black"))
    # Belt B: pulley on the upper tube, envelope in the mid/upper gap. Drives the inner tube at 3×.
    z_b = P.COL_UPPER_Z0 + P.COL_UPPER_LEN - 16
    for sy, s in ((1, "l"), (-1, "r")):
        out.append(Bought(f"gt2_pulley_b_{s}",
                          cyl_between("y", (P.COL_X, z_b), sy * (P.COL_UPPER_D / 2 - 8), sy * (P.COL_UPPER_D / 2 + 4), 16),
                          "lift_upper", "mast", "metal", 8, "gt2pulley", look="alu"))
        belt = box(P.COL_X - 1.5, P.COL_X + 1.5,
                   sy * (P.COL_UPPER_D / 2 + 2), sy * (P.COL_UPPER_D / 2 + 5),
                   P.COL_MID_Z0 + 30, z_b)
        out.append(Bought(f"gt2_belt_b_{s}", belt, "lift_upper", "mast", "metal", 8, "gt2belt", look="black"))
    # Top-of-travel KW12 on the front of the outer tube. The torso has a groove there.
    # The leaf stops about 1 mm short of the mid-tube flag at full stroke.
    z1 = P.COL_Z0 + P.COL_OUTER_LEN
    face = P.COL_OUTER_D / 2
    body = box(8, 18, face + 1.6, face + 8.0, z1 - 40, z1 - 24)
    leaf = box(10, 16, face - P.COL_WALL - 0.4, face + 1.6, z1 - 34, z1 - 28)
    out.append(Bought("limit_top", fuse(body, leaf), "base", "mast", "electronics", 4, "kw12", look="black"))
    return out
