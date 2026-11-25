"""Bought parts, modelled from their datasheet dimensions.

These are not the vendors' STEP files. They are parametric models at the published outside
dimensions, with the features that matter for fit and for looks: flanges, bolt circles, shafts,
horns, connectors, heatsinks, ports, lenses. Each model fits inside the envelope the printed parts
were designed around, so cad/export.py's collision check covers them too.

Every builder returns a list of (suffix, shape, look) in a local frame. place() puts them in the
robot frame. 'look' picks the material in the viewer and the sim.
"""

from __future__ import annotations

import math

import cadquery as cq
import numpy as np
from OCP.gp import gp_Trsf

import params as P
from lib import box, cbox, cut, cyl, cyl_between, fuse, rrect, tube_between


# ---------------------------------------------------------------- placement

def boughts(name, pieces, link, group, kind, mass, bom):
    """One Bought per piece; the first carries the mass and the BOM key."""
    from lib import Bought

    out = []
    for i, (sfx, shp, look) in enumerate(pieces):
        nm = name if not sfx else f"{name}_{sfx}"
        out.append(Bought(nm, shp, link, group, kind, mass if i == 0 else 0.0, bom, look=look))
    return out


def place(pieces, origin, xdir=(1, 0, 0), zdir=(0, 0, 1)):
    """Map a local frame (x, y = z cross x, z) onto the robot frame at origin."""
    x = np.asarray(xdir, float)
    z = np.asarray(zdir, float)
    x, z = x / np.linalg.norm(x), z / np.linalg.norm(z)
    y = np.cross(z, x)
    R = np.column_stack([x, y, z])
    t = gp_Trsf()
    o = origin
    t.SetValues(*(float(v) for v in (R[0, 0], R[0, 1], R[0, 2], o[0], R[1, 0], R[1, 1], R[1, 2], o[1],
                                     R[2, 0], R[2, 1], R[2, 2], o[2])))
    loc = cq.Location(t)
    return [(sfx, shp.moved(loc), look) for sfx, shp, look in pieces]


def _ring_holes(n, pcd, d, z0, z1, start=0.0):
    out = []
    for i in range(n):
        a = math.radians(start) + 2 * math.pi * i / n
        out.append(cyl((pcd / 2 * math.cos(a), pcd / 2 * math.sin(a), z0), "z", d, z1 - z0))
    return out


def _fillet(shape, r):
    try:
        return cq.Workplane().add(shape).edges().fillet(r).val()
    except Exception:  # noqa: BLE001 - keep the plain shape if OCC can't fillet it
        return shape


# ---------------------------------------------------------------- Damiao DM-J4340 / DM-J4310

def damiao(kind: str):
    """Local frame: +z is the output, the output face is z = 0, the body is -H..0, the output disc 0..2."""
    D, H = (P.DM4340_D, P.DM4340_H) if kind == "dm4340" else (P.DM4310_D, P.DM4310_H)
    body = cyl((0, 0, -H + 2), "z", D, H - 4)
    front = cyl((0, 0, -2), "z", D - 3, 2)  # stepped front ring around the output
    rear = cyl((0, 0, -H), "z", D - 2, 2)  # rear cover
    shell = fuse(body, front, rear)
    shell = cut(shell, cyl((0, 0, -H - 1), "z", D - 12, 1.6))  # rear cover recess
    shell = cut(shell, *[tube_between("z", (0, 0), z, z + 1.2, D + 1, D - 1.0) for z in (-H + 9, -H + 13, -H + 17)])
    for x, y in [(P.DM_REAR_PCD / 2 * math.cos(a), P.DM_REAR_PCD / 2 * math.sin(a)) for a in
                 [math.pi / 4 + i * math.pi / 2 for i in range(P.DM_REAR_N)]]:
        shell = cut(shell, cyl((x, y, -H - 1), "z", 2.6, 4))
    disc = cyl((0, 0, 0), "z", P.DM_OUT_D, 2)
    disc = cut(disc, cyl((0, 0, -1), "z", 12, 4), *_ring_holes(P.DM_OUT_N, P.DM_OUT_PCD, 2.6, -1, 3))
    # XT30 and CAN (GH 2-pin) on the rear face, inside the cup's cable hole
    xt30 = cbox(-2.5, 0, -H - 2.4, 5.0, 10.0, 4.8)
    can = cbox(5.0, 0, -H - 1.8, 4.0, 6.0, 3.6)
    return [("", shell, "anodised"), ("out", disc, "alu"), ("conn", fuse(xt30, can), "yellow")]


