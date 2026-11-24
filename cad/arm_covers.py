"""Printed arm covers: they close over the J2, J3 and J4 servos so the arm reads as one finished shell.

Each cover hangs on the link that carries its servo and is shaped so the next link can turn
through its whole range without touching it:

  shoulder cover   link 1   a drum round the J2 roll axis, so the clevis turns inside its own circle
  clevis cover     link 2   a rounded box over the J3 cup, below the shoulder drum's swing
  elbow cover      link 3   a drum round the J4 elbow axis, inside the elbow bridge's swing

Clamshell halves, M3 screws into heat-set inserts in the structural links (no glue). The elbow
halves share the two upper-arm clamshell bolts at the collar and snap together at the bottom.
Cable paths run in next to each joint axis; slots over each servo let it breathe.
Built as the left arm; the right arm is the mirror.
"""
from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import box, cut, cyl_between, fuse, hexagon, hw, rrect, tube_between
from arm import (CV_SCREW_X, CV_SCREW_Z, E, EC_BOLTS, J2_FACE_X, J3_FACE_Z, S, SH_SCREW_X, SH_SCREW_Y, SH_TAB_Z,
                 X0, Y0, _hex_x)
from base import split_one

WALL = 2.4


def _fillet(s, r, sel=None):
    try:
        wp = cq.Workplane().add(s)
        wp = wp.edges(sel) if sel else wp.edges()
        return wp.fillet(r).val()
    except Exception:
        return s


# ---------------------------------------------------------------- shoulder drum (link 1)

SH = dict(ro=57.0, x0=J2_FACE_X - 2.95, x1=42.4, y_rim=125.0, hole=32.0)


