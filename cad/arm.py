"""Seven-axis arm (six joints plus the jaw). Built as the left arm; the right is a mirror.

Nori A3-style Feetech bus servos in printed cups. No printed planetaries.

J1 shoulder pitch  STS3095   axis Y   (in the torso yoke)
J2 shoulder roll   STS3095   axis X   (in the shoulder cap)
J3 upper-arm yaw   STS3250   axis Z   (in the clevis)
J4 elbow           STS3095   axis Y   (bottom of the upper arm)
J5 wrist pitch     STS3250   axis Y   (bottom of the forearm)
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
# Servo frames: (origin, output/horn direction, servo-length direction), left arm
SV = {
    "j2": ((J2_FACE_X, Y0, S), (-1, 0, 0), (0, 1, 0), "sts3095"),
    "j3": ((X0, Y0, J3_FACE_Z), (0, 0, -1), (-1, 0, 0), "sts3250"),
    "j4": ((X0, J4_FACE_Y, E), (0, 1, 0), (0, 0, -1), "sts3095"),
}

# arm covers (see arm_covers.py): fixing points on the structural links
SH_TAB_X = (X0 - 18.0, X0 + 12.0)  # shoulder tabs, x span
SH_TAB_Y1 = P.J1_FACE_Y + 21.0
SH_TAB_Z = 34.0  # tab face, from the J2 axis
SH_SCREW_X = (X0 - 10.0, X0 + 8.0)
SH_SCREW_Y = P.J1_FACE_Y + 14.0
CV_SCREW_X = X0 + 22.0  # clevis cover screws, in the span past the J3 cup
CV_SCREW_Z = (J3_FACE_Z + 15.0, J3_FACE_Z + 37.0)
EC_BOLTS = ((Y0 - 26.0, E + 37.0), (Y0 - 26.0, E + 51.0))  # upper-arm clamshell bolts that also hold the elbow-cover collar

# wrist-roll servo, shaft down on the arm axis
J6_BODY_Z = (W - 81.0, W - 46.0)
WRIST_SKIRT = dict(ri=41.0, ro=43.8, z0=J6_BODY_Z[0] - 12.0, web=2.4)  # clears the palm sleeve corners (R 39.8)
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


def _horn_holes(center, axis, face, outward, depth=12, kind="sts3215", head_from=None):
    pcd = P.STS3095_HORN_PCD if kind == "sts3095" else P.STS_HORN_PCD
    hole = P.M3 if kind == "sts3095" else 2.3
    tools = []
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        u, v = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        if axis == "x":
            p = (face, center[1] + u, center[2] + v)
        elif axis == "y":
            p = (center[0] + u, face, center[2] + v)
        else:
            p = (center[0] + u, center[1] + v, face)
        q = tuple(p[k] - outward[k] * 1 for k in range(3))
        tools.append(cyl(q, outward, hole, depth))
        if head_from is not None:
            h = tuple(p[k] + outward[k] * head_from for k in range(3))
            tools.append(cyl(h, outward, 6.6 if kind == "sts3095" else 4.5, depth))
    c = list(center)
    c["xyz".index(axis)] = face
    q = tuple(c[k] - outward[k] * 1 for k in range(3))
    tools.append(cyl(q, outward, 4.0 if kind == "sts3095" else 3.2, depth))
    hw("M3x8 socket head (3095 horn)" if kind == "sts3095" else "M2x8 screw (horn)", 4)
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
    import servo as G

    hub = cyl_between("y", (X0, S), P.J1_FACE_Y + 3.5, P.J1_FACE_Y + 10, 52)
    cup, inserts, keep = G.mount(*SV["j2"][:3], kind=SV["j2"][3])
    bridge = box(J2_FACE_X + 4, X0 + 8, P.J1_FACE_Y + 5, Y0 - (G.D + 0.6) / 2 + 1.0, S - 24, S + 24)
    # Gussets above and below the one bridge, overlapping the hub and the J2 flange.
    # The servo keep-out is cut below, so the ribs stop at the motor body.
    rib_hi = box(J2_FACE_X + 6, X0 + 10, P.J1_FACE_Y + 4.5, P.J1_FACE_Y + 12, S + 12, S + 28)
    rib_lo = box(J2_FACE_X + 6, X0 + 10, P.J1_FACE_Y + 4.5, P.J1_FACE_Y + 12, S - 28, S - 12)
    fair = cyl_between("x", (P.J1_FACE_Y + 8, S), J2_FACE_X + 4, X0 + 10, 34)
    fair = fair.intersect(box(J2_FACE_X + 2, X0 + 12, P.J1_FACE_Y + 4, P.J1_FACE_Y + 13, S - 28, S + 28))
    # Tabs for the shoulder cover: two heat-set inserts each, top and bottom.
    tabs = [box(*SH_TAB_X, P.J1_FACE_Y + 4.5, SH_TAB_Y1, S + 24, S + SH_TAB_Z),
            box(*SH_TAB_X, P.J1_FACE_Y + 4.5, SH_TAB_Y1, S - SH_TAB_Z, S - 24)]
    s = fuse(cut(fuse(hub, bridge, rib_hi, rib_lo, fair, *tabs), keep), cup)
    tools = [cyl_between("y", (X0, S), P.J1_FACE_Y, Y0 + 40, 14), inserts]
    for x in SH_SCREW_X:
        for sz in (1, -1):
            z = S + sz * SH_TAB_Z
            tools.append(cyl_between("z", (x, SH_SCREW_Y), z - sz * P.M3_INSERT_DEPTH, z + sz * 1.0, P.M3_INSERT))
    hw("M3 heat-set insert", 4)
    # J1 horn screws: heads reached straight through the empty J2 cup
    tools += _horn_holes((X0, 0, S), "y", P.J1_FACE_Y + 3.5, (0, 1, 0), depth=12, kind="sts3095", head_from=5)
    pcd = P.STS3095_HORN_PCD
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        u, v = pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)
        tools.append(cyl_between("y", (X0 + u, S + v), P.J1_FACE_Y + 10, Y0 + 40, 7.0))
    hw("M3 heat-set insert", 4)
    hw("M3x10 socket head (servo tabs)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 2: clevis (J2 out, J3 cup)

def clevis() -> cq.Shape:
    import servo as G

    x0, x1 = J2_FACE_X - 2 - 6, J2_FACE_X - 4.0
    disc = cyl_between("x", (Y0, S), x0, x1, 52)
    cup, inserts, keep = G.mount(*SV["j3"][:3], kind=SV["j3"][3], flange_d=52.0)
    # thin cheek at the J2 horn; span to the J3 cup stays below the J2 servo body
    cheek = box(x0, x1, Y0 - 24, Y0 + 24, J3_FACE_Z + 3.5, S)
    span = box(x1 - 1, X0 + 28, Y0 - 24, Y0 + 24, J3_FACE_Z + 3.5, J3_FACE_Z + 48)
    # Side cheeks share the J2 disc and the J3 cup, so one plate is not the whole load path.
    side_a = box(x0, x1, Y0 - 32, Y0 - 20, J3_FACE_Z + 16, S - 22)
    side_b = box(x0, x1, Y0 + 20, Y0 + 32, J3_FACE_Z + 16, S - 22)
    fair = cyl_between("x", (Y0, S - 36), x0, x1, 36)
    s = fuse(cut(fuse(disc, cheek, span, side_a, side_b, fair), keep), cup)
    tools = _horn_holes((0, Y0, S), "x", x1, (-1, 0, 0), depth=10, kind="sts3095", head_from=4)
    tools += [cyl_between("x", (Y0, S), x0 - 1, x1 + 1, 14), inserts]
    for z in CV_SCREW_Z:  # clevis cover screws, into the span's side faces
        for y in (Y0 - 24, Y0 + 24):
            tools.append(cyl_between("y", (CV_SCREW_X, z), y - P.M3_INSERT_DEPTH, y + P.M3_INSERT_DEPTH, P.M3_INSERT))
    hw("M3 heat-set insert", 4)
    hw("M3 heat-set insert", 4)
    hw("M3x10 socket head (servo tabs)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 3: upper arm (J3 out, J4 cup), clamshell

def upper_arm() -> cq.Shape:
    import servo as G

    d1 = J3_FACE_Z - 4.2
    d0 = d1 - 6
    disc = cyl_between("z", (X0, Y0), d0, d1, P.ARM_TUBE_D)
    tube = tube_between("z", (X0, Y0), E + 28, d0 + 0.5, P.ARM_TUBE_D, P.ARM_TUBE_D - 6)  # starts above the elbow disc
    cup, inserts, keep = G.mount(*SV["j4"][:3], kind=SV["j4"][3], flange_d=58.0)
    # carry the tube down past the elbow axis to tie into the cup, short of the elbow disc's swing
    tie = tube_between("z", (X0, Y0), E + 12, E + 28.5, P.ARM_TUBE_D, P.ARM_TUBE_D - 6).intersect(box(-300, 300, 0, J4_FACE_Y - 2, E - 20, E + 30))
    s = fuse(disc, tube, tie)
    tools = []
    adds = []
    for y, z in ((Y0 - 26, d0 - 14), (Y0 + 26, d0 - 14), (Y0 + 26, E + 44)):
        b, t = _clam_bolt(y, z)
        adds.append(b)
        tools += t
    # The two clamshell bolts on the -y side above the elbow also clamp the elbow-cover collar:
    # a solid column wall to wall, and a plain hole (head and nut sit on the collar).
    outer = cyl_between("z", (X0, Y0), E + 20, E + 80, P.ARM_TUBE_D)
    for y, z in EC_BOLTS:
        adds.append(cyl_between("x", (y, z), X0 - 30, X0 + 30, 10).intersect(outer))
        tools.append(cyl_between("x", (y, z), X0 - 40, X0 + 40, P.M3))
    s = fuse(cut(fuse(s, *adds), keep), cup)
    tools += _horn_holes((X0, Y0, 0), "z", d1, (0, 0, -1), depth=10, kind="sts3215", head_from=4)
    tools += [cyl_between("z", (X0, Y0), d0 - 1, d1 + 1, 14), inserts]
    hw("M3 heat-set insert", 4)
    hw("M3x10 socket head (servo tabs)", 4)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 4a: elbow (J4 out to the forearm flange)

ELBOW_FLANGE = (E - 74.0, E - 68.0)  # bridge and nose stay outside the elbow cover's swing


def elbow() -> cq.Shape:
    y0, y1 = J4_FACE_Y + 3.5, J4_FACE_Y + 10
    disc = cyl_between("y", (X0, E), y0, y1, 54)
    plate = box(X0 - 22, X0 + 22, y0, y1, ELBOW_FLANGE[1], E)
    bridge = box(X0 - 22, X0 + 22, Y0 - 26, y1, ELBOW_FLANGE[1], ELBOW_FLANGE[1] + 10)
    flange = cyl_between("z", (X0, Y0), ELBOW_FLANGE[1] - 0.01, ELBOW_FLANGE[1] + 10, 54)
    # Second pair of cheeks beside the plate, and a round nose over the square flange edge.
    cheek_l = box(X0 - 26, X0 - 14, y0, y1, ELBOW_FLANGE[1] + 2, E - 10)
    cheek_r = box(X0 + 14, X0 + 26, y0, y1, ELBOW_FLANGE[1] + 2, E - 10)
    nose = cyl_between("z", (X0, (y0 + y1) / 2), ELBOW_FLANGE[1] + 1, ELBOW_FLANGE[1] + 10, 40)
    s = fuse(disc, plate, bridge, flange, cheek_l, cheek_r, nose)
    tools = _horn_holes((X0, 0, E), "y", y0, (0, 1, 0), depth=10, kind="sts3095", head_from=4)
    tools.append(cyl_between("y", (X0, E), y0 - 1, y1 + 1, 14))
    for x, y in _forearm_bolts():
        tools.append(cyl((x, y, ELBOW_FLANGE[1] - 1), "z", P.M3, 20))
        tools.append(hexagon(x, y, ELBOW_FLANGE[1] + 6, ELBOW_FLANGE[1] + 11, P.NUT_AF))
    tools.append(cyl((X0, Y0, ELBOW_FLANGE[1] - 1), "z", 18, 20))  # bore; not a cable path (J4 shaft is the Ø14)
    # Cable slot past J4, +X side (elbow_cover_b), through the flange into the forearm. Not the Ø14 shaft hole.
    tools.append(box(X0 + 17, X0 + 25, Y0 - 4.5, Y0 + 4.5, ELBOW_FLANGE[1] - 2, E - 8))
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
             cyl((X0, Y0, f0 - 6), "z", 18, 16),
             # Cable channel past the J5 body, +X side of the tube, into the wrist. Not the J5 idler.
             box(X0 + 17, X0 + 25, Y0 - 4.5, Y0 + 4.5, W - 2, f0 + 1)]
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
    # Round the sleeve corners so the wrist fairing covers the square edges.
    sx0, sx1 = j6x0 - 3, j6x0 + P.STS_L + 3
    sy0, sy1 = Y0 - P.STS_W / 2 - 3, Y0 + P.STS_W / 2 + 3
    wz0, wz1 = J6_BODY_Z[0] + 3, W - 40
    for x in (sx0, sx1):
        for y in (sy0, sy1):
            parts.append(cyl_between("z", (x, y), wz0, wz1, 7))
    # Skirt: hides the J6 horn and the top of the palm, clear of the palm's roll circle.
    sk = WRIST_SKIRT
    parts.append(tube_between("z", (X0, Y0), sk["z0"], wz0 + 0.01, 2 * sk["ro"], 2 * sk["ri"]))
    parts.append(cyl_between("z", (X0, Y0), wz0 - sk["web"], wz0 + 0.01, 2 * sk["ro"]))
    s = fuse(*parts)
    tools = [box(j6x0 - 0.3, j6x0 + P.STS_L + 0.3, Y0 - P.STS_W / 2 - 0.3, Y0 + P.STS_W / 2 + 0.3, J6_BODY_Z[0] - 1, J6_BODY_Z[1] + 0.3),
             cyl_between("y", (X0, W), yb0 - 1, yb1 + 1, P.M3),
             # Enter from the forearm +X channel, only down to the top of J6 (the J6 body fills the sleeve in X).
             box(X0 + 17, X0 + 25, Y0 - 4.5, Y0 + 4.5, J6_BODY_Z[1] - 1, W + 1),
             # Then a lane along the -Y face of J6 into the skirt, not through the J5 idler.
             box(X0 - 8, X0 + 16, Y0 - P.STS_W / 2 - 5, Y0 - P.STS_W / 2 - 0.5, J6_BODY_Z[0] + 2, J6_BODY_Z[1] + 2)]
    tools += _horn_holes((X0, 0, W), "y", J5_BODY["y"][1] + 4.3, (0, 1, 0), depth=12)
    # the J6 horn turns inside the web's opening
    tools.append(cyl_between("z", (X0, Y0), J6_BODY_Z[0] - 6, J6_BODY_Z[0] + 1, 2 * (P.STS_HORN_D / 2 + 1.5)))
    # Camera USB enters the skirt on the back (-X), next to the roll axis.
    sk = WRIST_SKIRT
    tools.append(box(X0 - sk["ro"] - 1, X0 - sk["ri"] + 2.5, Y0 - 3.5, Y0 + 3.5, sk["z0"] - 0.5, wz0 + 0.5))
    hw("M3x12 shoulder screw (idler)", 1)
    return cut(s, *tools)


# ---------------------------------------------------------------- link 6: palm and parallel gripper (J6 out, holds J7)
#
# J7 points its horn down. A 16-tooth module-1.5 involute pinion on the horn drives two racks
# that slide in channels in the palm, in opposite directions, so the fingers open symmetrically.
# Pitch radius 12 mm. 50 mm of travel per finger is 239 degrees of servo (STS3215, multi-turn).
# Rated 0.98 N·m -> 40.8 N per finger; a metal pinion is the wear part so that limit can be used.
# A printed PETG pinion should stay at about 0.5 N·m (~20.8 N per finger).

GEAR_M = 1.5
GEAR_Z = 16
GEAR_R = GEAR_M * GEAR_Z / 2  # 12
GEAR_PRESSURE = 20.0  # deg, involute
BACKLASH = 0.1
J7_BODY_Z = (J6_HORN_Z - 6 - P.STS_H, J6_HORN_Z - 6)  # servo body, shaft down at the arm axis
J7_HORN_Z = (J7_BODY_Z[0] - 4, J7_BODY_Z[0])
PINION_Z = (J7_HORN_Z[0] - 8, J7_HORN_Z[0])
RACK_Z = (PINION_Z[0] - 0.0, PINION_Z[1])
HOUSING_Z = (PINION_Z[0] - 4.5, J7_BODY_Z[0] - 1)
FLOOR_Z = (HOUSING_Z[0], PINION_Z[0] - 0.5)
HOUSING_Y = 72.0
FINGER_T = 9.0
FINGER_W = 34.0  # pad width, mm
PAD_T = 0.0  # inner faces meet at the mid-plane when closed (~0 mm gap)
GRIP_TRAVEL = 50.0  # mm per finger; 100 mm opening
NAIL = 3.5  # fingertip hook past the pad, mm
HAND = W - (PINION_Z[0] - 60.0 - NAIL)  # wrist axis to fingernail
TIP = W - HAND
FINGER_TOP = HOUSING_Z[0] - 3.1  # wide finger plate sits 0.5 mm below the lid
RACK_X0 = GEAR_R + BACKLASH - GEAR_M  # tooth tips, from the axis
RACK_X1 = GEAR_R + BACKLASH + 1.25 * GEAR_M + 5.0  # back of the rack body
WRIST_CAM_X = X0 - 25.2  # USB camera board on the back of the palm, looking at the fingertips
CAM_PITCH = 28.0  # UB0234 hole pitch, 28 x 28 mm square
LID_Z = (HOUSING_Z[0] - 2.6, HOUSING_Z[0])
LID_SCREWS = ((18.0, 48.0), (18.0, -48.0), (-18.0, 48.0), (-18.0, -48.0))


def _involute_pt(r_base, r):
    t = math.sqrt(max((r / r_base) ** 2 - 1.0, 0.0))
    return (r_base * (math.cos(t) + t * math.sin(t)),
            r_base * (math.sin(t) - t * math.cos(t)))


def _pinion_teeth(r_tip, r_root, r_pitch, n, z0, z1):
    alpha = math.radians(GEAR_PRESSURE)
    r_base = r_pitch * math.cos(alpha)
    pitch_thick = math.pi * GEAR_M / 2
    px, py = _involute_pt(r_base, r_pitch)
    pitch_ang = math.atan2(py, px)
    half = pitch_thick / (2 * r_pitch)
    n_samp = 10
    r0 = max(r_root, r_base * 1.001)
    rs = [r0 + (r_tip - r0) * i / n_samp for i in range(n_samp + 1)]
    teeth = []
    hub = cq.Workplane("XY").workplane(offset=z0).circle(r_root).extrude(z1 - z0).val()
    for i in range(n):
        c = 2 * math.pi * i / n
        pts = []
        # right flank (involute, +side)
        def rot(x, y, ang):
            return (x * math.cos(ang) - y * math.sin(ang), x * math.sin(ang) + y * math.cos(ang))
        if r_root < r_base:
            pts.append(rot(r_root, 0, c - half))
            pts.append(rot(r_base, 0, c - half))
        for r in rs:
            x, y = _involute_pt(r_base, r)
            pts.append(rot(x, y, c - half - pitch_ang))
        for r in reversed(rs):
            x, y = _involute_pt(r_base, r)
            pts.append(rot(x, -y, c + half + pitch_ang))
        if r_root < r_base:
            pts.append(rot(r_base, 0, c + half))
            pts.append(rot(r_root, 0, c + half))
        # close toward centre so the tooth welds to the hub
        pts.append(rot(r_root * 0.6, 0, c))
        teeth.append(cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0).val())
    return fuse(hub, *teeth)


def pinion() -> cq.Shape:
    r_tip, r_root = GEAR_R + GEAR_M, GEAR_R - 1.25 * GEAR_M
    s = _pinion_teeth(r_tip, r_root, GEAR_R, GEAR_Z, *PINION_Z).translate((X0, Y0, 0))
    s = fuse(s, cyl((X0, Y0, PINION_Z[1] - 2), "z", 2 * r_root, 2))
    tools = _horn_holes((X0, Y0, 0), "z", PINION_Z[1], (0, 0, -1), depth=10)
    return cut(s, *tools)


def _rack(sign, y0, y1):
    """Involute rack: straight 20° flanks. Pitch line at GEAR_R + BACKLASH/2."""
    p = math.pi * GEAR_M
    tan20 = math.tan(math.radians(GEAR_PRESSURE))
    s_p = p / 2
    xa = GEAR_R + BACKLASH / 2  # pitch line, backlash away from the pinion
    tip, root = xa - GEAR_M, xa + 1.25 * GEAR_M
    w_tip = s_p - 2 * GEAR_M * tan20
    w_root = s_p + 2 * 1.25 * GEAR_M * tan20
    body = box(sign * root, sign * RACK_X1, y0, y1, *RACK_Z)
    teeth = []
    k0 = math.floor((y0 - Y0) / p) - 1
    k1 = math.ceil((y1 - Y0) / p) + 1
    for k in range(k0, k1 + 1):
        yc = Y0 + (k + 0.5) * p
        pts = [(sign * root, yc - w_root / 2), (sign * tip, yc - w_tip / 2), (sign * tip, yc + w_tip / 2), (sign * root, yc + w_root / 2)]
        teeth.append(cq.Workplane("XY").workplane(offset=RACK_Z[0]).polyline(pts).close().extrude(RACK_Z[1] - RACK_Z[0]).val())
    s = fuse(body, *teeth).intersect(box(-60, 60, y0, y1, RACK_Z[0], RACK_Z[1]))
    return s.translate((X0, 0, 0))


def rack(sign) -> cq.Shape:
    """PETG rack + drop. Bolts to the TPU finger. sign=+1 is the +y finger (rack on +x)."""
    span = GRIP_TRAVEL + 12.0
    if sign > 0:
        body = _rack(1, Y0 - span, Y0 + 25)
        y0, y1 = Y0 + PAD_T, Y0 + PAD_T + FINGER_T
        bx0, bx1 = X0 + RACK_X1 - 5.0, X0 + RACK_X1
    else:
        body = _rack(-1, Y0 - 25, Y0 + span)
        y0, y1 = Y0 - PAD_T - FINGER_T, Y0 - PAD_T
        bx0, bx1 = X0 - RACK_X1, X0 - RACK_X1 + 5.0
    drop = box(bx0, bx1, y0, y1, FINGER_TOP - 8, RACK_Z[1])
    top = box(min(X0 - FINGER_W / 2, bx0), max(X0 + FINGER_W / 2, bx1), y0, y1, FINGER_TOP - 8, FINGER_TOP)
    s = fuse(body, drop, top)
    face = y0 if sign > 0 else y1
    tools = [cyl_between("y", (X0, z), face - 5, face + 5, 2.6) for z in (TIP + NAIL + 12, TIP + NAIL + 32)]
    hw("M2.5x10 screw (TPU finger)", 2)
    return cut(s, *tools)


def finger(sign) -> cq.Shape:
    """Compliant TPU 95A finger: 34 mm curved pad, fingernail, FSR 402 pocket. Closed gap ~0 mm."""
    hw = FINGER_W / 2
    if sign > 0:
        y_in, y_out = Y0 + PAD_T, Y0 + PAD_T + FINGER_T
    else:
        y_out, y_in = Y0 - PAD_T - FINGER_T, Y0 - PAD_T
    z0, z1 = TIP + NAIL, FINGER_TOP - 7
    r_pad = 22.0
    body = box(X0 - hw, X0 + hw, min(y_in, y_out), max(y_in, y_out), z0, z1)
    # Convex pad: cylinder along Z, crest on the mid-plane (Y0) at X0.
    pad = cyl_between("z", (X0, Y0 + sign * r_pad), z0, z1, 2 * r_pad)
    ymin, ymax = (Y0 + 0.05, Y0 + FINGER_T) if sign > 0 else (Y0 - FINGER_T, Y0 - 0.05)
    pad = pad.intersect(box(X0 - hw, X0 + hw, ymin, ymax, z0, z1))
    # Fingernail: thin hook at the tip, same mid-plane crest, 3.5 mm past the pad.
    nail_y0, nail_y1 = (Y0 + 0.05, Y0 + 2.2) if sign > 0 else (Y0 - 2.2, Y0 - 0.05)
    nail = box(X0 - 11, X0 + 11, nail_y0, nail_y1, TIP, z0 + 1.2)
    s = fuse(body, pad, nail)
    tools = [cyl_between("y", (X0, z), y_in - 1, y_out + 1, 3.2) for z in (TIP + NAIL + 12, TIP + NAIL + 32)]
    # FSR 402 pocket in the back of the pad (18 x 18 x 0.6), cable groove toward the rack.
    midz = (z0 + z1) / 2
    back = y_out
    if sign > 0:
        tools.append(box(X0 - 9, X0 + 9, back - 0.7, back + 0.2, midz - 9, midz + 9))
        tools.append(box(X0 - 1.3, X0 + 1.3, back - 0.7, back + 0.2, midz + 8, z1 + 0.5))
    else:
        tools.append(box(X0 - 9, X0 + 9, back - 0.2, back + 0.7, midz - 9, midz + 9))
        tools.append(box(X0 - 1.3, X0 + 1.3, back - 0.2, back + 0.7, midz + 8, z1 + 0.5))
    return cut(s, *tools)


def palm() -> cq.Shape:
    top0, top1 = J6_HORN_Z - 5, J6_HORN_Z
    disc = cyl_between("z", (X0, Y0), top0, top1, 32)
    sx0, sx1 = X0 - P.STS_SHAFT_FROM_END, X0 - P.STS_SHAFT_FROM_END + P.STS_L
    sleeve = box(sx0 - 3, sx1 + 3, Y0 - P.STS_W / 2 - 3, Y0 + P.STS_W / 2 + 3, HOUSING_Z[1] - 0.01, top0 + 0.5)
    housing = rrect(X0, Y0, HOUSING_Z[0], HOUSING_Z[1], 50, 2 * HOUSING_Y, 6)
    # Camera shroud on the back: 32 x 32 UB0234, 28 mm square hole pitch, lens window toward the fingers.
    cam_z = (HOUSING_Z[0] + HOUSING_Z[1]) / 2
    shroud_outer = box(WRIST_CAM_X - 9.5, X0 - 24.0 - 0.4, Y0 - 18, Y0 + 18, cam_z - 18, cam_z + 18)
    shroud = cut(shroud_outer, box(WRIST_CAM_X - 8.8, X0 - 24.0, Y0 - 16.5, Y0 + 16.5, cam_z - 16.5, cam_z + 16.5))
    s = fuse(disc, sleeve, housing, shroud)
    tools = [box(sx0 - 0.3, sx1 + 0.3, Y0 - P.STS_W / 2 - 0.3, Y0 + P.STS_W / 2 + 0.3, J7_BODY_Z[0] - 0.01, J7_BODY_Z[1] + 0.3),
             cyl((X0, Y0, PINION_Z[0] - 1), "z", 2 * (GEAR_R + GEAR_M) + 2, J7_BODY_Z[0] - PINION_Z[0] + 1.5),
             # Pocket for the UB0234 board (x 0..1.6) and holder (x 1.6..8.6), 0.5 mm clearance.
             box(WRIST_CAM_X - 9.1, WRIST_CAM_X + 0.5, Y0 - 16.5, Y0 + 16.5, cam_z - 16.5, cam_z + 16.5),
             box(WRIST_CAM_X - 9.1, WRIST_CAM_X - 1.1, Y0 - 7.5, Y0 + 7.5, cam_z - 15.5, cam_z - 0.5)]
    for sgn in (1, -1):
        xa, xb = sorted((sgn * (RACK_X0 - 0.6), sgn * (RACK_X1 + 0.6)))
        tools.append(box(X0 + xa, X0 + xb, Y0 - HOUSING_Y - 1, Y0 + HOUSING_Y + 1, RACK_Z[0] - 0.4, RACK_Z[1] + 0.4))
        fa, fb = sorted((sgn * (RACK_X1 - 5.6), sgn * (RACK_X1 + 0.6)))
        tools.append(box(X0 + fa, X0 + fb, Y0 - HOUSING_Y - 1, Y0 + HOUSING_Y + 1, FLOOR_Z[0] - 1, RACK_Z[0]))
    tools += _horn_holes((X0, Y0, 0), "z", top1, (0, 0, -1), depth=10)
    # 28 x 28 mm camera holes and a lens window looking down the fingers.
    for dy in (-CAM_PITCH / 2, CAM_PITCH / 2):
        for dz in (-CAM_PITCH / 2, CAM_PITCH / 2):
            tools.append(cyl_between("x", (Y0 + dy, cam_z + dz), WRIST_CAM_X - 10, WRIST_CAM_X + 6, 1.8))
    tools.append(box(WRIST_CAM_X - 10, WRIST_CAM_X + 2.5, Y0 - 8, Y0 + 8, cam_z - 18.5, cam_z - 14.5))  # lens window
    # Cable channel from the camera up the back into the wrist-skirt slot.
    tools.append(box(WRIST_CAM_X - 4, WRIST_CAM_X + 2.5, Y0 - 3.2, Y0 + 3.2, cam_z + 14, top1 + 1))
    # Lid inserts, four M3, from the underside.
    for dx, dy in LID_SCREWS:
        tools.append(cyl((X0 + dx, Y0 + dy, HOUSING_Z[0] - 0.2), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 0.4))
    hw("M2x6 thread-forming (wrist camera)", 4)
    hw("M3 heat-set insert", 4)
    return cut(s, *tools)


def palm_lid() -> cq.Shape:
    """PETG lid over the pinion and racks. 1.2 mm rack clearance, four M3x8 into the palm. One solid."""
    s = rrect(X0, Y0, LID_Z[0], LID_Z[1], 48, 2 * HOUSING_Y - 8, 5)
    tools = [cyl((X0, Y0, LID_Z[0] - 1), "z", 2 * (GEAR_R + GEAR_M) + 3.0, (LID_Z[1] - LID_Z[0]) + 0.6)]
    # Staggered slots: each rack exits one Y end; a 5 mm bridge at the other end keeps one solid.
    lid_hy = HOUSING_Y - 4.0
    bridge = 5.0
    for sgn, y_lo, y_hi in ((1, Y0 - lid_hy + bridge, Y0 + lid_hy + 1), (-1, Y0 - lid_hy - 1, Y0 + lid_hy - bridge)):
        xa, xb = sorted((sgn * (RACK_X0 - 1.2), sgn * (RACK_X1 + 1.2)))
        tools.append(box(X0 + xa, X0 + xb, y_lo, y_hi, LID_Z[0] - 1, LID_Z[1] + 1))
    for dx, dy in LID_SCREWS:
        tools.append(cyl_between("z", (X0 + dx, Y0 + dy), LID_Z[0] - 1, LID_Z[1] + 1, P.M3))
        tools.append(cyl_between("z", (X0 + dx, Y0 + dy), LID_Z[0] - 1, LID_Z[0] + 1.2, P.M3_HEAD))
    hw("M3x8 socket head (palm lid)", 4)
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
    add("wrist", wrist(), "link5", color="dark", note="J5 horn and idler, holds J6. Camera cable enters the skirt at the back.")
    add("palm", palm(), "link6", color="dark", note="J6 horn on top, J7 inside, rack channels, camera shroud (28 mm pitch) and lid inserts. Print with the horn disc down.")
    add("pinion", pinion(), "link6", color="frame", note="16T module-1.5 involute on the J7 horn. 100% PETG, or use a bought metal pinion of the same size.")
    add("rack_a", rack(1), "link7", color="dark", note="PETG rack and drop. Slides in from the +y end.")
    add("rack_b", rack(-1), "link8", color="dark", note="PETG rack and drop. Slides in from the -y end.")
    add("finger_a", finger(1), "link7", color="accent", material="TPU", note="TPU 95A, 34 mm curved pad, fingernail, FSR 402 pocket. Print pad-up, 100%, no supports.")
    add("finger_b", finger(-1), "link8", color="accent", material="TPU", note="TPU 95A, 34 mm curved pad, fingernail, FSR 402 pocket.")
    add("palm_lid", palm_lid(), "link6", color="dark", note="Covers the pinion. Print skin-down. Four M3x8 into the palm. No glue.")
    import arm_covers

    for name, solid, link, note in arm_covers.parts_left():
        add(name, solid, link, color="shell", note=note)
    return out


def bought(side: str) -> list[Bought]:
    import vendor as V

    m = (lambda s: s) if side == "l" else _mirror
    out = []

    def add(name, pieces, link, kind, mass, key):
        mirrored = [(sfx, m(shp), look) for sfx, shp, look in pieces]
        out.extend(V.boughts(f"{name}_{side}", mirrored, f"{side}_{link}", "arm", kind, mass, key))

    out.extend(sv_instances(side)[1])
    j5 = [(sfx, shp, "alu" if not sfx else look) for sfx, shp, look in V.sts3215()]  # STS3250: same case, aluminium middle
    add("j5", V.place(j5, (X0, J5_BODY["y"][1], W), xdir=(0, 0, 1), zdir=(0, 1, 0)), "link4", "actuator", P.STS3250_MASS, "sts3250")
    add("j6", V.place(V.sts3215(), (X0, Y0, J6_BODY_Z[0]), xdir=(1, 0, 0), zdir=(0, 0, -1)), "link5", "actuator", P.STS_MASS, "sts3215")
    add("j7", V.place(V.sts3215(), (X0, Y0, J7_BODY_Z[0]), xdir=(1, 0, 0), zdir=(0, 0, -1)), "link6", "actuator", P.STS_MASS, "sts3215")
    add("wrist_cam", V.place(V.usb_cam(), (WRIST_CAM_X, Y0, (HOUSING_Z[0] + HOUSING_Z[1]) / 2), xdir=(-1, 0, 0), zdir=(0, 0, 1)),
        "link6", "electronics", 15, "wristcam")
    return out


def sv_instances(side: str):
    """J2..J4 servos of one arm: (parts, boughts). Cups are printed into the links."""
    import servo as G

    parts, buys = [], []
    links = {"j2": ("link1", "link2"), "j3": ("link2", "link3"), "j4": ("link3", "link4")}
    for j, frame in SV.items():
        origin, zdir, xdir, kind = frame
        fr = (origin, zdir, xdir) if side == "l" else G.mirror_frame(origin, zdir, xdir)
        pa, ch = links[j]
        p, b = G.instance(f"{j}_{side}", *fr, f"{side}_{pa}", f"{side}_{ch}", "arm", kind=kind)
        parts += p
        buys += b
    return parts, buys


def _mir_axis(a):
    return (-a[0], a[1], -a[2])


def joints(side: str) -> list[Joint]:
    sy = 1 if side == "l" else -1
    L = P.LIMITS
    raw = [
        ("shoulder_pitch", "lift", "link1", (X0, P.J1_FACE_Y, S), (0, 1, 0), "sts3095"),
        ("shoulder_roll", "link1", "link2", (X0, Y0, S), (1, 0, 0), "sts3095"),
        ("upper_arm_yaw", "link2", "link3", (X0, Y0, J3_FACE_Z), (0, 0, 1), "sts3250"),
        ("elbow", "link3", "link4", (X0, Y0, E), (0, 1, 0), "sts3095"),
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