# ---------------------------------------------------------------- Feetech STS3215

def sts3215():
    """Local frame: the shaft is +z at the origin, the top face is z = 0, the case is x -11.5..33.7, y +-12.35, z -35..0."""
    L, W, H, s = P.STS_L, P.STS_W, P.STS_H, P.STS_SHAFT_FROM_END
    x0, x1 = -s, L - s
    case = _fillet(box(x0, x1, -W / 2, W / 2, -H + 3, -3), 1.2)
    top = _fillet(box(x0 + 0.5, x1 - 0.5, -W / 2 + 0.5, W / 2 - 0.5, -3, -0.01), 1.0)
    bottom = _fillet(box(x0 + 0.5, x1 - 0.5, -W / 2 + 0.5, W / 2 - 0.5, -H, -H + 3.01), 1.0)
    shell = fuse(case, top, bottom)
    # screws in the bottom cover, a label recess and the two bus connectors flush in the far end
    for x in (x0 + 4, x1 - 4):
        for y in (-W / 2 + 4, W / 2 - 4):
            shell = cut(shell, cyl((x, y, -H - 1), "z", 2.0, 2))
    shell = cut(shell, box(x0 + 8, x1 - 8, W / 2 - 0.4, W / 2 + 1, -H + 9, -9))
    for z in (-H + 8, -H + 18):
        shell = cut(shell, box(x1 - 0.8, x1 + 1, -4, 4, z, z + 6))
    boss = cyl((0, 0, -0.01), "z", 9.0, 1.0)
    horn = cut(cyl((0, 0, 0.99), "z", P.STS_HORN_D, 3.0),
               *_ring_holes(4, P.STS_HORN_PCD, 2.2, 0, 5, 45), cyl((0, 0, 0), "z", 3.2, 5))
    return [("", shell, "black"), ("horn", fuse(boss, horn), "white")]


def sts3095():
    """Local frame: shaft +z at the origin, top face z = 0, case x -16.5..48.5, y ±15, z -48..0.

    Dual shaft: 15T horn on +z, rear spline on −z. Aluminium case.
    """
    L, W, H, s = P.STS3095_L, P.STS3095_W, P.STS3095_H, P.STS3095_SHAFT_FROM_END
    x0, x1 = -s, L - s
    case = _fillet(box(x0, x1, -W / 2, W / 2, -H + 4, -3), 1.5)
    top = _fillet(box(x0 + 0.6, x1 - 0.6, -W / 2 + 0.4, W / 2 - 0.4, -3, -0.01), 1.2)
    bottom = _fillet(box(x0 + 0.6, x1 - 0.6, -W / 2 + 0.4, W / 2 - 0.4, -H, -H + 4.01), 1.2)
    shell = fuse(case, top, bottom)
    cx = (x0 + x1) / 2
    for dx in (-P.STS3095_HOLE_L / 2, P.STS3095_HOLE_L / 2):
        for dy in (-P.STS3095_HOLE_W / 2, P.STS3095_HOLE_W / 2):
            shell = cut(shell, cyl((cx + dx, dy, -4), "z", 3.3, 6))
    for z in (-H + 10, -H + 22):
        shell = cut(shell, box(x1 - 0.8, x1 + 1, -5, 5, z, z + 7))
    boss = cyl((0, 0, -0.01), "z", 11.0, 1.0)
    horn = cut(cyl((0, 0, 0.5), "z", P.STS3095_HORN_D, 2.5),
               *_ring_holes(4, P.STS3095_HORN_PCD, 3.2, 0, 5, 45), cyl((0, 0, 0), "z", 4.0, 5))
    rear = cyl((0, 0, -H - 8), "z", P.STS3095_SPLINE_D, 8)
    return [("", shell, "alu"), ("horn", fuse(boss, horn), "steel"), ("shaft", rear, "steel")]