def shoulder_cover():
    """Whole drum, before the split. Axis = J2 (x) through (Y0, S)."""
    ro, ri = SH["ro"], SH["ro"] - WALL
    outer = _fillet(cyl_between("x", (Y0, S), SH["x0"], SH["x1"], 2 * ro), 10.0)
    inner = _fillet(cyl_between("x", (Y0, S), SH["x0"] + WALL, SH["x1"] - WALL, 2 * ri), 7.6)
    s = cut(outer, inner)
    # screw bosses down onto the shoulder tabs (top and bottom)
    bosses, tools = [], []
    for x in SH_SCREW_X:
        for sz in (1, -1):
            z_tab = S + sz * (SH_TAB_Z + 0.3)
            bosses.append(cyl_between("z", (x, SH_SCREW_Y), z_tab, S + sz * (ro - 1), 9.0).intersect(outer))
            tools.append(cyl_between("z", (x, SH_SCREW_Y), z_tab - sz, S + sz * (ro + 5), P.M3))
            tools.append(cyl_between("z", (x, SH_SCREW_Y), S + sz * (SH_TAB_Z + 4.5), S + sz * (ro + 5), 6.6))
    s = fuse(s, *bosses)
    tools.append(cyl_between("x", (Y0, S), SH["x0"] - 1, SH["x0"] + WALL + 1, SH["hole"]))  # horn and clevis disc
    tools.append(box(SH["x0"] - 1, SH["x0"] + WALL + 1, Y0 - 9, Y0 + 9, S - SH["hole"] / 2 - 16, S))  # cable notch
    tools.append(box(-500, 500, -500, SH["y_rim"], -500, 2000))  # open to the torso (cable path)
    for k in range(5):  # cooling slots over the servo's far end, top and bottom
        y = Y0 + 14 + 8 * k
        tools.append(box(X0 - 12, X0 + 14, y - 1.5, y + 1.5, S - ro - 5, S - ro + 12))
        tools.append(box(X0 - 12, X0 + 14, y - 1.5, y + 1.5, S + ro - 12, S + ro + 5))
    hw("M3x10 socket head (arm cover)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- clevis box (link 2)

CV = dict(x0=-21.3, x1=42.0, y0=128.0, y1=186.0, z0=J3_FACE_Z - 3.2, z1=350.0, hole=30.0)


def clevis_cover():
    c = CV
    lx, ly = c["x1"] - c["x0"], c["y1"] - c["y0"]
    cx, cy = (c["x0"] + c["x1"]) / 2, (c["y0"] + c["y1"]) / 2
    outer = _fillet(rrect(cx, cy, c["z0"], c["z1"], lx, ly, 12.0), 6.0, ">Z or <Z")
    inner = rrect(cx - 5, cy, c["z0"] + WALL, c["z1"] - WALL, lx - 2 * WALL + 10, ly - 2 * WALL, 12.0 - WALL)
    s = cut(outer, inner)
    pads, tools = [], []
    for z in CV_SCREW_Z:
        for y0, y1, y_face in ((c["y0"] + 1, Y0 - 24 - 0.3, c["y0"]), (Y0 + 24 + 0.3, c["y1"] - 1, c["y1"])):
            pads.append(cyl_between("y", (CV_SCREW_X, z), y0, y1, 9.0))
            ya, yb = (y_face - 1, Y0 - 24) if y_face < Y0 else (Y0 + 24, y_face + 1)
            tools.append(cyl_between("y", (CV_SCREW_X, z), ya, yb, P.M3))
    s = fuse(s, *pads)
    tools.append(cyl_between("z", (X0, Y0), c["z0"] - 1, c["z0"] + WALL + 1, c["hole"]))  # J3 horn
    for k in range(4):  # top slots over the J3 servo
        x = X0 - 18 + 8 * k
        tools.append(box(x - 1.5, x + 1.5, Y0 - 12, Y0 + 12, c["z1"] - WALL - 1, c["z1"] + 1))
    hw("M3x10 socket head (arm cover)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- elbow drum (link 3)

EC = dict(y0=121.6, y1=182.9, ring=29.0, deck=E + 27.5, collar=(E + 27.5, E + 57.0), collar_r=(32.3, 36.0), collar_y1=178.5, side=36.0)


def elbow_cover():
    """Whole elbow drum before the split. Axis = J4 (y) through (X0, E)."""
    c = EC
    # Profile in x-z: flat sides flush with the collar, tapering in to a rounded chin just under the J4
    # cup. Every point stays inside R 57.2 of the elbow axis, and the elbow bridge swings at R 58.
    core = [(-26.0, 60.0), (-26.0, 10.0), (-12.5, -45.5), (12.5, -45.5), (26.0, 10.0), (26.0, 60.0)]
    R_OUT, R_IN = 10.0, 10.0 - WALL

    def prism(r, y0, y1):
        pts = [(X0 + u, E + v) for u, v in core]
        w = cq.Workplane("XZ", origin=(0, y1, 0)).polyline(pts).close().offset2D(r, "arc").extrude(y1 - y0)
        return w.val()

    outer = _fillet(prism(R_OUT, c["y0"], c["y1"]), 4.0, "|X or |Z")
    inner = prism(R_IN, c["y0"] + WALL, c["y1"] - WALL)
    drum = cut(outer, inner, cyl_between("y", (X0, E), c["y1"] - WALL - 1, c["y1"] + 1, 2 * c["ring"]))
    sx = c["side"]
    drum = drum.intersect(box(-500, 500, -500, 500, -500, c["deck"]))
    deck = outer.intersect(box(-500, 500, -500, 500, c["deck"] - WALL, c["deck"]))
    cr0, cr1 = c["collar_r"]
    # The collar stops short of the +y side, where the elbow plate swings past and the third
    # upper-arm bolt keeps its own head and nut.
    collar = tube_between("z", (X0, Y0), c["collar"][0] - 0.01, c["collar"][1], 2 * cr1, 2 * cr0)
    collar = collar.intersect(box(-500, 500, -500, c["collar_y1"], -500, 2000))
    pads, tools = [], []
    for y, z in EC_BOLTS:
        pads.append(cyl_between("x", (y, z), X0 - 25, X0 + 25, 10.0).intersect(
            cyl_between("z", (X0, Y0), c["collar"][0], c["collar"][1], 2 * 37.0)))
        tools.append(cyl_between("x", (y, z), X0 - 40, X0 + 40, P.M3))
        tools.append(_hex_x(X0 + 21, X0 + 26, y, z))
    s = fuse(drum, deck, collar, *pads)
    tools.append(cyl_between("z", (X0, Y0), c["deck"] - WALL - 1, c["collar"][1] + 1, 2 * cr0))  # upper-arm tube
    tools.append(cyl_between("y", (X0, E), c["y0"] - 1, c["y0"] + WALL + 1, 10.0))  # J4 rear shaft
    for k in range(4):  # side slots beside the J4 servo, both faces
        z = E + 14 + 6 * k
        for xa, xb in ((X0 - 70, X0 - sx + 1), (X0 + sx - 1, X0 + 70)):
            tools.append(box(xa, xb, Y0 - 16, Y0 + 16, z - 1.5, z + 1.5))
    hw("M3x50 socket head + nut (upper arm + elbow cover)", 2)
    return cut(s, *tools)


def elbow_halves():
    full = elbow_cover()
    a = split_one(full, box(-500, X0, -500, 500, -500, 2000), "elbow_cover_a")
    b = split_one(full, box(X0, 500, -500, 500, -500, 2000), "elbow_cover_b")
    # two snap tongues on half a (one per flat wall) and their windows in half b
    yi0, yi1 = EC["y0"] + WALL, EC["y1"] - WALL
    tongues = [box(X0 - 6, X0 + 7, yi0, yi0 + 1.4, E - 46, E - 36), box(X0 - 6, X0 + 7, yi1 - 1.4, yi1, E - 52.6, E - 48.9)]
    bumps = [cyl_between("y", (X0 + 4, E - 41), yi0 - 0.8, yi0 + 0.5, 2.6), cyl_between("y", (X0 + 4, E - 50.8), yi1 - 0.5, yi1 + 0.8, 2.6)]
    a = fuse(a, *tongues, *bumps)
    b = cut(b, cyl_between("y", (X0 + 4, E - 41), EC["y0"] - 1, yi0 + 0.1, 3.0),
            cyl_between("y", (X0 + 4, E - 50.8), yi1 - 0.1, EC["y1"] + 1, 3.0))
    return a, b


def parts_left():
    """(name, solid, link, note) for the left arm."""
    sh = shoulder_cover()
    top = split_one(sh, box(-500, 500, -500, 500, S, 2000), "shoulder_cover_top")
    bot = split_one(sh, box(-500, 500, -500, 500, -500, S), "shoulder_cover_bot")
    cv = clevis_cover()
    ca = split_one(cv, box(-500, 500, -500, Y0, -500, 2000), "clevis_cover_a")
    cb = split_one(cv, box(-500, 500, Y0, 500, -500, 2000), "clevis_cover_b")
    ea, eb = elbow_halves()
    n_sh = "Shoulder cover half. Two M3x10 into inserts in the shoulder tab. Prints on the split face."
    n_cv = "Clevis cover half. Two M3x10 into inserts in the clevis span. Prints on the split face."
    n_ec = "Elbow cover half. Clamped by the two upper-arm collar bolts (M3x50 + nut); snaps shut at the bottom. Prints on the split face."
    return [
        ("shoulder_cover_top", top, "link1", n_sh),
        ("shoulder_cover_bot", bot, "link1", n_sh),
        ("clevis_cover_a", ca, "link2", n_cv),
        ("clevis_cover_b", cb, "link2", n_cv),
        ("elbow_cover_a", ea, "link3", n_ec),
        ("elbow_cover_b", eb, "link3", n_ec),
    ]
