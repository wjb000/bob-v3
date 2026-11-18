"""Mobile base: rounded shell, ribbed floor pan, hub clamps, casters, shelves.

The pan is the structure. The shell is skin: it sits on lugs on the pan and its
tiles are joined from the inside with identical joiner tabs, so no screw head
shows on the top or the sides.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P
from lib import (
    Bought, Part, box, cbox, cut, cyl, cyl_between, fuse, hexagon, hw, largest,
    rr_boundary, rrect, rrect_shell, tube_between,
)

# ---------------------------------------------------------------- layout

SHELL_LX, SHELL_LY = P.BASE_L, P.BASE_W
INNER_LX, INNER_LY = SHELL_LX - 2 * P.BASE_WALL, SHELL_LY - 2 * P.BASE_WALL
PAN_LX, PAN_LY = SHELL_LX - 2 * P.PAN_INSET, SHELL_LY - 2 * P.PAN_INSET
PAN_R = P.BASE_R - P.PAN_INSET
TOP_CHAMFER = 20.0

MAST_HOLE = (P.MAST_X - P.MAST_DX / 2 - 4, P.MAST_X + P.MAST_DX / 2 + 4, P.MAST_DY / 2 + 4)
MAST_FLANGE = 14.0  # mast foot overhang on the pan
ESTOP_XY = (-205.0, 0.0)
LIGHT_Z = (196.0, 202.0)

BATT_C = (90.0, 0.0)
BATT_Z0 = P.PAN_TOP + 4.0  # sits on the joiner tabs
SHELF_Z = 130.0
SHELF_T = 4.0

# Every M3 insert in the pan, named, so parts and seams can avoid each other.
PAN_PTS: dict[str, list[tuple[float, float]]] = {}


def _mast_foot_pts():
    x0, x1 = P.MAST_X - P.MAST_DX / 2, P.MAST_X + P.MAST_DX / 2
    f = MAST_FLANGE / 2 + 1
    return [(x0 - f, -35), (x0 - f, 35), (x1 + f, -45), (x1 + f, 45),
            (P.MAST_X - 25, -(P.MAST_DY / 2 + f)), (P.MAST_X - 25, P.MAST_DY / 2 + f),
            (P.MAST_X + 25, -(P.MAST_DY / 2 + f)), (P.MAST_X + 25, P.MAST_DY / 2 + f)]


def _axle_pts(side):
    y = side
    return [(-24, y * 118), (24, y * 118), (-24, y * 150), (24, y * 150)]


def _caster_pts(cx):
    return [(cx - 30, -66), (cx - 30, 66), (cx + 30, -66), (cx + 30, 66)]


FRONT_SHELF_PTS = [(40, 110), (146, 110), (146, 14)]
REAR_SHELF_PTS = [(-106, 30), (-106, 130), (-160, 125), (-250, 125)]
CRADLE_PTS = [(62, 114), (118, 114), (62, -114), (118, -114)]
LUG_PTS = []


def _lug_points():
    pts = []
    # front / rear, clear of the caster holes
    for sx in (1, -1):
        for sy in (1, -1):
            pts.append((sx * (PAN_LX / 2 - 6), sy * 70.0))
    # corner arcs at 45 degrees
    cx0, cy0 = PAN_LX / 2 - PAN_R, PAN_LY / 2 - PAN_R
    for sx in (1, -1):
        for sy in (1, -1):
            r = PAN_R - 6
            pts.append((sx * (cx0 + r * math.cos(math.pi / 4)), sy * (cy0 + r * math.sin(math.pi / 4))))
    # sides, outside the wheel cut
    for x in (140.0, -150.0):
        for sy in (1, -1):
            pts.append((x, sy * (rr_boundary("x", x, PAN_LX, PAN_LY, PAN_R) - 6)))
    return pts


def _register():
    PAN_PTS.clear()
    PAN_PTS["mast"] = _mast_foot_pts()
    PAN_PTS["axle_l"] = _axle_pts(1)
    PAN_PTS["axle_r"] = _axle_pts(-1)
    PAN_PTS["caster_f"] = _caster_pts(P.CASTER_X)
    PAN_PTS["caster_r"] = _caster_pts(-P.CASTER_X)
    PAN_PTS["shelf_fl"] = FRONT_SHELF_PTS
    PAN_PTS["shelf_fr"] = [(x, -y) for x, y in FRONT_SHELF_PTS]
    PAN_PTS["shelf_rl"] = REAR_SHELF_PTS
    PAN_PTS["shelf_rr"] = [(x, -y) for x, y in REAR_SHELF_PTS]
    PAN_PTS["cradle"] = CRADLE_PTS
    LUG_PTS[:] = _lug_points()
    PAN_PTS["lug"] = list(LUG_PTS)


_register()


def _all_pan_pts():
    return [p for v in PAN_PTS.values() for p in v]


def _clear(p, others, r=15.0):
    return all(math.hypot(p[0] - o[0], p[1] - o[1]) >= r for o in others)


# ---------------------------------------------------------------- seams

JOIN_OFF = 8.0  # insert each side of a seam
TAB = (30.0, 14.0, 4.0)


def _top_seam_pairs():
    """Shell top seams: pairs of insert points straddling each cut line."""
    pairs = []
    flat_x = SHELL_LX / 2 - TOP_CHAMFER - 12
    flat_y = SHELL_LY / 2 - TOP_CHAMFER - 12
    mx0, mx1, my = MAST_HOLE
    for gx in P.GRID_X:
        for y in (-178.0, -132.0, -45.0, 45.0, 132.0, 178.0):
            if abs(y) > flat_y:
                continue
            a, b = (gx - JOIN_OFF, y), (gx + JOIN_OFF, y)
            if any(mx0 - 8 < q[0] < mx1 + 8 and abs(q[1]) < my + 8 for q in (a, b)):
                continue
            if any(abs(y - gy) < 16 for gy in P.GRID_Y):
                continue
            pairs.append(("x", a, b))
    for gy in P.GRID_Y:
        for x in (-232.0, -165.0, -40.0, 30.0, 140.0, 222.0):
            if abs(x) > flat_x:
                continue
            if any(abs(x - gx) < 16 for gx in P.GRID_X):
                continue
            a, b = (x, gy - JOIN_OFF), (x, gy + JOIN_OFF)
            pairs.append(("y", a, b))
    return pairs


def _arch_top(x):
    if abs(x) >= P.WHEEL_ARCH_R:
        return 0.0
    return P.AXLE_Z + math.sqrt(P.WHEEL_ARCH_R ** 2 - x * x)


def _wall_seam_pairs():
    """(kind, p_a, p_b, inward normal) on the inner wall face at each seam."""
    out = []
    zs = (95.0, 160.0, 210.0)
    # side walls, seams at x = GRID_X
    for gx in P.GRID_X:
        for sy in (1, -1):
            for z in zs:
                a = (gx - JOIN_OFF, sy * INNER_LY / 2, z)
                b = (gx + JOIN_OFF, sy * INNER_LY / 2, z)
                if z < max(_arch_top(a[0]), _arch_top(b[0])) + 14:
                    continue
                out.append(("side", a, b, (0, -sy, 0)))
    # front / rear walls, seams at y = GRID_Y
    for gy in P.GRID_Y:
        for sx in (1, -1):
            for z in zs:
                if sx > 0 and 112 < z < 160:
                    continue  # lidar slot
                ya, yb = gy - JOIN_OFF, gy + JOIN_OFF
                xa = sx * rr_boundary("y", ya, INNER_LX, INNER_LY, P.BASE_R - P.BASE_WALL)
                xb = sx * rr_boundary("y", yb, INNER_LX, INNER_LY, P.BASE_R - P.BASE_WALL)
                out.append(("end", (xa, ya, z), (xb, yb, z), (-sx, 0, 0)))
    return out


def tab_at(a, b, n, standoff=9.0) -> cq.Shape:
    """A joiner tab whose long axis runs a->b and whose thickness grows along n from standoff."""
    l, w, t = TAB
    c = [(a[i] + b[i]) / 2 + n[i] * standoff for i in range(3)]
    d = [b[i] - a[i] for i in range(3)]
    plane = cq.Plane(origin=tuple(c), xDir=tuple(d), normal=tuple(n))
    wp = cq.Workplane(plane).sketch().rect(l, w).vertices().fillet(4).finalize().extrude(t)
    wp = wp.faces(">Z").workplane().pushPoints([(-JOIN_OFF, 0), (JOIN_OFF, 0)]).hole(P.M3)
    return wp.val()


def joiner_tab() -> cq.Shape:
    l, w, t = TAB
    s = rrect(0, 0, 0, t, l, w, 4)
    for dx in (-JOIN_OFF, JOIN_OFF):
        s = s.cut(cyl((dx, 0, -1), "z", P.M3, t + 2))
    return s


# ---------------------------------------------------------------- shell

def _shell_full() -> cq.Shape:
    s = rrect_shell(0, 0, P.SHELL_BOTTOM, P.BASE_TOP, SHELL_LX, SHELL_LY, P.BASE_R, P.BASE_WALL,
                    chamfer_top=TOP_CHAMFER, open_bot=True)
    adds = []
    # top-seam bosses hang under the skin
    z_skin = P.BASE_TOP - P.BASE_WALL
    for _, a, b in _top_seam_pairs():
        for q in (a, b):
            adds.append(cyl((q[0], q[1], z_skin - 9), "z", 10, 9.5))
    # wall-seam bosses point inward
    for _, a, b, n in _wall_seam_pairs():
        c = [(a[i] + b[i]) / 2 for i in range(3)]
        for q in (a, b):
            # boss runs from the wall to the shared tab plane, so a curved wall still meets one flat tab
            depth = 9.0 + sum((c[i] - q[i]) * n[i] for i in range(3))
            adds.append(cyl((q[0] - n[0] * 1, q[1] - n[1] * 1, q[2]), n, 10, depth + 1))
    # lugs onto the pan
    for x, y in LUG_PTS:
        r = math.hypot(x, y)
        ux, uy = x / r, y / r
        lug = fuse(cyl((x, y, P.PAN_TOP), "z", 14, 8), cbox(x + ux * 14, y + uy * 14, P.PAN_TOP + 4, 28, 28, 8))
        adds.append(lug)
    # stiffening rim inside the chamfer line
    s = fuse(s, *adds)
    s = s.intersect(rrect(0, 0, P.SHELL_BOTTOM, P.BASE_TOP, SHELL_LX, SHELL_LY, P.BASE_R, chamfer_top=TOP_CHAMFER))

    tools = []
    for _, a, b in _top_seam_pairs():
        for q in (a, b):
            tools.append(cyl((q[0], q[1], z_skin - 9.5), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 0.5))
    for _, a, b, n in _wall_seam_pairs():
        c = [(a[i] + b[i]) / 2 for i in range(3)]
        for q in (a, b):
            depth = 9.0 + sum((c[i] - q[i]) * n[i] for i in range(3))
            p = (q[0] + n[0] * (depth + 0.5), q[1] + n[1] * (depth + 0.5), q[2])
            tools.append(cyl(p, (-n[0], -n[1], -n[2]), P.M3_INSERT, P.M3_INSERT_DEPTH))
    for x, y in LUG_PTS:
        tools.append(cyl((x, y, P.PAN_TOP - 1), "z", P.M3, 12))
        tools.append(cyl((x, y, P.PAN_TOP + 4), "z", P.M3_HEAD, 10))
    # wheel arches
    for sy in (1, -1):
        tools.append(cyl_between("y", (0, P.AXLE_Z), sy * 140, sy * 240, 2 * P.WHEEL_ARCH_R))
    # mast opening
    mx0, mx1, my = MAST_HOLE
    tools.append(rrect((mx0 + mx1) / 2, 0, P.BASE_TOP - 30, P.BASE_TOP + 5, mx1 - mx0, 2 * my, P.MAST_R + 4))
    # lidar window: a 200 degree band, with four thin pillars so the lower band stays attached
    tools.append(lidar_window())
    # light line: a groove around the shell for an LED strip under a diffuser
    tools.append(rrect_shell(0, 0, LIGHT_Z[0], LIGHT_Z[1], SHELL_LX + 2, SHELL_LY + 2, P.BASE_R + 1, 2.5, open_top=True, open_bot=True))
    # e-stop, charge port, main switch, vents
    tools.append(cyl((ESTOP_XY[0], ESTOP_XY[1], P.BASE_TOP - 10), "z", P.ESTOP_HOLE, 20))
    tools.append(cyl((-SHELL_LX / 2 - 5, -40, 100), "x", 12.2, 20))
    tools.append(cyl((-SHELL_LX / 2 - 5, 40, 100), "x", 20.2, 20))
    for i in range(7):
        y = -36 + 12 * i
        tools.append(rrect(-SHELL_LX / 2, y, 150, 188, 20, 5, 2.4))
    return cut(s, *tools)


LIDAR_HALF_ANGLE = 100.0
LIDAR_PILLARS = (-72.0, -38.0, 38.0, 72.0)


def lidar_window() -> cq.Shape:
    lx = P.LIDAR_X
    z0, h = P.LIDAR_SCAN_Z - 13, 26.0
    a = math.radians(LIDAR_HALF_ANGLE)
    wedge = (
        cq.Workplane("XY").workplane(offset=z0)
        .moveTo(lx, 0)
        .lineTo(lx + 500 * math.cos(a), 500 * math.sin(a))
        .lineTo(lx + 500, 500).lineTo(lx + 500, -500)
        .lineTo(lx + 500 * math.cos(a), -500 * math.sin(a))
        .close().extrude(h).val()
    )
    win = wedge.intersect(cyl((lx, 0, z0), "z", 320, h))
    for deg in LIDAR_PILLARS:
        bar = box(0, 200, -3, 3, z0 - 1, z0 + h + 1).rotate((0, 0, 0), (0, 0, 1), deg).translate((lx, 0, 0))
        win = win.cut(bar)
    return win


def split_one(full, region, name) -> cq.Shape:
    """Intersect and insist on one solid; a dropped island is a design error."""
    piece = full.intersect(region)
    solids = sorted(piece.Solids(), key=lambda s: -s.Volume())
    if not solids:
        raise ValueError(f"{name}: empty")
    if len(solids) > 1 and solids[1].Volume() > 30:
        raise ValueError(f"{name}: splits into {len(solids)} islands, second is {solids[1].Volume():.0f} mm^3")
    return solids[0]


def _cells():
    xs = [-SHELL_LX / 2 - 10, *P.GRID_X, SHELL_LX / 2 + 10]
    ys = [-SHELL_LY / 2 - 10, *P.GRID_Y, SHELL_LY / 2 + 10]
    out = []
    names_x = ["rear", "mid", "front"]
    names_y = ["r", "c", "l"]
    for i in range(3):
        for j in range(3):
            out.append((f"{names_x[i]}_{names_y[j]}", xs[i], xs[i + 1], ys[j], ys[j + 1]))
    return out


def shell_parts() -> list[Part]:
    full = _shell_full()
    parts = []
    for name, x0, x1, y0, y1 in _cells():
        tile = split_one(full, box(x0, x1, y0, y1, 0, 400), f"base_shell_{name}")
        parts.append(Part(f"base_shell_{name}", tile, "base", "base", color="shell", rot=(180, 0, 0), walls=3, infill=15,
                          note="Print top-down. Heat-set inserts in the seam bosses."))
        hw("M3 heat-set insert", 0)
    n_top = sum(2 for _ in _top_seam_pairs())
    n_wall = sum(2 for _ in _wall_seam_pairs())
    hw("M3 heat-set insert", n_top + n_wall)
    hw("M3x10 socket head", n_top + n_wall + len(LUG_PTS))
    return parts


def joiner_count():
    return len(_top_seam_pairs()) + len(_wall_seam_pairs()) + len(_pan_seam_pairs())


def joiner_placed() -> list[cq.Shape]:
    """Joiner tabs in place, for the viewer and clearance checks."""
    out = []
    z_skin = P.BASE_TOP - P.BASE_WALL
    for _, a, b in _top_seam_pairs():
        out.append(tab_at((a[0], a[1], z_skin), (b[0], b[1], z_skin), (0, 0, -1)))
    for _, a, b, n in _wall_seam_pairs():
        out.append(tab_at(a, b, n))
    for _, a, b in _pan_seam_pairs():
        out.append(tab_at((a[0], a[1], P.PAN_TOP), (b[0], b[1], P.PAN_TOP), (0, 0, 1), standoff=0.0))
    return out


# ---------------------------------------------------------------- pan

def _pan_seam_pairs():
    pairs = []
    taken = _all_pan_pts()
    for gx in P.GRID_X:
        for y in (-190.0, -135.0, -60.0, 0.0, 60.0, 135.0, 190.0):
            a, b = (gx - JOIN_OFF, y), (gx + JOIN_OFF, y)
            ok = all(_pan_inside(q, 12) for q in (a, b)) and all(_clear(q, taken, 16) for q in (a, b))
            ok = ok and all(abs(y - gy) > 18 for gy in P.GRID_Y)
            ok = ok and not any(_in_cut(q, 8) for q in (a, b))
            mx0, mx1, my = MAST_HOLE
            ok = ok and not any(mx0 - 16 < q[0] < mx1 + 16 and abs(q[1]) < my + 16 for q in (a, b))
            if ok:
                pairs.append(("x", a, b))
    for gy in P.GRID_Y:
        for x in (-232.0, -170.0, -130.0, -40.0, 30.0, 120.0, 160.0, 225.0):
            a, b = (x, gy - JOIN_OFF), (x, gy + JOIN_OFF)
            ok = all(_pan_inside(q, 12) for q in (a, b)) and all(_clear(q, taken, 16) for q in (a, b))
            ok = ok and all(abs(x - gx) > 18 for gx in P.GRID_X)
            ok = ok and not any(_in_cut(q, 8) for q in (a, b))
            mx0, mx1, my = MAST_HOLE
            ok = ok and not any(mx0 - 16 < q[0] < mx1 + 16 and abs(q[1]) < my + 16 for q in (a, b))
            # keep tabs out from under the battery cradle walls
            bx, by = P.BATT[0] / 2 + 10, P.BATT[1] / 2 + 10
            ok = ok and not (abs(x - BATT_C[0]) < bx + 16 and abs(abs(gy) - by) < 22)
            if ok:
                pairs.append(("y", a, b))
    return pairs


def _pan_inside(q, margin):
    x, y = q
    return abs(x) <= rr_boundary("y", y, PAN_LX, PAN_LY, PAN_R) - margin and abs(y) <= PAN_LY / 2 - margin


def _in_cut(q, margin):
    x, y = q
    if abs(x) < P.WHEEL_CUT_X + margin and abs(y) > P.WHEEL_CUT_Y - margin:
        return True
    for cx in (P.CASTER_X, -P.CASTER_X):
        if math.hypot(x - cx, y) < P.CASTER_HOLE / 2 + margin:
            return True
    return False


def _pan_full() -> cq.Shape:
    z0, z1 = P.PAN_BOTTOM, P.PAN_TOP
    skin = rrect(0, 0, z1 - P.PAN_SKIN, z1, PAN_LX, PAN_LY, PAN_R)
    rim = rrect_shell(0, 0, z0, z1, PAN_LX, PAN_LY, PAN_R, 4.0, open_top=True, open_bot=True)
    ribs = []
    for x in range(-240, 241, 60):
        ribs.append(box(x - 1.5, x + 1.5, -PAN_LY / 2, PAN_LY / 2, z0, z1 - 1))
    for y in range(-180, 181, 60):
        ribs.append(box(-PAN_LX / 2, PAN_LX / 2, y - 1.5, y + 1.5, z0, z1 - 1))
    # ribs either side of every cut line, so each tile edge is stiff
    for gx in P.GRID_X:
        for d in (-2.5, 2.5):
            ribs.append(box(gx + d - 1.5, gx + d + 1.5, -PAN_LY / 2, PAN_LY / 2, z0, z1 - 1))
    for gy in P.GRID_Y:
        for d in (-2.5, 2.5):
            ribs.append(box(-PAN_LX / 2, PAN_LX / 2, gy + d - 1.5, gy + d + 1.5, z0, z1 - 1))
    grid = fuse(*ribs).intersect(rrect(0, 0, z0, z1, PAN_LX - 2, PAN_LY - 2, PAN_R - 1))
    bosses = []
    pts = _all_pan_pts() + [q for _, a, b in _pan_seam_pairs() for q in (a, b)]
    for x, y in pts:
        bosses.append(cyl((x, y, z0 + 3), "z", 11, z1 - z0 - 3))
    # rims around the cuts
    rims = []
    for sy in (1, -1):
        y0 = P.WHEEL_CUT_Y if sy > 0 else -PAN_LY
        y1 = PAN_LY if sy > 0 else -P.WHEEL_CUT_Y
        rims.append(box(-P.WHEEL_CUT_X - 4, P.WHEEL_CUT_X + 4, y0 - 4 * sy if sy > 0 else y0, y1 if sy > 0 else y1 + 4, z0, z1))
    for cx in (P.CASTER_X, -P.CASTER_X):
        rims.append(tube_between("z", (cx, 0), z0, z1, P.CASTER_HOLE + 8, P.CASTER_HOLE - 1))
    pan = fuse(skin, rim, grid, *bosses, *rims).intersect(rrect(0, 0, z0, z1, PAN_LX, PAN_LY, PAN_R))
    tools = []
    for sy in (1, -1):
        tools.append(box(-P.WHEEL_CUT_X, P.WHEEL_CUT_X, sy * P.WHEEL_CUT_Y, sy * 400, 0, 100))
    for cx in (P.CASTER_X, -P.CASTER_X):
        tools.append(cyl((cx, 0, 0), "z", P.CASTER_HOLE, 100))
    for x, y in pts:
        tools.append(cyl((x, y, z1 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
        tools.append(cyl((x, y, z0 - 1), "z", 2.5, 20))  # vent the insert hole
    # cable pass under the mast and drain holes
    tools.append(cyl((P.MAST_X + 20, 0, 0), "z", 30, 100))
    hw("M3 heat-set insert", len(pts))
    hw("M3x10 socket head", 2 * len(_pan_seam_pairs()))
    return cut(pan, *tools)


def pan_parts() -> list[Part]:
    full = _pan_full()
    out = []
    for name, x0, x1, y0, y1 in _cells():
        tile = split_one(full, box(x0, x1, y0, y1, 0, 100), f"base_pan_{name}")
        out.append(Part(f"base_pan_{name}", tile, "base", "base", color="frame", rot=(180, 0, 0),
                        note="Structure. Skin down on the bed, ribs up. 4 walls."))
    return out


# ---------------------------------------------------------------- hub clamps

AXLE_BLOCK = (-32.0, 32.0, 112.0, 157.0)


def _axle_bore(y0, y1):
    bore = cyl_between("y", (0, P.AXLE_Z), y0, y1, P.AXLE_D + 0.3)
    flats = box(-20, 20, y0, y1, P.AXLE_Z - P.AXLE_FLATS / 2 - 0.15, P.AXLE_Z + P.AXLE_FLATS / 2 + 0.15)
    return bore.intersect(flats)


def axle_block(side) -> tuple[cq.Shape, cq.Shape]:
    x0, x1, y0, y1 = AXLE_BLOCK
    zc = P.AXLE_Z
    lower = rrect(0, (y0 + y1) / 2, P.PAN_TOP, zc, x1 - x0, y1 - y0, 6)
    upper = rrect(0, (y0 + y1) / 2, zc, zc + 26, x1 - x0, y1 - y0, 6, chamfer_top=4)
    tools_l, tools_u = [], []
    for x, y in _axle_pts(1):
        tools_l.append(cyl((x, y, P.PAN_TOP - 1), "z", P.M3, 60))
        tools_l.append(cyl((x, y, P.PAN_TOP + 8), "z", P.M3_HEAD, 60))
        tools_u.append(cyl((x, y, zc - 1), "z", 8.0, 60))  # screwdriver access
    for x in (-24.0, 24.0):
        y = 134.0
        tools_l.append(cyl((x, y, zc - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, 10))
        tools_u.append(cyl((x, y, zc - 1), "z", P.M3, 40))
        tools_u.append(cyl((x, y, zc + 10), "z", P.M3_HEAD, 40))
    b = _axle_bore(y0 - 1, y1 + 1)
    lower = cut(lower, b, *tools_l)
    upper = cut(upper, b, *tools_u)
    hw("M3 heat-set insert", 2)
    hw("M3x16 socket head", 2)
    hw("M3x10 socket head", 4)
    if side < 0:
        lower = lower.mirror("XZ", (0, 0, 0))
        upper = upper.mirror("XZ", (0, 0, 0))
    return lower, upper


# ---------------------------------------------------------------- casters

def caster_bridge(cx, lidar=False) -> cq.Shape:
    z0, z1 = P.PAN_TOP, P.CASTER_PLATE_Z
    legs = [cyl((x, y, z0), "z", 16, z1 - z0) for x, y in _caster_pts(cx)]
    plate = rrect(cx, 0, z1, z1 + 10, 72, 152, 14)
    parts = [plate, *legs]
    s = fuse(*parts)
    tools = [cyl((cx, 0, z1 - 1), "z", 22.2, 7 + 1), cyl((cx, 0, z1 - 1), "z", P.M8, 20),
             cyl((cx, 0, z1 + 6), "z", 18, 20)]
    for x, y in _caster_pts(cx):
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 40))
        tools.append(cyl((x, y, z0 + 8), "z", P.M3_HEAD, 40))
    if lidar:
        for x, y in _lidar_mount_pts(cx):
            tools.append(cyl((x, y, z1 + 10 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
        hw("M3 heat-set insert", 3)
    hw("M3x10 socket head", 4)
    hw("608ZZ bearing", 1)
    hw("M8x40 bolt + nyloc + 2 washers (caster swivel)", 1)
    return cut(s, *tools)


def _lidar_mount_pts(cx):
    return [(cx + 31 * math.cos(a), 31 * math.sin(a)) for a in (math.pi / 6, 5 * math.pi / 6, 3 * math.pi / 2)]


def lidar_mount(cx) -> cq.Shape:
    """Ring that lifts the RPLIDAR C1 to the scan slot. Bolts to the front caster bridge."""
    z0 = P.CASTER_PLATE_Z + 10
    ring = tube_between("z", (cx, 0), z0, P.LIDAR_Z0, 52, 40)
    flange = cyl((cx, 0, z0), "z", 74, 4)
    top = tube_between("z", (cx, 0), P.LIDAR_Z0 - 3, P.LIDAR_Z0, 58, 30)
    s = fuse(ring, flange, top)
    tools = [cyl((cx, 0, z0 - 1), "z", 40, 10)]
    for x, y in _lidar_mount_pts(cx):
        tools.append(cyl((x, y, z0 - 1), "z", P.M3, 10))
    for dx, dy in ((-17, -17), (17, -17), (-17, 17), (17, 17)):  # RPLIDAR C1 base holes, VERIFY
        tools.append(cyl((cx + dx, dy, P.LIDAR_Z0 - 8), "z", 2.6, 10))
    hw("M2.5x6 screw (lidar)", 4)
    hw("M3x10 socket head", 3)
    return cut(s, *tools)


def caster_fork(cx) -> cq.Shape:
    ax = cx - P.CASTER_TRAIL
    r = P.CASTER_WHEEL / 2
    top0, top1 = 53.0, 64.0
    disc = cyl((cx, 0, top0), "z", 46, top1 - top0)
    arms = []
    half = P.CASTER_WHEEL_W / 2 + 1.5
    for sy in (1, -1):
        y0 = sy * half
        y1 = sy * (half + 5)
        arm = box(ax - 11, cx + 11, y0, y1, r - 2, top1).intersect(
            fuse(cyl_between("y", (ax, r), y0, y1, 22), box(ax - 11, cx + 14, y0, y1, r, top1)))
        arms.append(arm)
    s = fuse(disc, *arms)
    s = cut(s, cyl((cx, 0, top0 - 1), "z", P.M8, 20), cyl_between("y", (ax, r), -40, 40, P.M8),
            hexagon(cx, 0, top0 - 1, top0 + 6.5, 13.2))
    hw("M8x40 bolt + nyloc (caster axle)", 1)
    return s


def caster_wheel(cx) -> cq.Shape:
    ax = cx - P.CASTER_TRAIL
    r = P.CASTER_WHEEL / 2
    w = P.CASTER_WHEEL_W
    s = cyl_between("y", (ax, r), -w / 2, w / 2, P.CASTER_WHEEL)
    s = s.edges().chamfer(2.0) if False else s
    tools = [cyl_between("y", (ax, r), -w / 2 - 1, -w / 2 + 7, 22.15),
             cyl_between("y", (ax, r), w / 2 - 7, w / 2 + 1, 22.15),
             cyl_between("y", (ax, r), -w, w, 12.0)]
    hw("608ZZ bearing", 2)
    return cut(s, *tools)


# ---------------------------------------------------------------- battery and shelves

def battery_cradle() -> cq.Shape:
    bx, by, bz = P.BATT
    cx, cy = BATT_C
    frame = rrect_shell(cx, cy, P.PAN_TOP, P.PAN_TOP + 40, bx + 10, by + 10, 6, 4.0, open_top=True, open_bot=True)
    feet = []
    for x, y in CRADLE_PTS:
        feet.append(fuse(cyl((x, y, P.PAN_TOP), "z", 14, 6), box(x - 7, x + 7, y, y - 10 * (1 if y > 0 else -1), P.PAN_TOP, P.PAN_TOP + 6)))
    s = fuse(frame, *feet)
    tools = [cyl((x, y, P.PAN_TOP - 1), "z", P.M3, 20) for x, y in CRADLE_PTS]
    # strap slots
    for y in (-60, 60):
        tools.append(box(cx - bx / 2 - 10, cx + bx / 2 + 10, y - 13, y + 13, P.PAN_TOP + 26, P.PAN_TOP + 30))
    hw("M3x10 socket head", 4)
    hw("Velcro battery strap 25 mm", 2)
    return cut(s, *tools)


def _shelf(pts, outline_box, side, front) -> cq.Shape:
    x0, x1, y0, y1 = outline_box
    if side < 0:
        y0, y1 = -y1, -y0
    plate = rrect((x0 + x1) / 2, (y0 + y1) / 2, SHELF_Z, SHELF_Z + SHELF_T, x1 - x0, y1 - y0, 8)
    plate = plate.intersect(rrect(0, 0, 0, 300, INNER_LX - 14, INNER_LY - 14, P.BASE_R - 14))
    legs = []
    for x, y in pts:
        legs.append(cyl((x, y, P.PAN_TOP), "z", 11, SHELF_Z - P.PAN_TOP + 1))
    s = fuse(plate, *legs)
    tools = []
    for x, y in pts:
        tools.append(cyl((x, y, P.PAN_TOP - 1), "z", P.M3, 300))
        tools.append(cyl((x, y, P.PAN_TOP + 7), "z", 6.6, 300))
    # universal mounting grid: M3 holes on 20 mm, zip slots between
    for gx in range(int(x0) + 16, int(x1) - 10, 20):
        for gy in range(int(y0) + 16, int(y1) - 10, 20):
            if all(math.hypot(gx - x, gy - y) > 12 for x, y in pts):
                tools.append(cyl((gx, gy, SHELF_Z - 1), "z", 2.9, 10))
    hw("M3x12 socket head", len(pts))
    return cut(s, *tools)


def front_shelf(side) -> cq.Shape:
    pts = FRONT_SHELF_PTS if side > 0 else [(x, -y) for x, y in FRONT_SHELF_PTS]
    return _shelf(pts, (32, 160, 4, 122), side, True)


def rear_shelf(side) -> cq.Shape:
    pts = REAR_SHELF_PTS if side > 0 else [(x, -y) for x, y in REAR_SHELF_PTS]
    return _shelf(pts, (-262, -98, 20, 142), side, False)


# ---------------------------------------------------------------- bought envelopes

def bought() -> list[Bought]:
    import vendor as V

    out = []
    for sy, name in ((1, "hub_l"), (-1, "hub_r")):
        pcs = V.place(V.hub_motor(sy), (0, sy * P.WHEEL_Y, P.AXLE_Z), xdir=(1, 0, 0), zdir=(0, sy, 0))
        out += V.boughts(name, pcs, f"wheel_{'l' if sy > 0 else 'r'}", "base", "wheel", P.HUB_MASS, "hub")
    out += V.boughts("battery", V.place(V.battery(), (BATT_C[0], BATT_C[1], BATT_Z0)), "base", "base", "battery", P.BATT_MASS, "battery")
    out += V.boughts("lidar", V.place(V.rplidar_c1(), (P.LIDAR_X, 0, P.LIDAR_Z0)), "base", "base", "electronics", 110, "lidar")
    z = SHELF_Z + SHELF_T
    boards = [
        ("zsx11h_l", (70, 60), V.zsx11h(), 60, "zsx"),
        ("zsx11h_r", (70, -60), V.zsx11h(), 60, "zsx"),
        ("esp32", (130, 60), V.esp32_devkit(), 10, "esp32"),
        ("imu", (130, -40), V.small_board(25, 20, (5, 5, 1)), 5, "imu"),
        ("tmc2209", (132, -92), V.small_board(15, 20, (5, 5, 1), look="pcb_black"), 5, "tmc"),
        ("buck_12v", (-175, 88), V.finned_buck(110, 62, 33), 260, "buck12"),
        ("buck_5v", (-125, -100), V.open_buck(60, 40, 22), 70, "buck5"),
        ("fuse_block", (-118, 38), V.fuse_block(40, 30, 25), 40, "fuse"),
        ("contactor_relay", (-212, 38), V.contactor(40, 30, 30), 60, "relay"),
    ]
    for name, (x, y), pcs, m, key in boards:
        zz = z + (8.5 if name == "esp32" else 0.0)  # the devkit stands on its pin headers
        out += V.boughts(name, V.place(pcs, (x, y, zz)), "base", "base", "electronics", m, key)
    out += V.boughts("estop", V.place(V.estop(), (ESTOP_XY[0], ESTOP_XY[1], P.BASE_TOP)), "base", "base", "electronics", 80, "estop")
    glow = rrect_shell(0, 0, LIGHT_Z[0] + 0.5, LIGHT_Z[1] - 0.5, SHELL_LX - 0.6, SHELL_LY - 0.6, P.BASE_R - 0.3, 1.2, open_top=True, open_bot=True)
    out.append(Bought("light_base", glow, "base", "base", "electronics", 15, "ledstrip", look="glow"))
    for cx in (P.CASTER_X, -P.CASTER_X):
        out.append(Bought(f"caster_bolt_{'f' if cx > 0 else 'r'}", cyl((cx, 0, P.CASTER_PLATE_Z - 12), "z", 8, 30), "base", "base", "metal", 30, "m8",
                          look="steel"))
    return out


def parts() -> list[Part]:
    out = []
    out += shell_parts()
    out += pan_parts()
    for side, s in ((1, "l"), (-1, "r")):
        lo, up = axle_block(side)
        out.append(Part(f"axle_block_{s}", lo, "base", "base", color="frame", note="Clamps the hub axle on its flats. MEASURE the axle first."))
        out.append(Part(f"axle_cap_{s}", up, "base", "base", color="frame", rot=(180, 0, 0)))
    out.append(Part("caster_bridge_front", caster_bridge(P.CASTER_X, lidar=True), "base", "base", color="frame", rot=(180, 0, 0),
                    note="Swivel 608ZZ pocket underneath. Inserts on top for the lidar mount."))
    out.append(Part("caster_bridge_rear", caster_bridge(-P.CASTER_X), "base", "base", color="frame", rot=(180, 0, 0)))
    out.append(Part("lidar_mount", lidar_mount(P.CASTER_X), "base", "base", color="dark", rot=(0, 0, 0),
                    note="Lifts the RPLIDAR C1 to the slot in the shell."))
    for cx, s in ((P.CASTER_X, "front"), (-P.CASTER_X, "rear")):
        out.append(Part(f"caster_fork_{s}", caster_fork(cx), "base", "base", color="dark", rot=(180, 0, 0)))
        out.append(Part(f"caster_wheel_{s}", caster_wheel(cx), "base", "base", color="dark", rot=(90, 0, 0),
                        note="Two 608ZZ pressed in. TPU 95A if your printer does it, PETG otherwise."))
    cradle = battery_cradle()
    for sy, s in ((1, "l"), (-1, "r")):
        half = split_one(cradle, box(-400, 400, 0, sy * 400, 0, 400), f"battery_cradle_{s}")
        out.append(Part(f"battery_cradle_{s}", half, "base", "base", color="frame",
                        note="Two halves meet under the pack; the strap holds them together."))
    for side, s in ((1, "l"), (-1, "r")):
        out.append(Part(f"shelf_front_{s}", front_shelf(side), "base", "base", color="frame", rot=(180, 0, 0),
                        note="Motor drivers and the ESP32 on the 20 mm grid."))
        out.append(Part(f"shelf_rear_{s}", rear_shelf(side), "base", "base", color="frame", rot=(180, 0, 0),
                        note="Bucks, fuse block, contactor."))
    return out