# ---------------------------------------------------------------- NEMA 17, 48 mm

def nema17():
    """Local frame: face at z = 0, body +z, shaft -z."""
    S, L = P.NEMA_SIZE, P.NEMA_LEN
    cap_f = rrect(0, 0, 0, 9, S, S, 3)
    cap_f = cap_f.intersect(cq.Workplane("XY").polygon(8, S * 1.235).extrude(9).val().rotate((0, 0, 0), (0, 0, 1), 22.5))
    stack = rrect(0, 0, 9, L - 9, S - 0.6, S - 0.6, 2)
    cap_r = cap_f.translate((0, 0, L - 9))
    body = fuse(cap_f, cap_r)
    for x in (-P.NEMA_BOLT / 2, P.NEMA_BOLT / 2):
        for y in (-P.NEMA_BOLT / 2, P.NEMA_BOLT / 2):
            body = cut(body, cyl((x, y, -1), "z", 3.0, 5))
    pilot = cyl((0, 0, -2), "z", P.NEMA_PILOT, 2)
    shaft = cyl((0, 0, -10), "z", 5.0, 8).cut(box(1.5, 4, -4, 4, -11, -3))
    conn = cbox(0, S / 2 + 2.5, L - 6, 16, 5, 7)
    return [("", fuse(body, pilot), "alu"), ("stack", stack, "black"), ("shaft", shaft, "steel"), ("conn", conn, "white")]


# ---------------------------------------------------------------- hoverboard hub motor

def hub_motor(side):
    """Local frame: wheel axis +z pointing outboard, centred at the origin; the axle points -z."""
    R, Wd = P.WHEEL_OD / 2, P.WHEEL_W
    tire = cut(tube_between("z", (0, 0), -Wd / 2, Wd / 2, 2 * R, 2 * R - 34),
               *[tube_between("z", (0, 0), z - 1.0, z + 1.0, 2 * R + 2, 2 * R - 5) for z in (-12.0, -4.0, 4.0, 12.0)])
    hub = cyl((0, 0, -Wd / 2 - 2), "z", 2 * R - 34, Wd + 4)
    hub = cut(hub, *[cyl((38 * math.cos(a), 38 * math.sin(a), Wd / 2 + 1), "z", 7, 2) for a in
                     [i * 2 * math.pi / 5 for i in range(5)]])
    axle_len = P.WHEEL_Y - P.WHEEL_W / 2 - 112.0
    axle = cyl((0, 0, -Wd / 2 - axle_len), "z", P.AXLE_D, axle_len - 2.0).intersect(
        box(-20, 20, -P.AXLE_FLATS / 2, P.AXLE_FLATS / 2, -200, 0))
    cable = cyl((3.5, 0, -Wd / 2 - axle_len - 8), "z", 4.0, 8.01)
    return [("", tire, "rubber"), ("hub", hub, "alu"), ("axle", fuse(axle, cable), "steel")]


# ---------------------------------------------------------------- electronics

def pcb(lx, ly, t=1.6, holes=()):
    s = rrect(0, 0, 0, t, lx, ly, 1.5)
    for x, y in holes:
        s = cut(s, cyl((x, y, -1), "z", 3.2, t + 2))
    return s


