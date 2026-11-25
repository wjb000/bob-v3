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
# The shell is one open-bottom print that drops over the frame, eye plate and camera from
# above, so its bottom edge is straight inside (no 8 mm chamfer that would narrow the
# opening below the eye plate). The frame plate is the head's floor: it sits 8 mm up
# inside the shell skirt, and 4 screws go up through it into the shell.
HCHAMF_TOP, HCHAMF_BOT = 20.0, 1.5
SHELL_Z0 = HZ0 + 1.0  # skirt 1 mm shorter than the old floor, so the square bottom edge keeps the old chin clearance
FRAME_Z = (S + 112.0, S + 116.0)
FLOOR = dict(lx=P.HEAD_D - 2 * HWALL - 1.0, ly=P.HEAD_W - 2 * HWALL - 1.0, r=HR - HWALL - 0.5)  # 0.5 mm inside the wall
FLOOR_BOSS_H = 12.0  # shell corbel height above the frame plate
VISOR = dict(w=128.0, h=80.0, zc=S + 176.0, r=24.0)
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
    plate = rrect(HCX, 0, FRAME_Z[0], FRAME_Z[1], FLOOR["lx"], FLOOR["ly"], FLOOR["r"])
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
    for x, y in _floor_pts():  # the shell's corbels sit on the plate here
        tools.append(cyl((x, y, FRAME_Z[0] - 1), "z", P.M3, FRAME_Z[1] - FRAME_Z[0] + 2))
    hw("M3x6 screw (D435 rear)", 2)
    return cut(s, *tools)


def _floor_pts():
    """Screw points: up through the frame plate into an insert in a corbel on each side wall."""
    yi = P.HEAD_W / 2 - HWALL - 7.0
    return [(HCX - 35, -yi), (HCX - 35, yi), (HCX + 25, -yi), (HCX + 25, yi)]


def _corbel(x, sy) -> cq.Shape:
    """Boss on the inside of a side wall, standing on the frame plate. 45 degree top so the
    shell prints top-down without support under it."""
    yw = sy * (P.HEAD_W / 2 - HWALL + 1.0)  # 1 mm into the wall
    u = 13.0  # reach in from the wall
    z0, z1 = FRAME_Z[1], FRAME_Z[1] + FLOOR_BOSS_H
    pts = [(0.0, z0), (u, z0), (u, z1), (0.0, z1 + u)]
    prof = cq.Workplane("YZ").workplane(offset=x - 5.0).polyline([(yw - sy * a, z) for a, z in pts]).close().extrude(10.0)
    return prof.val()


def head_shell() -> cq.Shape:
    """One print, open at the bottom. The skirt hides the frame plate, which is the floor."""
    L, W = HX1 - HX0, P.HEAD_W
    s = rrect_shell(HCX, 0, SHELL_Z0, HZ1, L, W, HR, HWALL, chamfer_top=HCHAMF_TOP, chamfer_bot=HCHAMF_BOT, open_bot=True)
    adds, tools = [], []
    for x, y in _floor_pts():
        adds.append(_corbel(x, 1 if y > 0 else -1))
        tools.append(cyl((x, y, FRAME_Z[1] - 0.01), "z", P.M3_INSERT, P.M3_INSERT_DEPTH))
    s = fuse(s, *adds)
    s = s.intersect(rrect(HCX, 0, SHELL_Z0, HZ1, L, W, HR, chamfer_top=HCHAMF_TOP, chamfer_bot=HCHAMF_BOT))
    # visor opening
    v = VISOR
    tools.append(cq.Workplane("YZ").workplane(offset=HX1 - HWALL - 1).center(0, v["zc"]).sketch().rect(v["w"], v["h"]).vertices()
                 .fillet(v["r"]).finalize().extrude(20).val())
    # ear pods: a press-fit spigot through each side wall
    for sy in (1, -1):
        tools.append(cyl_between("y", (EAR_X, EAR_Z), sy * (P.HEAD_W / 2 - 6), sy * (P.HEAD_W / 2 + 2), EAR_SPIGOT + 0.4))
    hw("M3x10 socket head", len(_floor_pts()))
    hw("M3 heat-set insert", len(_floor_pts()))
    return cut(s, *tools)


def visor() -> cq.Shape:
    """Black visor: a plug that fills the opening plus a lip behind the wall. The eye plate clamps the lip."""
    v = VISOR
    x0 = HX1 - HWALL
    front = cq.Workplane("YZ").workplane(offset=x0).center(0, v["zc"]).sketch().rect(v["w"] - 0.6, v["h"] - 0.6).vertices() \
        .fillet(v["r"] - 0.3).finalize().extrude(HWALL - 0.4).val()
    lip = cq.Workplane("YZ").workplane(offset=x0 - 2).center(0, v["zc"]).sketch().rect(v["w"] + 8, v["h"] + 8).vertices() \
        .fillet(v["r"] + 4).finalize().extrude(2.0).val()
    s = fuse(front, lip)
    tools = []
    for y in (-EYE_Y, EYE_Y):
        tools.append(cyl_between("x", (y, EYE_Z), x0 - 5, x0 + 10, P.EYE_GLASS + 0.6))
    tools.append(cq.Workplane("YZ").workplane(offset=x0 - 5).center(0, CAM_Z).sketch().rect(P.D435[0] - 4, P.D435[2] - 6)
                 .vertices().fillet(8).finalize().extrude(20).val())
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
        Part("head_frame", head_frame(), "head_tilt", "head", color="frame", rot=(0, -90, 0),
             note="Tilt horn and idler, camera post, eye plate. Its plate is the head's floor. "
                  "Prints standing on the plate's back edge; use a brim."),
        Part("eye_plate", eye_plate(), "head_tilt", "head", color="frame", note="Two GC9A01 round TFTs."),
        Part("visor", visor(), "head_tilt", "head", color="dark", rot=(0, -90, 0),
             note="Black PETG, face down. Eye and camera windows."),
    ]
    out.append(Part("head_shell", head_shell(), "head_tilt", "head", color="shell", rot=(180, 0, 0), walls=3, infill=15,
                    note="One piece, top down, open at the bottom. Visor fits from inside. Drops over the frame; "
                         "4 M3x10 up through the frame plate into the side-wall inserts."))
    return out


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
