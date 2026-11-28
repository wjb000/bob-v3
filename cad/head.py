"""Head: pan/tilt neck on two STS3215, white shell, dark visor with two round
GC9A01 'eyes' and a RealSense D435i behind a window.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import Bought, Joint, Part, box, cbox, cut, cyl, cyl_between, fuse, hw, rrect, rrect_shell, tube_between
from arm import _horn_holes

S = P.SHOULDER_Z0
NX = P.NECK_X  # pan axis x
PAN_HORN_Z = S + 51.0  # top of the pan horn (servo face at S+47, torso top at S+50)
TILT_Z = S + P.TILT_Z
HX0, HX1 = P.HEAD_CX - P.HEAD_D / 2 + 4, P.HEAD_CX + P.HEAD_D / 2 + 4
HCX = (HX0 + HX1) / 2
HZ0, HZ1 = S + 104.0, S + 104.0 + P.HEAD_H
HR = 22.0
HWALL = 3.0
FRAME_Z = (S + 112.0, S + 116.0)
# Face door. Clears the frame plate (y ±64, z 632) and the camera post (z to 730).
# The corner radius stays small so the plate's lower corners are not pinched.
# The tilt cheeks are lower; they use the floor track, not this opening.
VISOR = dict(w=136.0, h=110.0, zc=S + 161.0, r=12.0)
# Floor groove from the neck slot to the face, so the frame slides in at its installed height.
CHEEK_TRACK = dict(x0=130.0, y0=-36.0, y1=28.0, z0=HZ0 - 6.0, z1=632.0)
EYE_Z = S + 158.0
EYE_Y = 31.0
EYE_ARM_Y = 13.0  # eye plate arms, inboard of the eye pin holes
CAM_Z = S + 196.0
# tilt servo: shaft along +Y at (NX, TILT_Z), body forward of the shaft
TILT_BODY = dict(x=(NX - P.STS_SHAFT_FROM_END, NX - P.STS_SHAFT_FROM_END + P.STS_L), y=(-22.0, 13.0),
                 z=(TILT_Z - P.STS_W / 2, TILT_Z + P.STS_W / 2))
TILT_HORN_Y = 13.0 + 4.0
POST_X = (HX1 - 38.0, HX1 - 30.0)
EAR_X, EAR_Z, EAR_D, EAR_T, EAR_SPIGOT = HCX, S + 176.0, 50.0, 6.0, 20.0
COLLAR = dict(cx=NX + 10.0, cy=-4.0, lx=70.0, ly=58.0, r=24.0, z0=S + 53.0, z1=S + 74.0)


def neck_yoke() -> cq.Shape:
    z0 = PAN_HORN_Z
    disc = cyl((NX, 0, z0), "z", 34, 5)
    tb = TILT_BODY
    cradle = box(tb["x"][0] - 3, tb["x"][1] + 3, tb["y"][0] - 3, tb["y"][1] + 0.01, tb["z"][0] - 3, tb["z"][1] + 3)
    column = box(NX - 12, NX + 12, -16, 8, z0, tb["z"][0])
    s = fuse(disc, column, cradle)
    tools = [box(tb["x"][0] - 0.3, tb["x"][1] + 0.3, tb["y"][0] - 0.3, tb["y"][1] + 5, tb["z"][0] - 0.3, tb["z"][1] + 0.3)]
    tools += _horn_holes((NX, 0, 0), "z", z0, (0, 0, 1), depth=8)
    # idler pin boss on the -Y side of the cradle
    tools.append(cyl_between("y", (NX, TILT_Z), tb["y"][0] - 4, tb["y"][0] + 1, P.M3_INSERT))
    hw("M3 heat-set insert", 1)
    return cut(s, *tools)


def head_frame() -> cq.Shape:
    tb = TILT_BODY
    plate = rrect(HX0 + 20 + 46, 0, FRAME_Z[0], FRAME_Z[1], 92, 128, 16)
    cheek_h = box(NX - 14, NX + 14, TILT_HORN_Y, TILT_HORN_Y + 5, TILT_Z - 14, FRAME_Z[1])
    cheek_i = box(NX - 14, NX + 14, tb["y"][0] - 3 - 6, tb["y"][0] - 3 - 1, TILT_Z - 14, FRAME_Z[1])
    rounds = [cyl_between("y", (NX, TILT_Z), TILT_HORN_Y, TILT_HORN_Y + 5, 28),
              cyl_between("y", (NX, TILT_Z), tb["y"][0] - 9, tb["y"][0] - 4, 28)]
    # camera post; the eye plate hangs off its front
    post = box(POST_X[0], POST_X[1], -40, 40, FRAME_Z[1] - 0.01, CAM_Z + 14)
    s = fuse(plate, cheek_h, cheek_i, *rounds, post)
    tools = _horn_holes((NX, 0, TILT_Z), "y", TILT_HORN_Y, (0, 1, 0), depth=8)
    tools.append(cyl_between("y", (NX, TILT_Z), tb["y"][0] - 10, tb["y"][0] - 3, P.M3))
    for y in (-22.5, 22.5):  # D435 rear M3 pair, VERIFY spacing
        tools.append(cyl_between("x", (y, CAM_Z), POST_X[0] - 1, POST_X[1] + 1, P.M3))
        tools.append(cyl_between("x", (y, CAM_Z), POST_X[0] - 1, POST_X[0] + 3, P.M3_HEAD))
    for y in (-EYE_ARM_Y, EYE_ARM_Y):  # eye plate screws
        tools.append(cyl_between("x", (y, EYE_Z), POST_X[0] - 1, POST_X[1] + 1, P.M3))
        tools.append(cyl_between("x", (y, EYE_Z), POST_X[0] - 1, POST_X[0] + 3, P.M3_HEAD))
    # clear the tilt cradle
    tools.append(rrect(NX + 18, -5, FRAME_Z[0] - 1, FRAME_Z[1] + 1, 92, 41, 8))
    for x, y in _floor_pts():
        tools.append(cyl((x, y, FRAME_Z[0] - 1), "z", P.M3_INSERT, 5.5))
    hw("M3x6 screw (D435 rear)", 2)
    hw("M3 heat-set insert", len(_floor_pts()))
    return cut(s, *tools)


def _floor_pts():
    return [(HCX - 50, -60.0), (HCX - 50, 60.0), (HCX + 40, -60.0), (HCX + 40, 60.0)]


def _yz(x0, x1, w, h, zc, r) -> cq.Shape:
    r = min(max(r, 0.2), w / 2 - 0.05, h / 2 - 0.05)
    return (
        cq.Workplane("YZ").workplane(offset=min(x0, x1)).center(0, zc)
        .sketch().rect(w, h).vertices().fillet(r).finalize()
        .extrude(abs(x1 - x0)).val()
    )


def _snap_sites():
    """Top and both sides. The bottom edge is the cheek track, so it has no clip."""
    v = VISOR
    zc, w, h = v["zc"], v["w"], v["h"]
    return ((0.0, zc + h / 2, 0.0, 1.0), (w / 2, zc, 1.0, 0.0), (-w / 2, zc, -1.0, 0.0))


def _edge_box(ey, ez, ny, nz, t0, t1, half_u, x0, x1) -> cq.Shape:
    """Box at an opening edge. t=0 is the edge, t>0 runs out into the bezel."""
    tc = (t0 + t1) / 2.0
    ht = abs(t1 - t0) / 2.0
    cy, cz = ey + ny * tc, ez + nz * tc
    y0 = cy - (abs(ny) * ht + abs(nz) * half_u)
    y1 = cy + (abs(ny) * ht + abs(nz) * half_u)
    z0 = cz - (abs(nz) * ht + abs(ny) * half_u)
    z1 = cz + (abs(nz) * ht + abs(ny) * half_u)
    return box(min(x0, x1), max(x0, x1), y0, y1, z0, z1)


def head_shell() -> cq.Shape:
    s = rrect_shell(HCX, 0, HZ0, HZ1, HX1 - HX0, P.HEAD_W, HR, HWALL, chamfer_top=20, chamfer_bot=8)
    adds, tools = [], []
    for x, y in _floor_pts():
        adds.append(cyl((x, y, HZ0 + 1), "z", 10, FRAME_Z[0] - HZ0 - 1))
        tools.append(cyl((x, y, HZ0 - 1), "z", P.M3, 30))
        tools.append(cyl((x, y, HZ0 - 1), "z", P.M3_HEAD, 3.5))
    s = fuse(s, *adds)
    s = s.intersect(rrect(HCX, 0, HZ0, HZ1, HX1 - HX0, P.HEAD_W, HR, chamfer_top=20, chamfer_bot=8))
    # neck slot in the floor
    tools.append(rrect(NX + 12, -3, HZ0 - 5, HZ0 + 10, 76, 66, 14))
    v = VISOR
    x_in = HX1 - HWALL
    # Carry the door back past the bottom chamfer so the frame plate does not catch a lip.
    tools.append(_yz(176.0, HX1 + 4, v["w"], v["h"], v["zc"], v["r"]))
    tr = CHEEK_TRACK
    tools.append(box(tr["x0"], HX1 + 4, tr["y0"], tr["y1"], tr["z0"], tr["z1"]))
    for ey, ez, ny, nz in _snap_sites():
        tools.append(_edge_box(ey, ez, ny, nz, -0.3, 1.35, 3.0, x_in - 0.15, x_in + 2.05))
    # ear pods: a press-fit spigot through each side wall
    for sy in (1, -1):
        tools.append(cyl_between("y", (EAR_X, EAR_Z), sy * (P.HEAD_W / 2 - 6), sy * (P.HEAD_W / 2 + 2), EAR_SPIGOT + 0.4))
    hw("M3x10 socket head", len(_floor_pts()))
    return cut(s, *tools)


def visor() -> cq.Shape:
    """Front plug. An outer lip stops it falling in; three clips hold it. The frame goes in first."""
    v = VISOR
    x_in, x_out = HX1 - HWALL, HX1
    plug = _yz(x_in - 1.0, x_out + 0.5, v["w"] - 0.8, v["h"] - 0.8, v["zc"], v["r"] - 0.4)
    lip = _yz(x_out + 0.35, x_out + 2.1, v["w"] + 4.0, v["h"] + 4.0, v["zc"], v["r"] + 2.0)
    snaps = []
    for ey, ez, ny, nz in _snap_sites():
        snaps.append(_edge_box(ey, ez, ny, nz, -2.5, -1.2, 3.2, x_in - 9.0, x_in - 0.4))
        snaps.append(_edge_box(ey, ez, ny, nz, -2.5, -1.2, 3.2, x_in - 1.05, x_in - 0.15))
        snaps.append(_edge_box(ey, ez, ny, nz, -1.2, 0.85, 2.2, x_in + 0.25, x_in + 1.45))
    s = fuse(plug, lip, *snaps)
    tools = []
    for y in (-EYE_Y, EYE_Y):
        tools.append(cyl_between("x", (y, EYE_Z), x_in - 3, x_out + 4, P.EYE_GLASS + 0.6))
    tools.append(cq.Workplane("YZ").workplane(offset=x_in - 3).center(0, CAM_Z).sketch().rect(P.D435[0] - 4, P.D435[2] - 6)
                 .vertices().fillet(8).finalize().extrude(x_out + 6 - (x_in - 3)).val())
    return cut(s, *tools)


EYE_PLATE_X = (HX1 - HWALL - 2 - 4, HX1 - HWALL - 2)


def eye_plate() -> cq.Shape:
    x0, x1 = EYE_PLATE_X
    plate = cq.Workplane("YZ").workplane(offset=x0).center(0, EYE_Z).sketch().rect(110, 46).vertices().fillet(10) \
        .finalize().extrude(x1 - x0).val()
    arms = [box(POST_X[1], x0 + 0.5, y - 7, y + 7, EYE_Z - 7, EYE_Z + 7) for y in (-EYE_ARM_Y, EYE_ARM_Y)]
    s = fuse(plate, *arms)
    tools = []
    for y in (-EYE_Y, EYE_Y):
        tools.append(cyl_between("x", (y, EYE_Z), x1 - 2.2, x1 + 1, P.EYE_PCB + 0.6))  # module recess
        tools.append(cyl_between("x", (y, EYE_Z), x0 - 1, x1, 22))  # flex / pins
    for y in (-EYE_ARM_Y, EYE_ARM_Y):
        tools.append(cyl_between("x", (y, EYE_Z), POST_X[1] - 1, POST_X[1] + 10, 2.6))
    hw("M3x12 thread-forming (eye plate)", 2)
    return cut(s, *tools)


def ear(sy) -> cq.Shape:
    """Dark ear pod: speaker and mic grille, press-fits into the side wall."""
    y0 = sy * (P.HEAD_W / 2)
    disc = cyl_between("y", (EAR_X, EAR_Z), y0, y0 + sy * EAR_T, EAR_D)
    rim = cyl_between("y", (EAR_X, EAR_Z), y0 + sy * (EAR_T - 1.5), y0 + sy * EAR_T, EAR_D - 3)
    spigot = tube_between("y", (EAR_X, EAR_Z), y0 - sy * 6, y0 + sy * 0.5, EAR_SPIGOT, EAR_SPIGOT - 4)
    s = fuse(disc.cut(rim), spigot)
    tools = []
    for r, n in ((0, 1), (6, 6), (12, 12), (18, 18)):
        for i in range(n):
            a = 2 * math.pi * i / n
            tools.append(cyl_between("y", (EAR_X + r * math.cos(a), EAR_Z + r * math.sin(a)), y0 - sy * 7, y0 + sy * 8, 2.4))
    return cut(s, *tools)


def neck_collar() -> cq.Shape:
    c = COLLAR
    return rrect_shell(c["cx"], c["cy"], c["z0"], c["z1"], c["lx"], c["ly"], c["r"], 2.4, open_top=True, open_bot=True)


def parts() -> list[Part]:
    out = [
        Part("ear_l", ear(1), "head_tilt", "head", color="dark", rot=(90, 0, 0), note="Press-fits into the head's left side. Speaker grille."),
        Part("ear_r", ear(-1), "head_tilt", "head", color="dark", rot=(-90, 0, 0), note="Mic grille."),
        Part("neck_collar", neck_collar(), "head_pan", "head", color="dark", note="Clips around the neck yoke and hides the pan servo."),
        Part("neck_yoke", neck_yoke(), "head_pan", "head", color="dark", note="Pan horn below, tilt servo cradle above."),
        Part("head_frame", head_frame(), "head_tilt", "head", color="frame", note="Tilt horn and idler, camera post, eye plate."),
        Part("eye_plate", eye_plate(), "head_tilt", "head", color="frame", note="Two GC9A01 round TFTs."),
        Part("visor", visor(), "head_tilt", "head", color="dark", rot=(0, -90, 0),
             note="Snaps in from the front after the frame. Outer lip, three clips."),
        Part("head_shell", head_shell(), "head_tilt", "head", color="shell", rot=(0, -90, 0), walls=3, infill=15,
             note="One piece, face opening up. Frame slides in through the visor; four screws up through the floor."),
    ]
    return out


def head_joiners():
    """One shell, so the head has no seam tabs."""
    return []


def bought() -> list[Bought]:
    import vendor as V

    out = []
    out += V.boughts("tilt_servo", V.place(V.sts3215(), (NX, TILT_BODY["y"][1], TILT_Z), xdir=(1, 0, 0), zdir=(0, 1, 0)),
                     "head_pan", "head", "actuator", P.STS_MASS, "sts3215")
    out += V.boughts("head_cam", V.place(V.rgb_cam(), (HX1 - HWALL - 2 - 20.5 - 0.3, 0, CAM_Z)), "head_tilt", "head", "electronics", 25, "headcam")
    out += V.boughts("esp32s3_head", V.place(V.small_board(25, 52, (10, 10, 1.5)), (HCX - 30, 0, S + 135)), "head_tilt", "head",
                     "electronics", 10, "esp32s3")
    out += V.boughts("mic_array", V.place(V.mic_array(), (HCX - 10, 0, HZ1 - 17)), "head_tilt", "head", "electronics", 20, "mic")
    for y in (-EYE_Y, EYE_Y):
        pcs = V.place(V.round_tft(), (EYE_PLATE_X[1] - 2.2, y, EYE_Z), xdir=(0, 1, 0), zdir=(1, 0, 0))
        out += V.boughts(f"eye_{'l' if y > 0 else 'r'}", pcs, "head_tilt", "head", "electronics", 8, "eye")
    return out


def joints() -> list[Joint]:
    L = P.LIMITS
    return [
        Joint("head_pan", "hinge", "lift", "head_pan", (NX, 0, PAN_HORN_Z), (0, 0, 1), L["head_pan"], "sts3215"),
        Joint("head_tilt", "hinge", "head_pan", "head_tilt", (NX, 0, TILT_Z), (0, 1, 0), L["head_tilt"], "sts3215"),
    ]