def jetson():
    """Orin Nano Super dev kit. Local: carrier board in XY (103 x 90.5), components up +z, 34.8 total."""
    lx, ly = P.JETSON[0], P.JETSON[1]
    board = pcb(lx, ly, holes=[(sx * 43, sy * 36) for sx in (-1, 1) for sy in (-1, 1)]).translate((0, 0, 3))
    feet = fuse(*[cyl((sx * 43, sy * 36, 0), "z", 5, 3) for sx in (-1, 1) for sy in (-1, 1)])
    module = box(-40, 30, -10, 35, 4.6, 7.6)
    sink = box(-39, 29, -9, 34, 7.6, 12.0)
    fins = fuse(*[box(-39 + i * 4.25, -39 + i * 4.25 + 1.4, -9, 34, 12.0, 27.0) for i in range(16)])
    fan = cut(cyl((-5, 12, 27.0), "z", 40, 7.8), cyl((-5, 12, 33), "z", 14, 2))
    ports = fuse(
        box(lx / 2 - 18, lx / 2, -40, -26, 4.6, 20.6),  # USB-A stack
        box(lx / 2 - 21, lx / 2, -22, -6, 4.6, 18.1),  # RJ45
        box(lx / 2 - 9, lx / 2, 0, 17, 4.6, 9.6),  # DisplayPort
        box(lx / 2 - 8, lx / 2, 22, 31, 4.6, 8.0),  # USB-C
        cyl((lx / 2 - 7, 38, 4.6), "z", 9, 11),  # barrel jack
    )
    return [("", board, "pcb_black"), ("feet", feet, "steel"), ("module", module, "pcb"), ("sink", fuse(sink, fins), "alu"),
            ("fan", fan, "black"), ("ports", ports, "steel")]


def d435():
    """RealSense D435i. Local: x forward (the glass), y along the 90 mm length, z up. Origin at the centre."""
    L, H, D = P.D435[0], P.D435[1], P.D435[2]
    body = cq.Workplane("YZ").workplane(offset=-D / 2).sketch().rect(L, H).vertices().fillet(H / 2 - 0.5).finalize().extrude(D - 1).val()
    glass = cq.Workplane("YZ").workplane(offset=D / 2 - 1).sketch().rect(L - 4, H - 4).vertices().fillet(H / 2 - 2.5).finalize().extrude(1).val()
    lenses = []
    for y, d in ((-32.5, 6.0), (17.5, 6.0), (-9.0, 8.5), (32.0, 6.0)):  # IR left, IR right, projector, RGB
        lenses.append(cyl((D / 2 - 0.2, y, 0), "x", d, 0.3))
    holes = [cyl((-D / 2 - 1, y, 0), "x", 3.0, 5) for y in (-22.5, 22.5)]
    return [("", cut(body, *holes), "alu"), ("glass", glass, "glass"), ("lens", fuse(*lenses), "lens")]


def rplidar_c1():
    """Local: base on z = 0, Ø55.6 x 41.3."""
    base = cyl((0, 0, 0), "z", P.LIDAR_D, 22)
    window = cyl((0, 0, 22), "z", P.LIDAR_D - 4, 14)
    cap = cyl((0, 0, 36), "z", P.LIDAR_D - 6, P.LIDAR_H - 36)
    cap = cut(cap, cyl((0, 0, P.LIDAR_H - 1.2), "z", 30, 2))
    return [("", fuse(base, cap), "black"), ("window", window, "glass")]


def zsx11h():
    """ZS-X11H. Local: board on z = 0, 63 x 45, max 22 tall."""
    b = pcb(63, 45)
    sink = fuse(box(-30, 2, -20, 20, 1.6, 6.0), *[box(-30 + i * 3.6, -28.6 + i * 3.6, -20, 20, 6.0, 17.0) for i in range(9)])
    caps = fuse(*[cyl((10 + 9 * i, 12, 1.6), "z", 8, 15) for i in range(2)], cyl((19, -10, 1.6), "z", 10, 18))
    terms = fuse(box(26, 31.5, -22, 22, 1.6, 12), box(2, 24, 17, 22.5, 1.6, 9))
    return [("", b, "pcb"), ("sink", sink, "alu"), ("caps", caps, "black"), ("terms", terms, "green")]


def esp32_devkit():
    b = pcb(52, 28)
    mod = box(-26, -7.5, -9, 9, 1.6, 4.6)
    shield = box(-24, -10, -8, 8, 4.6, 5.4)
    usb = box(22, 26, -4, 4, 1.6, 4.6)
    pins = fuse(box(-24, 24, 11.5, 14, -8.5, 0), box(-24, 24, -14, -11.5, -8.5, 0))
    return [("", b, "pcb_black"), ("module", fuse(mod, usb), "steel"), ("shield", shield, "steel"), ("pins", pins, "black")]


