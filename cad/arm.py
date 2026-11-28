"""Seven-axis arm (six joints plus the jaw). Built as the left arm; the right is a mirror.

J1 shoulder pitch  DM-J4340  axis Y   (in the torso yoke)
J2 shoulder roll   DM-J4340  axis X   (in the shoulder cap)
J3 upper-arm yaw   DM-J4310  axis Z   (in the clevis)
J4 elbow           DM-J4310  axis Y   (bottom of the upper arm)
J5 wrist pitch     STS3215   axis Y   (bottom of the forearm)
J6 wrist roll      STS3215   axis Z   (in the wrist clevis)
J7 jaw             STS3215   axis X   (in the palm)

Links that carry a motor across their split plane are printed as clamshell
halves (split at x = SHOULDER_X), so the motor body is clamped between them.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import Bought, Joint, Part, box, cbox, cut, cyl, cyl_between, fuse, hexagon, hw, rrect, tube_between
from base import split_one

X0 = P.SHOULDER_X
Y0 = P.SHOULDER_Y
S = P.SHOULDER_Z0
E = S - P.UPPER_ARM
W = E - P.FOREARM
J3_FACE_Z = S + P.J3_FACE
J2_FACE_X = X0 - 26.65
J4_FACE_Y = Y0 + 23.0
# GM-5 module frames: (origin, output direction, servo-offset direction), left arm
GM = {
    "j2": ((J2_FACE_X, Y0, S), (-1, 0, 0), (0, 1, 0)),
    "j3": ((X0, Y0, J3_FACE_Z), (0, 0, -1), (-1, 0, 0)),
    "j4": ((X0, J4_FACE_Y, E), (0, 1, 0), (0, 0, -1)),
}

# wrist-roll servo, shaft down on the arm axis
J6_BODY_Z = (W - 81.0, W - 46.0)
J6_HORN_Z = J6_BODY_Z[0] - 4.0
# jaw servo, shaft along +X


def _out_holes(center, axis, face, outward, pcd=P.DM_OUT_PCD, n=P.DM_OUT_N, depth=30.0, head_from=None):
    """Clearance holes on the DM output bolt circle, drilled from `face` along `outward`."""
    tools = []
    for i in range(n):
        a = 2 * math.pi * i / n
        u, v = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        if axis == "x":
            p = (face, center[1] + u, center[2] + v)
        elif axis == "y":
            p = (center[0] + u, face, center[2] + v)
        else:
            p = (center[0] + u, center[1] + v, face)
        d = outward
        q = tuple(p[k] - d[k] * 1.0 for k in range(3))
        tools.append(cyl(q, d, P.M3, depth))
        if head_from is not None:
            h = tuple(p[k] + d[k] * head_from for k in range(3))
            tools.append(cyl(h, d, 6.6, depth))
    hw("M3x8 socket head (DM output)", n)
    return tools


def _rear_holes(center, axis, face, inward, n=P.DM_REAR_N, pcd=P.DM_REAR_PCD):
    tools = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        u, v = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        if axis == "x":
            p = (face, center[1] + u, center[2] + v)
        elif axis == "y":
            p = (center[0] + u, face, center[2] + v)
        else:
            p = (center[0] + u, center[1] + v, face)
        q = tuple(p[k] - inward[k] * 8 for k in range(3))
        tools.append(cyl(q, inward, P.M3, 10))
    hw("M3x10 socket head (DM rear)", n)
    return tools


def _horn_holes(center, axis, face, outward, depth=12):
    tools = []
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        u, v = P.STS_HORN_PCD / 2 * math.cos(a), P.STS_HORN_PCD / 2 * math.sin(a)
        if axis == "x":
            p = (face, center[1] + u, center[2] + v)
        elif axis == "y":
            p = (center[0] + u, face, center[2] + v)
        else:
            p = (center[0] + u, center[1] + v, face)
        q = tuple(p[k] - outward[k] * 1 for k in range(3))
        tools.append(cyl(q, outward, 2.3, depth))
    c = list(center)
    c["xyz".index(axis)] = face
    q = tuple(c[k] - outward[k] * 1 for k in range(3))
    tools.append(cyl(q, outward, 3.2, depth))  # horn centre screw
    hw("M2x8 screw (horn)", 4)
    return tools


def _clam_bolt(y, z, xr=(X0 - 30, X0 + 30), boss=10.0):
    """Boss and tools for one clamshell bolt along X: head on the -X half, nut on the +X half."""
    b = cyl_between("x", (y, z), X0 - 9, X0 + 9, boss)
    tools = [cyl_between("x", (y, z), xr[0], xr[1], P.M3),
             cyl_between("x", (y, z), xr[0], X0 - 6, P.M3_HEAD),
             _hex_x(X0 + 6, xr[1], y, z)]
    hw("M3x16 socket head + nut (clamshell)", 1)
    return b, tools


def _hex_x(x0, x1, y, z):
    h = hexagon(0, 0, 0, x1 - x0, P.NUT_AF)
    return h.rotate((0, 0, 0), (0, 1, 0), 90).translate((x0, y, z))


# ---------------------------------------------------------------- link 1: shoulder cap (J1 out, J2 cup)

def shoulder() -> cq.Shape:
    import gearbox as G

    hub = cyl_between("y", (X0, S), P.J1_FACE_Y + 2, P.J1_FACE_Y + 8, 52)
    cup, inserts, keep = G.mount(*GM["j2"])
    bridge = box(J2_FACE_X + 4, X0 + 8, P.J1_FACE_Y + 5, Y0 - (G.D + 0.6) / 2 + 1.0, S - 24, S + 24)
    s = fuse(hub, cup, bridge)
    tools = [cyl_between("y", (X0, S), P.J1_FACE_Y, Y0 + 40, 14), keep, inserts]
    # J1 output screws: heads reached straight through the empty J2 cup, so drill on through
    tools += _out_holes((X0, 0, S), "y", P.J1_FACE_Y + 2, (0, 1, 0), depth=12, head_from=6)
    for i in range(P.DM_OUT_N):
        a = 2 * math.pi * i / P.DM_OUT_N
        u, v = P.DM_OUT_PCD / 2 * math.cos(a), P.DM_OUT_PCD / 2 * math.sin(a)
        tools.append(cyl_between("y", (X0 + u, S + v), P.J1_FACE_Y + 8, Y0 + 40, 7.0))
    hw("M3 heat-set insert", 4)
    hw("M3x8 socket head (module flange)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 2: clevis (J2 out, J3 cup)

def clevis() -> cq.Shape:
    import gearbox as G

    x0, x1 = J2_FACE_X - 2 - 6, J2_FACE_X - 2
    disc = cyl_between("x", (Y0, S), x0, x1, 52)
    cup, inserts, keep = G.mount(*GM["j3"])
    plate = box(x0, x1, Y0 - 24, Y0 + 24, J3_FACE_Z + 3.5, S)
    s = fuse(disc, plate, cup)
    tools = _out_holes((0, Y0, S), "x", x1, (-1, 0, 0), depth=10, head_from=4)
    tools += [cyl_between("x", (Y0, S), x0 - 1, x1 + 1, 14), keep, inserts]
    hw("M3 heat-set insert", 4)
    hw("M3x8 socket head (module flange)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 3: upper arm (J3 out, J4 cup), clamshell

def upper_arm() -> cq.Shape:
    import gearbox as G

    d1 = J3_FACE_Z - 2
    d0 = d1 - 6
    disc = cyl_between("z", (X0, Y0), d0, d1, P.ARM_TUBE_D)
    tube = tube_between("z", (X0, Y0), E + 28, d0 + 0.5, P.ARM_TUBE_D, P.ARM_TUBE_D - 6)  # starts above the elbow disc
    cup, inserts, keep = G.mount(*GM["j4"])
    # carry the tube down past the elbow axis to tie into the cup, short of the elbow disc's swing
    tie = tube_between("z", (X0, Y0), E - 12, E + 28.5, P.ARM_TUBE_D, P.ARM_TUBE_D - 6).intersect(box(0, 300, 0, J4_FACE_Y - 5, E - 20, E + 30))
    s = fuse(disc, tube, cup, tie)
    tools = []
    adds = []
    for y, z in ((Y0 - 26, d0 - 14), (Y0 + 26, d0 - 14), (Y0 - 26, E + 44), (Y0 + 26, E + 44),
                 (Y0 + 4, E - 37), (Y0 + 16, E - 37)):
        b, t = _clam_bolt(y, z)
        adds.append(b)
        tools += t
    s = fuse(s, *adds)
    tools += _out_holes((X0, Y0, 0), "z", d1, (0, 0, -1), depth=10, head_from=4)
    tools += [cyl_between("z", (X0, Y0), d0 - 1, d1 + 1, 14), keep, inserts]
    hw("M3 heat-set insert", 4)
    hw("M3x8 socket head (module flange)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 4a: elbow (J4 out to the forearm flange)

ELBOW_FLANGE = (E - 70.0, E - 64.0)


def elbow() -> cq.Shape:
    y0, y1 = J4_FACE_Y + 2, J4_FACE_Y + 8
    disc = cyl_between("y", (X0, E), y0, y1, 54)
    plate = box(X0 - 22, X0 + 22, y0, y1, ELBOW_FLANGE[1], E)
    bridge = box(X0 - 22, X0 + 22, Y0 - 26, y1, ELBOW_FLANGE[1], ELBOW_FLANGE[1] + 10)
    flange = cyl_between("z", (X0, Y0), ELBOW_FLANGE[1] - 0.01, ELBOW_FLANGE[1] + 10, 54)
    s = fuse(disc, plate, bridge, flange)
    tools = _out_holes((X0, 0, E), "y", y0, (0, 1, 0), depth=10, head_from=4)
    tools.append(cyl_between("y", (X0, E), y0 - 1, y1 + 1, 14))
    for x, y in _forearm_bolts():
        tools.append(cyl((x, y, ELBOW_FLANGE[1] - 1), "z", P.M3, 20))
        tools.append(hexagon(x, y, ELBOW_FLANGE[1] + 6, ELBOW_FLANGE[1] + 11, P.NUT_AF))
    tools.append(cyl((X0, Y0, ELBOW_FLANGE[1] - 1), "z", 18, 20))  # cable pass
    hw("M3x16 socket head + nut (elbow flange)", 4)
    return cut(s, *tools)


def _forearm_bolts():
    return [(X0 + 19 * math.cos(a), Y0 + 19 * math.sin(a)) for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]


# ---------------------------------------------------------------- link 4b: forearm, clamshell, holds J5

J5_BODY = dict(x=(X0 - P.STS_W / 2, X0 + P.STS_W / 2), y=(Y0 - 18.5, Y0 + 16.5), z=(W - P.STS_SHAFT_FROM_END, W - P.STS_SHAFT_FROM_END + P.STS_L))


def forearm() -> cq.Shape:
    f0, f1 = ELBOW_FLANGE
    r = P.FOREARM_TUBE_D / 2
    flange = cyl_between("z", (X0, Y0), f0, f1, 54)
    tube = cyl_between("z", (X0, Y0), W, f0 + 0.5, P.FOREARM_TUBE_D)
    end = cyl_between("y", (X0, W), Y0 - r, Y0 + r, P.FOREARM_TUBE_D)
    s = fuse(flange, tube, end)
    jb = J5_BODY
    tools = [cyl_between("z", (X0, Y0), jb["z"][1] - 1, f0 - 3, P.FOREARM_TUBE_D - 6),
             box(jb["x"][0] - 0.3, jb["x"][1] + 0.3, jb["y"][0] - 0.3, jb["y"][1] + 0.3, jb["z"][0] - 0.3, jb["z"][1] + 0.3),
             cyl_between("y", (X0, W), jb["y"][1] - 1, Y0 + r + 1, 28),  # horn window
             cyl_between("y", (X0, W), Y0 - r - 1, Y0 - r + 6, P.M3_INSERT),  # idler insert
             cyl((X0, Y0, f0 - 6), "z", 18, 16)]
    for x, y in _forearm_bolts():
        tools.append(cyl((x, y, f0 - 10), "z", P.M3, 30))
        tools.append(cyl((x, y, f0 - 10), "z", P.M3_HEAD, 10 + 0.01))
    adds = []
    for y, z in ((Y0 - 20, f0 - 18), (Y0 + 20, f0 - 18), (Y0 - 19, jb["z"][1] + 9), (Y0 + 19, jb["z"][1] + 9)):
        b, t = _clam_bolt(y, z)
        adds.append(b)
        tools += t
    s = fuse(s, *adds)
    hw("M3 heat-set insert", 1)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 5: wrist clevis (J5 out, holds J6)

def wrist() -> cq.Shape:
    r = P.FOREARM_TUBE_D / 2
    ya0, ya1 = Y0 + r + 1, Y0 + r + 6  # horn cheek
    yb0, yb1 = Y0 - r - 6, Y0 - r - 1  # idler cheek
    parts = []
    for y0, y1 in ((ya0, ya1), (yb0, yb1)):
        parts.append(cyl_between("y", (X0, W), y0, y1, 40))
        parts.append(box(X0 - 20, X0 + 20, y0, y1, W - 46, W))
    parts.append(cyl_between("y", (X0, W), J5_BODY["y"][1] + 4.3, ya0 + 0.5, 21))  # horn boss into the window
    parts.append(box(X0 - 20, X0 + 20, yb0, ya1, W - 46, W - 40))
    j6x0 = X0 - P.STS_SHAFT_FROM_END
    sleeve = box(j6x0 - 3, j6x0 + P.STS_L + 3, Y0 - P.STS_W / 2 - 3, Y0 + P.STS_W / 2 + 3, J6_BODY_Z[0] + 3, W - 40)
    parts.append(sleeve)
    s = fuse(*parts)
    tools = [box(j6x0 - 0.3, j6x0 + P.STS_L + 0.3, Y0 - P.STS_W / 2 - 0.3, Y0 + P.STS_W / 2 + 0.3, J6_BODY_Z[0] - 1, J6_BODY_Z[1] + 0.3),
             cyl_between("y", (X0, W), yb0 - 1, yb1 + 1, P.M3)]
    tools += _horn_holes((X0, 0, W), "y", J5_BODY["y"][1] + 4.3, (0, 1, 0), depth=12)
    hw("M3x12 shoulder screw (idler)", 1)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 6: palm and parallel gripper (J6 out, holds J7)
#
# J7 points its horn down. A printed 16-tooth module-1.5 pinion on the horn drives two racks that slide in
# channels in the palm, in opposite directions, so the two fingers open symmetrically about the arm axis.
# Pitch radius 12 mm: 40 mm of finger travel per side is 191 degrees of servo.

GEAR_M = 1.5
GEAR_Z = 16
GEAR_R = GEAR_M * GEAR_Z / 2  # 12
BACKLASH = 0.2
J7_BODY_Z = (J6_HORN_Z - 6 - P.STS_H, J6_HORN_Z - 6)  # servo body, shaft down at the arm axis
J7_HORN_Z = (J7_BODY_Z[0] - 4, J7_BODY_Z[0])
PINION_Z = (J7_HORN_Z[0] - 8, J7_HORN_Z[0])
RACK_Z = (PINION_Z[0] - 0.0, PINION_Z[1])
HOUSING_Z = (PINION_Z[0] - 4.5, J7_BODY_Z[0] - 1)
FLOOR_Z = (HOUSING_Z[0], PINION_Z[0] - 0.5)
HOUSING_Y = 55.0
FINGER_T = 8.0
PAD_T = 3.0
GRIP_TRAVEL = 40.0  # mm per finger
HAND = W - (PINION_Z[0] - 60.0)  # wrist axis to fingertip
TIP = W - HAND
FINGER_TOP = HOUSING_Z[0] - 1.0
RACK_X0 = GEAR_R + BACKLASH - GEAR_M  # tooth tips, from the axis
RACK_X1 = GEAR_R + BACKLASH + 1.25 * GEAR_M + 5.0  # back of the rack body
WRIST_CAM_X = X0 - 25.2  # USB camera board on the back of the palm, looking at the fingertips


def _pinion_profile(r_tip, r_root, r_pitch, n, z0, z1):
    s_p = math.pi * GEAR_M / 2
    tan20 = math.tan(math.radians(20))
    w_tip = max(s_p - 2 * (r_tip - r_pitch) * tan20, 0.6)
    w_root = s_p + 2 * (r_pitch - r_root) * tan20
    pts = []
    step = 2 * math.pi / n
    for i in range(n):
        c = i * step
        for r, w, sgn in ((r_root, w_root, -1), (r_tip, w_tip, -1), (r_tip, w_tip, 1), (r_root, w_root, 1)):
            a = c + sgn * (w / 2) / r
            pts.append((r * math.cos(a), r * math.sin(a)))
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0).val()


def pinion() -> cq.Shape:
    r_tip, r_root = GEAR_R + GEAR_M, GEAR_R - 1.25 * GEAR_M
    s = _pinion_profile(r_tip, r_root, GEAR_R, GEAR_Z, *PINION_Z).translate((X0, Y0, 0))
    s = fuse(s, cyl((X0, Y0, PINION_Z[1] - 2), "z", 2 * r_root, 2))
    tools = _horn_holes((X0, Y0, 0), "z", PINION_Z[1], (0, 0, -1), depth=10)
    return cut(s, *tools)


def _rack(sign, y0, y1):
    """Rack on the +x (sign=1) or -x side of the pinion, teeth facing the axis, between y0 and y1 at closed."""
    p = math.pi * GEAR_M
    tan20 = math.tan(math.radians(20))
    s_p = p / 2
    xa = GEAR_R + BACKLASH  # pitch line
    tip, root = xa - GEAR_M, xa + 1.25 * GEAR_M
    w_tip = s_p - 2 * GEAR_M * tan20
    w_root = s_p + 2 * 1.25 * GEAR_M * tan20
    body = box(sign * root, sign * RACK_X1, y0, y1, *RACK_Z)
    teeth = []
    k0 = math.floor((y0 - Y0) / p) - 1
    k1 = math.ceil((y1 - Y0) / p) + 1
    for k in range(k0, k1 + 1):
        yc = Y0 + (k + 0.5) * p  # gaps centred on Y0, where the pinion has a tooth
        pts = [(sign * root, yc - w_root / 2), (sign * tip, yc - w_tip / 2), (sign * tip, yc + w_tip / 2), (sign * root, yc + w_root / 2)]
        teeth.append(cq.Workplane("XY").workplane(offset=RACK_Z[0]).polyline(pts).close().extrude(RACK_Z[1] - RACK_Z[0]).val())
    s = fuse(body, *teeth).intersect(box(-60, 60, y0, y1, RACK_Z[0], RACK_Z[1]))
    return s.translate((X0, 0, 0))


def finger(sign) -> cq.Shape:
    """Rack + drop bracket + finger. sign=+1 is the finger on the +y side (its rack is on the +x side)."""
    if sign > 0:
        rack = _rack(1, Y0 - 45, Y0 + 25)
        y0, y1 = Y0 + PAD_T, Y0 + PAD_T + FINGER_T
        bx0, bx1 = X0 + RACK_X1 - 5.0, X0 + RACK_X1
    else:
        rack = _rack(-1, Y0 - 25, Y0 + 45)
        y0, y1 = Y0 - PAD_T - FINGER_T, Y0 - PAD_T
        bx0, bx1 = X0 - RACK_X1, X0 - RACK_X1 + 5.0
    drop = box(bx0, bx1, y0, y1, FINGER_TOP - 8, RACK_Z[1])
    top = box(min(X0 - 12, bx0), max(X0 + 12, bx1), y0, y1, FINGER_TOP - 8, FINGER_TOP)
    blade = box(X0 - 12, X0 + 12, y0, y1, TIP, FINGER_TOP - 7)
    s = fuse(rack, drop, top, blade)
    face = y0 if sign > 0 else y1
    tools = []
    for z in (TIP + 12, TIP + 32):
        tools.append(cyl_between("y", (X0, z), face - 5, face + 5, 2.6))
    return cut(s, *tools)


def palm() -> cq.Shape:
    top0, top1 = J6_HORN_Z - 5, J6_HORN_Z
    disc = cyl_between("z", (X0, Y0), top0, top1, 32)
    sx0, sx1 = X0 - P.STS_SHAFT_FROM_END, X0 - P.STS_SHAFT_FROM_END + P.STS_L
    sleeve = box(sx0 - 3, sx1 + 3, Y0 - P.STS_W / 2 - 3, Y0 + P.STS_W / 2 + 3, HOUSING_Z[1] - 0.01, top0 + 0.5)
    housing = rrect(X0, Y0, HOUSING_Z[0], HOUSING_Z[1], 50, 2 * HOUSING_Y, 6)
    s = fuse(disc, sleeve, housing)
    tools = [box(sx0 - 0.3, sx1 + 0.3, Y0 - P.STS_W / 2 - 0.3, Y0 + P.STS_W / 2 + 0.3, J7_BODY_Z[0] - 0.01, J7_BODY_Z[1] + 0.3),
             cyl((X0, Y0, PINION_Z[0] - 1), "z", 2 * (GEAR_R + GEAR_M) + 2, J7_BODY_Z[0] - PINION_Z[0] + 1.5)]
    for sgn in (1, -1):
        xa, xb = sorted((sgn * (RACK_X0 - 0.6), sgn * (RACK_X1 + 0.6)))
        tools.append(box(X0 + xa, X0 + xb, Y0 - HOUSING_Y - 1, Y0 + HOUSING_Y + 1, RACK_Z[0] - 0.4, RACK_Z[1] + 0.4))
        fa, fb = sorted((sgn * (RACK_X1 - 5.6), sgn * (RACK_X1 + 0.6)))
        tools.append(box(X0 + fa, X0 + fb, Y0 - HOUSING_Y - 1, Y0 + HOUSING_Y + 1, FLOOR_Z[0] - 1, RACK_Z[0]))
    tools += _horn_holes((X0, Y0, 0), "z", top1, (0, 0, -1), depth=10)
    for dy in (-12.0, 12.0):  # wrist camera, M2 thread-forming
        tools.append(cyl_between("x", (Y0 + dy, (HOUSING_Z[0] + HOUSING_Z[1]) / 2), WRIST_CAM_X - 1, WRIST_CAM_X + 6, 1.8))
    hw("M2x6 thread-forming (wrist camera)", 2)
    return cut(s, *tools)


def pad(sign) -> cq.Shape:
    """TPU finger pad."""
    y0, y1 = (Y0 + 0.0, Y0 + PAD_T) if sign > 0 else (Y0 - PAD_T, Y0 - 0.0)
    s = box(X0 - 12, X0 + 12, y0, y1, TIP, TIP + 44)
    tools = [cyl_between("y", (X0, z), y0 - 1, y1 + 1, 3.2) for z in (TIP + 12, TIP + 32)]
    for z in (TIP + 6, TIP + 16, TIP + 26, TIP + 36):  # grip ridges
        tools.append(box(X0 - 13, X0 + 13, (y1 - 0.8) if sign > 0 else (y0 - 0.2), (y1 + 0.2) if sign > 0 else (y0 + 0.8), z - 1, z + 1))
    hw("M2.5x8 screw (finger pad)", 2)
    return cut(s, *tools)


# ---------------------------------------------------------------- assembly

LINKS = ["link1", "link2", "link3", "link4", "link5", "link6", "link7"]


def _mirror(s):
    return s.mirror("XZ", (0, 0, 0))


def parts(side: str) -> list[Part]:
    m = (lambda s: s) if side == "l" else _mirror
    out = []
    lk = lambda n: f"{side}_{n}"  # noqa: E731

    def add(name, solid, link, **kw):
        out.append(Part(f"{name}_{side}", m(solid), lk(link), "arm", **kw))

    add("shoulder", shoulder(), "link1", color="shell", note="J1 output to the J2 cup. Screw it to J1 before J2 goes in.")
    add("clevis", clevis(), "link2", color="frame", note="J2 output, holds J3.")
    ua = upper_arm()
    add("upper_arm_a", split_one(ua, box(-500, X0, -500, 500, -500, 2000), "upper_arm_a"), "link3", color="shell",
        note="Clamshell half. Prints on the split face.")
    add("upper_arm_b", split_one(ua, box(X0, 500, -500, 500, -500, 2000), "upper_arm_b"), "link3", color="shell",
        note="Clamshell half with the nut traps.")
    add("elbow", elbow(), "link4", color="frame", note="J4 output to the forearm flange.")
    fa = forearm()
    add("forearm_a", split_one(fa, box(-500, X0, -500, 500, -500, 2000), "forearm_a"), "link4", color="shell")
    add("forearm_b", split_one(fa, box(X0, 500, -500, 500, -500, 2000), "forearm_b"), "link4", color="shell")
    add("wrist", wrist(), "link5", color="dark", note="J5 horn and idler, holds J6.")
    add("palm", palm(), "link6", color="dark", note="J6 horn on top, J7 inside, rack channels underneath.")
    add("pinion", pinion(), "link6", color="frame", note="16T module 1.5 on the J7 horn. 100% infill.")
    add("finger_a", finger(1), "link7", color="dark", note="Rack, drop and finger in one piece. Slides in from the +y end.")
    add("finger_b", finger(-1), "link8", color="dark", note="Rack, drop and finger. Slides in from the -y end.")
    add("pad_a", pad(1), "link7", color="rubber", material="TPU", note="TPU 95A.")
    add("pad_b", pad(-1), "link8", color="rubber", material="TPU", note="TPU 95A.")
    out += gm_instances(side)[0]
    return out


def bought(side: str) -> list[Bought]:
    import vendor as V

    m = (lambda s: s) if side == "l" else _mirror
    out = []

    def add(name, pieces, link, kind, mass, key):
        mirrored = [(sfx, m(shp), look) for sfx, shp, look in pieces]
        out.extend(V.boughts(f"{name}_{side}", mirrored, f"{side}_{link}", "arm", kind, mass, key))

    out.extend(gm_instances(side)[1])
    j5 = [(sfx, shp, "alu" if not sfx else look) for sfx, shp, look in V.sts3215()]  # STS3250: same case, aluminium middle
    add("j5", V.place(j5, (X0, J5_BODY["y"][1], W), xdir=(0, 0, 1), zdir=(0, 1, 0)), "link4", "actuator", 75.0, "sts3250")
    add("j6", V.place(V.sts3215(), (X0, Y0, J6_BODY_Z[0]), xdir=(1, 0, 0), zdir=(0, 0, -1)), "link5", "actuator", P.STS_MASS, "sts3215")
    add("j7", V.place(V.sts3215(), (X0, Y0, J7_BODY_Z[0]), xdir=(1, 0, 0), zdir=(0, 0, -1)), "link6", "actuator", P.STS_MASS, "sts3215")
    add("wrist_cam", V.place(V.usb_cam(), (WRIST_CAM_X, Y0, (HOUSING_Z[0] + HOUSING_Z[1]) / 2), xdir=(-1, 0, 0), zdir=(0, 0, 1)),
        "link6", "electronics", 15, "wristcam")
    return out


def gm_instances(side: str):
    """GM-5 modules J2..J4 of one arm: (parts, boughts)."""
    import gearbox as G

    parts, buys = [], []
    links = {"j2": ("link1", "link2"), "j3": ("link2", "link3"), "j4": ("link3", "link4")}
    for j, frame in GM.items():
        fr = frame if side == "l" else G.mirror_frame(*frame)
        pa, ch = links[j]
        p, b = G.instance(f"gm_{side}_{j}", *fr, f"{side}_{pa}", f"{side}_{ch}", "arm", servo="sts3250" if j == "j2" else "sts3215")
        parts += p
        buys += b
    return parts, buys


def _mir_axis(a):
    return (-a[0], a[1], -a[2])


def joints(side: str) -> list[Joint]:
    sy = 1 if side == "l" else -1
    L = P.LIMITS
    raw = [
        ("shoulder_pitch", "lift", "link1", (X0, P.J1_FACE_Y, S), (0, 1, 0), "gm5"),
        ("shoulder_roll", "link1", "link2", (X0, Y0, S), (1, 0, 0), "gm5"),
        ("upper_arm_yaw", "link2", "link3", (X0, Y0, J3_FACE_Z), (0, 0, 1), "gm5s"),
        ("elbow", "link3", "link4", (X0, Y0, E), (0, 1, 0), "gm5s"),
        ("wrist_pitch", "link4", "link5", (X0, Y0, W), (0, 1, 0), "sts3250"),
        ("wrist_roll", "link5", "link6", (X0, Y0, J6_HORN_Z), (0, 0, 1), "sts3215"),
    ]
    out = []
    for name, parent, child, anchor, axis, act in raw:
        pa = parent if parent == "lift" else f"{side}_{parent}"
        an = (anchor[0], sy * anchor[1], anchor[2])
        ax = axis if sy > 0 else _mir_axis(axis)
        out.append(Joint(f"{side}_{name}", "hinge", pa, f"{side}_{child}", an, ax, L[name], act))
    # parallel gripper: two slides, the second mirrors the first (they share one pinion)
    g = (X0, sy * Y0, RACK_Z[0])
    out.append(Joint(f"{side}_gripper", "slide", f"{side}_link6", f"{side}_link7", g, (0, sy * 1.0, 0), L["gripper"], "sts3215g"))
    out.append(Joint(f"{side}_gripper_b", "slide", f"{side}_link6", f"{side}_link8", g, (0, -sy * 1.0, 0), L["gripper"], "sts3215g",
                     mimic=f"{side}_gripper"))
    return out