def small_board(lx, ly, chip=(8, 8, 1.2), header=True, look="pcb_blue"):
    b = pcb(lx, ly)
    c = box(-chip[0] / 2, chip[0] / 2, -chip[1] / 2, chip[1] / 2, 1.6, 1.6 + chip[2])
    pieces = [("", b, look), ("chip", c, "black")]
    if header:
        pieces.append(("pins", box(-lx / 2 + 2, lx / 2 - 2, -ly / 2 + 0.5, -ly / 2 + 3, 1.6, 4.0), "black"))
    return pieces


def finned_buck(lx, ly, lz):
    """Aluminium-case DC-DC converter with long fins and a terminal strip at each end."""
    core = box(-lx / 2 + 8, lx / 2 - 8, -ly / 2, ly / 2, 0, lz * 0.45)
    fins = fuse(*[box(-lx / 2 + 8, lx / 2 - 8, -ly / 2 + i * (ly / 9), -ly / 2 + i * (ly / 9) + ly / 22, lz * 0.45, lz)
                  for i in range(10)])
    flanges = fuse(box(-lx / 2, -lx / 2 + 8, -ly / 2, ly / 2, 0, 3), box(lx / 2 - 8, lx / 2, -ly / 2, ly / 2, 0, 3))
    terms = fuse(box(-lx / 2 + 1, -lx / 2 + 7, -ly / 2 + 6, ly / 2 - 6, 3, 13), box(lx / 2 - 7, lx / 2 - 1, -ly / 2 + 6, ly / 2 - 6, 3, 13))
    return [("", fuse(core, fins, flanges), "alu"), ("terms", terms, "black")]


def open_buck(lx, ly, lz):
    b = pcb(lx, ly)
    sink = fuse(*[box(-lx / 2 + 6 + i * 4, -lx / 2 + 8 + i * 4, -ly / 2 + 4, ly / 2 - 4, 1.6, lz * 0.8) for i in range(6)])
    ind = cyl((lx / 2 - 14, 0, 1.6), "z", 16, lz * 0.55)
    cap = cyl((lx / 2 - 14, ly / 2 - 7, 1.6), "z", 8, lz * 0.75)
    terms = box(-lx / 2 + 1, -lx / 2 + 6, -ly / 2 + 4, ly / 2 - 4, 1.6, 10)
    return [("", b, "pcb_blue"), ("sink", sink, "alu"), ("ind", ind, "copper"), ("cap", cap, "black"), ("terms", terms, "green")]


def fuse_block(lx, ly, lz):
    base = rrect(0, 0, 0, 10, lx, ly, 2)
    lid = rrect(0, 0, 18, lz, lx - 4, ly - 4, 2)
    colors = []
    for i in range(6):
        colors.append(box(-lx / 2 + 4 + i * 5.6, -lx / 2 + 8 + i * 5.6, -6, 6, 10, 18))
    return [("", base, "black"), ("lid", lid, "smoke"), ("fuses", fuse(*colors), "red")]


def contactor(lx, ly, lz):
    body = rrect(0, 0, 0, lz - 6, lx, ly, 6)
    studs = fuse(cyl((-lx / 4, 0, lz - 6), "z", 6, 6), cyl((lx / 4, 0, lz - 6), "z", 6, 6))
    return [("", body, "black"), ("studs", studs, "copper")]


def battery():
    bx, by, bz = P.BATT
    pack = _fillet(box(-bx / 2, bx / 2, -by / 2, by / 2, 0, bz), 6)
    label = box(-bx / 2 + 8, bx / 2 - 8, -by / 2 + 20, by / 2 - 20, bz, bz + 0.3)
    lead = cyl((0, by / 2 - 12, bz), "z", 6, 3)
    return [("", pack, "battery"), ("label", label, "white"), ("lead", lead, "red")]


def estop():
    body = cyl((0, 0, -45), "z", 22, 45)
    ring = cyl((0, 0, 0), "z", 34, 6)
    head = cyl((0, 0, 6), "z", 40, 16)
    head = _fillet(head, 3)
    return [("", body, "black"), ("ring", ring, "yellow"), ("head", head, "red")]


def usb_board(lx, ly, lz, ports=2):
    b = pcb(lx, ly)
    p = fuse(*[box(lx / 2 - 14, lx / 2, -ly / 2 + 4 + i * 14, -ly / 2 + 17 + i * 14, 1.6, 8.6) for i in range(ports)])
    return [("", b, "pcb"), ("ports", p, "steel")]


def speaker():
    frame = tube_between("z", (0, 0), 0, 4, 40, 34)
    cone = cyl((0, 0, -6), "z", 34, 6)
    mag = cyl((0, 0, -10), "z", 20, 4)
    return [("", fuse(frame, mag), "black"), ("cone", cone, "grey")]


def mic_array():
    b = pcb(60, 60)
    mics = fuse(*[cyl((22 * math.cos(a), 22 * math.sin(a), 1.6), "z", 3, 1) for a in [i * math.pi / 2 for i in range(4)]])
    leds = fuse(*[cyl((26 * math.cos(a), 26 * math.sin(a), 1.6), "z", 2.5, 1) for a in [i * math.pi / 6 for i in range(12)]])
    chip = box(-6, 6, -6, 6, 1.6, 3)
    return [("", b, "pcb_black"), ("mics", mics, "steel"), ("leds", leds, "eye"), ("chip", chip, "black")]


def round_tft():
    """GC9A01 module. Local: PCB face on z = 0, glass +z."""
    b = cyl((0, 0, 0), "z", P.EYE_PCB, 1.6)
    glass = cyl((0, 0, 1.6), "z", P.EYE_GLASS, 0.6)
    return [("", b, "pcb_blue"), ("glass", glass, "eye")]


def usb_cam():
    """32 x 32 board camera. Local: board in YZ at x 0..1.6, lens barrel pointing down (-z) at the lower edge."""
    b = box(0, 1.6, -16, 16, -16, 16)  # Arducam UB0234: 32 x 32 board, M12 lens
    holder = box(1.6, 8.6, -7, 7, -15, -1)
    glass = cyl((5.1, 0, -15.6), "z", 6, 0.6)
    return [("", b, "pcb"), ("holder", holder, "black"), ("lens", glass, "lens")]


def lm12uu():
    s = tube_between("z", (0, 0), -15, 15, 21.0, 12.0)
    s = cut(s, *[tube_between("z", (0, 0), z - 0.6, z + 0.6, 22.0, 19.8) for z in (-11.0, 11.0)])
    return [("", s, "steel")]


def coupler():
    s = tube_between("z", (0, 0), 0, 25, 19, 8.2)
    s = cut(s, *[tube_between("z", (0, 0), z, z + 0.8, 20, 12).intersect(box(-12, 12, -12, 3, z - 1, z + 2))
                 for z in (7.0, 10.0, 13.0, 16.0)])
    return [("", s, "alu")]


def pi5():
    """Raspberry Pi 5 with the active cooler. Local: board in XY (85 x 56), parts up +z."""
    b = pcb(85, 56, holes=[(sx * 29, sy * 24.5) for sx in (-1, 1) for sy in (-1, 1)]).translate((0, 0, 3))
    feet = fuse(*[cyl((sx * 29, sy * 24.5, 0), "z", 5, 3) for sx in (-1, 1) for sy in (-1, 1)])
    cooler = fuse(box(-30, 12, -24, 18, 4.6, 8.0), *[box(-30 + i * 3.0, -29 + i * 3.0, -24, 18, 8.0, 14.0) for i in range(14)])
    fan = cut(cyl((-9, -3, 14), "z", 30, 4), cyl((-9, -3, 17), "z", 10, 2))
    ports = fuse(box(28, 42.5, -27, -12, 4.6, 20.6), box(28, 42.5, -9, 6, 4.6, 20.6), box(26, 42.5, 10, 26, 4.6, 18))
    return [("", b, "pcb"), ("feet", feet, "steel"), ("cooler", fuse(cooler), "alu"), ("fan", fan, "black"), ("ports", ports, "steel")]


def rgb_cam():
    """Wide-angle USB RGB camera module (38 x 38 board, M12 lens). Local: x forward through the lens, origin at the board."""
    b = box(-1.6, 0, -19, 19, -19, 19)
    holder = box(0, 8, -8, 8, -8, 8)
    lens = cyl((8, 0, 0), "x", 14, 12)
    glass = cyl((20, 0, 0), "x", 10, 0.5)
    return [("", b, "pcb"), ("holder", holder, "black"), ("lens", lens, "black"), ("glass", glass, "lens")]


def ddsm115():
    """Waveshare DDSM115 from its published STEP: (rotating pieces, stationary pieces).
    Local frame: z along the axle pointing outboard, origin at the tire centre."""
    R, W = P.WHEEL_OD / 2, P.WHEEL_W
    tire = cut(tube_between("z", (0, 0), -W / 2, W / 2, 2 * R, 67.0),
               *[tube_between("z", (0, 0), z - 0.8, z + 0.8, 2 * R + 2, 2 * R - 4) for z in (-14.0, -5.0, 5.0, 14.0)])
    hub = cyl((0, 0, -P.DDSM_ROTOR_IN), "z", 67.0, P.DDSM_ROTOR_IN + W / 2 + 2.0)
    cover = cut(cyl((0, 0, W / 2 + 2.0), "z", 67.0, 7.0), *[cyl((10.5 * math.cos(a), 10.5 * math.sin(a), W / 2 + 7.5), "z", 4.5, 2)
                                                         for a in (0.5, 2.6, 4.7)])
    stub = cyl((0, 0, -P.DDSM_STUB_END), "z", P.DDSM_STUB_D, P.DDSM_STUB_END - P.DDSM_ROTOR_IN + 0.01)
    for a in (90, 210, 330):
        r = math.radians(a)
        stub = cut(stub, cyl((P.DDSM_PCD / 2 * math.cos(r), P.DDSM_PCD / 2 * math.sin(r), -P.DDSM_STUB_END - 1), "z", 2.05, 7))
    rot = [("", tire, "rubber"), ("hub", hub, "anodised"), ("cover", cover, "black")]
    stat = [("", stub, "alu")]
    return rot, stat


def dewalt_pack():
    """DeWalt 20V MAX pack on a wire adapter, as an envelope with margin. Local: base on z = 0."""
    bx, by, bz = P.BATT
    body = _fillet(box(-bx / 2 + 2, bx / 2 - 2, -by / 2 + 4, by / 2 - 4, 0, 62), 5)
    band = box(-bx / 2 + 2, bx / 2 - 2, -by / 2 + 4, by / 2 - 4, 62, 70)
    adapter = _fillet(box(-bx / 2 + 8, bx / 2 - 8, -by / 2 + 10, by / 2 - 10, 70, bz - 2), 3)
    lead = cyl((0, by / 2 - 16, bz - 2), "z", 6, 2)
    return [("", body, "black"), ("band", band, "yellow"), ("adapter", adapter, "black"), ("lead", lead, "red")]


def battery_switch():
    """Blue Sea 6006 m-Series mini ON-OFF. Local: panel outer face at z = 0, knob +z, body -z.

    Catalogue: 21/32 in (16.7 mm) panel hole, 3/8 in studs, 0.29 kg. Face and body
    envelopes are drawn from the published outline; MEASURE yours.
    """
    face = cyl((0, 0, 0), "z", 48, 6)
    knob = cyl((0, 0, 6), "z", 40, 16)
    body = cyl((0, 0, -42), "z", 30, 42)
    studs = fuse(cyl((-12, 0, -50), "z", 9.5, 8), cyl((12, 0, -50), "z", 9.5, 8))
    return [("", fuse(face, body), "black"), ("knob", knob, "red"), ("studs", studs, "copper")]


def gx16():
    """GX16 3-pin panel socket, the hoverboard charge connector. Local: panel top face at z = 0."""
    flange = cyl((0, 0, 0), "z", 21, 2.5)
    nut = cyl((0, 0, -12), "z", 19, 3).cut(cyl((0, 0, -13), "z", 16, 5))
    body = cyl((0, 0, -22), "z", 15.8, 22)
    face = cyl((0, 0, 2.5), "z", 15, 1.5).cut(cyl((0, 0, 3), "z", 11, 2))
    return [("", fuse(flange, face), "steel"), ("body", fuse(body, nut), "black")]
