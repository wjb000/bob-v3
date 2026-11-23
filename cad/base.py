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
BX = P.BASE_CX  # the shell and pan are centred here, not on the axle
CASTERS = (P.CASTER_XF, -P.CASTER_XR)
TOP_CHAMFER = 24.0

MAST_HOLE = (P.COL_X - P.COL_OUTER_D / 2 - 4, P.COL_X + P.COL_OUTER_D / 2 + 4, P.COL_OUTER_D / 2 + 4)
MAST_FLANGE = 12.0  # column foot overhang on the pan
ESTOP_XY = (-122.0, 112.0)  # rear-left of the top, behind the battery, clear of the rear caster plate
LIGHT_Z = (172.0, 178.0)

# Pack turned so its 200 mm side runs fore-aft and it sits on +y, off the caster centreline.
# The cradle floor (BATT_Z0 - 8) rides 3 mm over the top of the left tire, so the
# wheels can tuck in under the pack. Clear of the column (y ≤ 50).
BATT_C = (0.0, 100.0)
BATT_LX, BATT_LY = P.BATT[1], P.BATT[0]  # 200 along x, 80 along y
BATT_Z0 = 112.0
SHELF_Z = 142.0
SHELF_T = 4.0

# Every M3 insert in the pan, named, so parts and seams can avoid each other.
PAN_PTS: dict[str, list[tuple[float, float]]] = {}


def _col_foot_pts():
    """Eight M3 on the column flange, outside the outer tube, on the flats."""
    d = P.COL_OUTER_D / 2 + 6.0
    o = 22.0
    return [(P.COL_X - d, -o), (P.COL_X - d, o), (P.COL_X + d, -o), (P.COL_X + d, o),
            (P.COL_X - o, -d), (P.COL_X + o, -d), (P.COL_X - o, d), (P.COL_X + o, d)]


def _axle_pts(side):
    """Four M3 in the pan, on the inboard face of the wheel bracket."""
    yf = P.WHEEL_Y - P.DDSM_STUB_END
    y = side
    return [(-20, y * (yf - 22)), (20, y * (yf - 22)), (-20, y * (yf - 8)), (20, y * (yf - 8))]


def _caster_pts(cx):
    # The two mounting holes of a CY-15A ball transfer, its long side across the robot.
    h = P.BALL_XFER_PITCH / 2
    return [(cx, -h), (cx, h)]


# Shelves stay on the open side (−y) and one rear pocket. +y is the battery.
# Clear of the wheel brackets (x ±26, y −135..−105 on this side).
FRONT_SHELF_PTS = [(55, -112), (90, -112), (72, -140)]
REAR_SHELF_PTS = [(-55, -112), (-90, -112), (-72, -140)]
FRONT_SHELF_R_PTS = [(120, -118), (140, -116), (126, -132)]
REAR_SHELF_R_PTS = [(-128, 92), (-138, 112), (-124, 128)]
# On the cradle side walls (x ≈ ±105). The old feet sat in the opening and the half fell apart.
CRADLE_PTS = [(107, 88), (107, 128), (-107, 88), (-107, 128)]
LUG_PTS = []


def _lug_points():
    """Lugs on the flats of the rounded-square shell, clear of the wheel cuts and the caster holes."""
    hx, hy = PAN_LX / 2 - 18, PAN_LY / 2 - 18
    pts = []
    for x in (BX - 150.0, -60.0, 60.0, BX + 140.0):
        for sy in (1, -1):
            y = sy * hy
            if abs(y) > P.WHEEL_CUT_Y - 16 and abs(x) < P.WHEEL_CUT_X + 28:
                continue
            pts.append((x, y))
    for y in (-80.0, 80.0):
        for sx, cx in zip((1, -1), CASTERS):
            x = BX + sx * hx
            if math.hypot(x - cx, y) < P.CASTER_HOLE / 2 + 24:
                continue
            pts.append((x, y))
    return pts


def _lidar_mount_pts(cx):
    return [(cx + 31 * math.cos(a), 31 * math.sin(a)) for a in (math.pi / 6, 5 * math.pi / 6, 3 * math.pi / 2)]


def _register():
    PAN_PTS.clear()
    PAN_PTS["col"] = _col_foot_pts()
    PAN_PTS["axle_l"] = _axle_pts(1)
    PAN_PTS["axle_r"] = _axle_pts(-1)
    PAN_PTS["lidar"] = _lidar_mount_pts(P.LIDAR_X)
    PAN_PTS["shelf_fl"] = FRONT_SHELF_PTS
    PAN_PTS["shelf_fr"] = FRONT_SHELF_R_PTS
    PAN_PTS["shelf_rl"] = REAR_SHELF_PTS
    PAN_PTS["cradle"] = CRADLE_PTS
    PAN_PTS["cable"] = [(-78.0, 24.0), (-78.0, 42.0)]
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


def _on_top(q):
    """True when a point sits on the top skin, inside the chamfer of the rounded square."""
    lim = rr_boundary("y", q[1], SHELL_LX, SHELL_LY, P.BASE_R) - TOP_CHAMFER - 14
    return abs(q[0] - BX) <= lim and abs(q[1]) <= SHELL_LY / 2 - TOP_CHAMFER - 14


def _top_seam_pairs():
    """Shell top seams: pairs of insert points straddling each cut line."""
    pairs = []
    mx0, mx1, my = MAST_HOLE
    for gx in P.GRID_X:
        for y in range(-180, 181, 46):
            a, b = (gx - JOIN_OFF, y), (gx + JOIN_OFF, y)
            if not (_on_top(a) and _on_top(b)):
                continue
            if any(mx0 - 8 < q[0] < mx1 + 8 and abs(q[1]) < my + 8 for q in (a, b)):
                continue
            if any(abs(y - gy) < 16 for gy in P.GRID_Y):
                continue
            if _near_port(a) or _near_port(b):
                continue
            pairs.append(("x", a, b))
    for gy in P.GRID_Y:
        for x in range(-224, 291, 46):
            if any(abs(x - gx) < 16 for gx in P.GRID_X):
                continue
            a, b = (x, gy - JOIN_OFF), (x, gy + JOIN_OFF)
            if not (_on_top(a) and _on_top(b)):
                continue
            if _near_port(a) or _near_port(b):
                continue
            pairs.append(("y", a, b))
    return pairs


def _near_port(q, tol=26.0):
    """Keep joiner tabs out of the charge socket and the e-stop body."""
    return (math.hypot(q[0] - P.CHARGE_XY[0], q[1] - P.CHARGE_XY[1]) < tol
            or math.hypot(q[0] - ESTOP_XY[0], q[1] - ESTOP_XY[1]) < tol)


def _wall_normal(x, y):
    """Inward normal of the rounded-square inner wall at a point on it."""
    hx, hy = INNER_LX / 2, INNER_LY / 2
    r = max(P.BASE_R - P.BASE_WALL, 1.0)
    x = x - BX
    ax, ay = abs(x), abs(y)
    if ay >= hy - r - 1 and ax <= hx - r + 1:
        return (0.0, -1.0 if y > 0 else 1.0, 0.0)
    if ax >= hx - r - 1 and ay <= hy - r + 1:
        return (-1.0 if x > 0 else 1.0, 0.0, 0.0)
    cx, cy = math.copysign(hx - r, x), math.copysign(hy - r, y)
    dx, dy = x - cx, y - cy
    n = math.hypot(dx, dy) or 1.0
    return (-dx / n, -dy / n, 0.0)


def _arch_top(x):
    if abs(x) >= P.WHEEL_ARCH_R:
        return 0.0
    return P.AXLE_Z + math.sqrt(P.WHEEL_ARCH_R ** 2 - x * x)


def _wall_seam_pairs():
    """(kind, p_a, p_b, inward normal) on the inner wall face at each seam. The normal is radial."""
    out = []
    zs = (75.0, 120.0)
    rin = P.BASE_R - P.BASE_WALL

    def wall_y(x):
        return rr_boundary("x", x - BX, INNER_LX, INNER_LY, rin)

    def wall_x(y):
        return rr_boundary("y", y, INNER_LX, INNER_LY, rin)

    def pair(a, b, kind):
        c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        return (kind, a, b, _wall_normal(*c))

    for gx in P.GRID_X:
        for sy in (1, -1):
            for z in zs:
                xa, xb = gx - JOIN_OFF, gx + JOIN_OFF
                if z < max(_arch_top(xa), _arch_top(xb)) + 14:
                    continue
                out.append(pair((xa, sy * wall_y(xa), z), (xb, sy * wall_y(xb), z), "side"))
    for gy in P.GRID_Y:
        for sx in (1, -1):
            for z in zs:
                if sx > 0 and 112 < z < 160:
                    continue  # lidar slot
                ya, yb = gy - JOIN_OFF, gy + JOIN_OFF
                out.append(pair((BX + sx * wall_x(ya), ya, z), (BX + sx * wall_x(yb), yb, z), "end"))
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
    s = rrect_shell(BX, 0, P.SHELL_BOTTOM, P.BASE_TOP, SHELL_LX, SHELL_LY, P.BASE_R, P.BASE_WALL,
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
        r = math.hypot(x - BX, y)
        ux, uy = (x - BX) / r, y / r
        lug = fuse(cyl((x, y, P.PAN_TOP), "z", 14, 8), cbox(x + ux * 14, y + uy * 14, P.PAN_TOP + 4, 28, 28, 8))
        adds.append(lug)
    # stiffening rim inside the chamfer line
    s = fuse(s, *adds)
    s = s.intersect(rrect(BX, 0, P.SHELL_BOTTOM, P.BASE_TOP, SHELL_LX, SHELL_LY, P.BASE_R, chamfer_top=TOP_CHAMFER))

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
    # wheel arches, opening the shell where the tire is
    for sy in (1, -1):
        tools.append(cyl_between("y", (0, P.AXLE_Z), sy * (P.WHEEL_Y - 28), sy * (P.BASE_W / 2 + 40), 2 * P.WHEEL_ARCH_R))
    # column opening
    mx0, mx1, my = MAST_HOLE
    tools.append(rrect((mx0 + mx1) / 2, 0, P.BASE_TOP - 30, P.BASE_TOP + 5, mx1 - mx0, 2 * my, P.COL_OUTER_R + 4))
    # lidar window: a 200 degree band, with four thin pillars so the lower band stays attached
    tools.append(lidar_window())
    # light line: a groove around the shell for an LED strip under a diffuser
    tools.append(rrect_shell(BX, 0, LIGHT_Z[0], LIGHT_Z[1], SHELL_LX + 2, SHELL_LY + 2, P.BASE_R + 1, 2.5, open_top=True, open_bot=True))
    # e-stop, charge port, main switch, vents
    tools.append(cyl((ESTOP_XY[0], ESTOP_XY[1], P.BASE_TOP - 10), "z", P.ESTOP_HOLE, 20))
    tools.append(cyl((P.CHARGE_XY[0], P.CHARGE_XY[1], P.BASE_TOP - 10), "z", P.CHARGE_HOLE, 20))  # charge socket, top
    tools.append(cyl((BX - SHELL_LX / 2 - 5, 40, 95), "x", 20.2, 20))
    for i in range(7):
        y = -36 + 12 * i
        tools.append(rrect(BX - SHELL_LX / 2, y, 125, 160, 20, 5, 2.4))
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
    xs = [BX - SHELL_LX / 2 - 10, *P.GRID_X, BX + SHELL_LX / 2 + 10]
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
    def spaced(vals, gap=42):
        out, last = [], None
        for v in vals:
            if last is None or v - last >= gap:
                out.append(v)
                last = v
        return out

    for gx in P.GRID_X:
        for y in range(-200, 201, 7):
            a, b = (gx - JOIN_OFF, y), (gx + JOIN_OFF, y)
            ok = all(_pan_inside(q, 12) for q in (a, b)) and all(_clear(q, taken, 18) for q in (a, b))
            ok = ok and all(abs(y - gy) > 18 for gy in P.GRID_Y)
            ok = ok and not any(_in_cut(q, 8) for q in (a, b)) and not any(_under_bracket(q) for q in (a, b))
            mx0, mx1, my = MAST_HOLE
            ok = ok and not any(mx0 - 28 < q[0] < mx1 + 28 and abs(q[1]) < my + 28 for q in (a, b))
            if ok:
                pairs.append(("x", a, b))
    keep = []
    for gx in P.GRID_X:
        ys = spaced([a[1] for k, a, b in pairs if k == "x" and a[0] == gx - JOIN_OFF])
        keep += [("x", (gx - JOIN_OFF, y), (gx + JOIN_OFF, y)) for y in ys]
    pairs = keep
    for gy in P.GRID_Y:
        for x in range(-230, 291, 7):
            a, b = (x, gy - JOIN_OFF), (x, gy + JOIN_OFF)
            ok = all(_pan_inside(q, 12) for q in (a, b)) and all(_clear(q, taken, 18) for q in (a, b))
            ok = ok and all(abs(x - gx) > 18 for gx in P.GRID_X)
            ok = ok and not any(_in_cut(q, 8) for q in (a, b)) and not any(_under_bracket(q) for q in (a, b))
            mx0, mx1, my = MAST_HOLE
            ok = ok and not any(mx0 - 28 < q[0] < mx1 + 28 and abs(q[1]) < my + 28 for q in (a, b))
            # keep tabs out from under the battery cradle walls
            ok = ok and not (abs(x - BATT_C[0]) < BATT_LX / 2 + 18 and abs(gy - BATT_C[1]) < BATT_LY / 2 + 18)
            if ok:
                pairs.append(("y", a, b))
    keep = [p_ for p_ in pairs if p_[0] == "x"]
    for gy in P.GRID_Y:
        xs = spaced([a[0] for k, a, b in pairs if k == "y" and a[1] == gy - JOIN_OFF])
        keep += [("y", (x, gy - JOIN_OFF), (x, gy + JOIN_OFF)) for x in xs]
    return keep


def _under_bracket(q, margin=12.0):
    """Inside a wheel bracket's footprint on the pan (x ±26, 30 mm inboard of the stub face)."""
    yf = P.WHEEL_Y - P.DDSM_STUB_END
    return abs(q[0]) < 26 + margin and yf - 30 - margin < abs(q[1]) < yf + margin


def _pan_inside(q, margin):
    x, y = q
    return abs(x - BX) <= rr_boundary("y", y, PAN_LX, PAN_LY, PAN_R) - margin and abs(y) <= PAN_LY / 2 - margin


def _in_cut(q, margin):
    x, y = q
    if abs(x) < P.WHEEL_CUT_X + margin and abs(y) > P.WHEEL_CUT_Y - margin:
        return True
    if P.CASTER_HOLE > 0:
        for cx in CASTERS:
            if math.hypot(x - cx, y) < P.CASTER_HOLE / 2 + margin:
                return True
    return False


def _pan_full() -> cq.Shape:
    z0, z1 = P.PAN_BOTTOM, P.PAN_TOP
    skin = rrect(BX, 0, z1 - P.PAN_SKIN, z1, PAN_LX, PAN_LY, PAN_R)
    rim = rrect_shell(BX, 0, z0, z1, PAN_LX, PAN_LY, PAN_R, 4.0, open_top=True, open_bot=True)
    ribs = []
    for x in range(-280, 281, 60):
        ribs.append(box(x - 1.5, x + 1.5, -PAN_LY / 2, PAN_LY / 2, z0, z1 - 1))
    for y in range(-220, 221, 60):
        ribs.append(box(BX - PAN_LX / 2, BX + PAN_LX / 2, y - 1.5, y + 1.5, z0, z1 - 1))
    # ribs either side of every cut line, so each tile edge is stiff
    for gx in P.GRID_X:
        for d in (-2.5, 2.5):
            ribs.append(box(gx + d - 1.5, gx + d + 1.5, -PAN_LY / 2, PAN_LY / 2, z0, z1 - 1))
    for gy in P.GRID_Y:
        for d in (-2.5, 2.5):
            ribs.append(box(BX - PAN_LX / 2, BX + PAN_LX / 2, gy + d - 1.5, gy + d + 1.5, z0, z1 - 1))
    grid = fuse(*ribs).intersect(rrect(BX, 0, z0, z1, PAN_LX - 2, PAN_LY - 2, PAN_R - 1))
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
    # solid pads the ball transfers bolt to
    for cx in CASTERS:
        rims.append(box(cx - P.BALL_XFER[0] / 2 - 2, cx + P.BALL_XFER[0] / 2 + 2,
                        -P.BALL_XFER[1] / 2 - 2, P.BALL_XFER[1] / 2 + 2, z0, z1))
    pan = fuse(skin, rim, grid, *bosses, *rims).intersect(rrect(BX, 0, z0, z1, PAN_LX, PAN_LY, PAN_R))
    # The pads stand 2 mm proud of the rib bottoms, so the 20 mm transfers just touch the floor.
    feet = [box(cx - P.BALL_XFER[0] / 2 - 2, cx + P.BALL_XFER[0] / 2 + 2,
                -P.BALL_XFER[1] / 2 - 2, P.BALL_XFER[1] / 2 + 2, P.BALL_XFER[2], z0 + 1) for cx in CASTERS]
    pan = fuse(pan, *feet)
    tools = []
    for sy in (1, -1):
        tools.append(box(-P.WHEEL_CUT_X, P.WHEEL_CUT_X, sy * P.WHEEL_CUT_Y, sy * 400, 0, 100))
    for x, y in _caster_pts(CASTERS[0]) + _caster_pts(CASTERS[1]):
        tools.append(cyl((x, y, 0), "z", P.M3, 100))  # screw up from below, nut on top of the pad
        tools.append(hexagon(x, y, z1 - 3.0, z1 + 1, 6.4))
    hw("M3x20 socket head (ball transfer)", 4)
    hw("M3 nut", 4)
    for x, y in pts:
        tools.append(cyl((x, y, z1 - P.M3_INSERT_DEPTH), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 1))
        tools.append(cyl((x, y, z0 - 1), "z", 2.5, 20))  # vent the insert hole
    # cable pass under the column and drain holes
    tools.append(cyl((P.COL_X + 20, 0, 0), "z", 30, 100))
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

def wheel_bracket(side) -> cq.Shape:
    """Holds a DDSM115 by its stub: 3 x M2.5 into the stub end on a 15.2 circle, 4 x M3 into the pan."""
    yf = P.WHEEL_Y - P.DDSM_STUB_END  # stub end face
    zc = P.AXLE_Z
    s = rrect(0, (yf - 30 + yf) / 2, P.PAN_TOP, zc + 24, 52, 30, 8, chamfer_top=4)
    tools = [cyl_between("y", (0, zc), yf - 40, yf + 1, 9.0)]  # motor cable through the middle
    for deg in (90, 210, 330):
        a = math.radians(deg)
        x, z = P.DDSM_PCD / 2 * math.cos(a), zc + P.DDSM_PCD / 2 * math.sin(a)
        tools.append(cyl_between("y", (x, z), yf - 31, yf + 1, 2.9))
        tools.append(cyl_between("y", (x, z), yf - 31, yf - 8, 5.2))
    for x, y in _axle_pts(1):
        tools.append(cyl((x, y, P.PAN_TOP - 1), "z", P.M3, 60))
        tools.append(cyl((x, y, P.PAN_TOP + 8), "z", P.M3_HEAD, 60))
    hw("M2.5x10 socket head (DDSM115 stub)", 3)
    hw("M3x10 socket head", 4)
    s = cut(s, *tools)
    return s if side > 0 else s.mirror("XZ", (0, 0, 0))


# ---------------------------------------------------------------- casters

def caster_bridge(cx, lidar=False) -> cq.Shape:
    z0, z1 = P.PAN_TOP, P.CASTER_PLATE_Z
    legs = [cyl((x, y, z0), "z", 16, z1 - z0) for x, y in _caster_pts(cx)]
    plate = rrect(cx + math.copysign(1.5, cx), 0, z1, z1 + 10, 63, 136, 14)  # nudged outboard, clear of the cable trough
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


def lidar_mount(cx) -> cq.Shape:
    """Ring that lifts the RPLIDAR C1 to the scan slot. Bolts to inserts in the pan."""
    z0 = P.PAN_TOP
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
    top0, top1 = P.CASTER_WHEEL + 3.0, P.CASTER_PLATE_Z - 2.0
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
    bx, by = BATT_LX, BATT_LY
    cx, cy = BATT_C
    z0 = BATT_Z0 - 8.0
    # 3 mm of air around the pack. Feet land on the side walls so each half is one solid.
    frame = rrect_shell(cx, cy, z0, z0 + 28, bx + 14, by + 14, 6, 4.0, open_top=True, open_bot=True)
    feet = []
    for x, y in CRADLE_PTS:
        # Stay on the wall. A foot that reaches inward lands in the pack.
        sign = 1.0 if x > 0 else -1.0
        feet.append(fuse(cyl((x, y, P.PAN_TOP), "z", 12, z0 - P.PAN_TOP + 4),
                         box(x - 4 * sign, x + 8 * sign, y - 10, y + 10, z0 - 2, z0 + 10)))
    s = fuse(frame, *feet)
    tools = [cyl((x, y, P.PAN_TOP - 1), "z", P.M3, 20) for x, y in CRADLE_PTS]
    # strap slots across the short side
    z0 = BATT_Z0 - 8.0
    for x in (-60, 60):
        tools.append(box(x - 13, x + 13, cy - by / 2 - 8, cy + by / 2 + 8, z0 + 16, z0 + 22))
    hw("M3x10 socket head", 4)
    hw("Velcro battery strap 25 mm", 2)
    return cut(s, *tools)


def _shelf(pts, outline_box, side, front) -> cq.Shape:
    x0, x1, y0, y1 = outline_box
    if side < 0:
        y0, y1 = -y1, -y0
    plate = rrect((x0 + x1) / 2, (y0 + y1) / 2, SHELF_Z, SHELF_Z + SHELF_T, x1 - x0, y1 - y0, 8)
    plate = plate.intersect(rrect(BX, 0, 0, 300, INNER_LX - 14, INNER_LY - 14, P.BASE_R - 14))
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
    # −y side, split so the two plates do not share a footprint.
    if side > 0:
        return _shelf(REAR_SHELF_PTS, (-110, -40, -155, -80), 1, False)
    return _shelf(FRONT_SHELF_PTS, (40, 100, -155, -80), 1, True)


def rear_shelf(side) -> cq.Shape:
    if side > 0:
        return _shelf(FRONT_SHELF_R_PTS, (108, 155, -155, -100), 1, True)
    return _shelf(REAR_SHELF_R_PTS, (-146, -112, 80, 136), 1, False)


# ---------------------------------------------------------------- bought envelopes

def bought() -> list[Bought]:
    import vendor as V

    out = []
    for sy, name in ((1, "hub_l"), (-1, "hub_r")):
        link = f"wheel_{'l' if sy > 0 else 'r'}"
        rot, stat = V.ddsm115()
        frame = dict(xdir=(1, 0, 0), zdir=(0, sy, 0))
        out += V.boughts(name, V.place(rot, (0, sy * P.WHEEL_Y, P.AXLE_Z), **frame), link, "base", "wheel", P.HUB_MASS - 300, "ddsm115")
        out += V.boughts(f"{name}_stator", V.place(stat, (0, sy * P.WHEEL_Y, P.AXLE_Z), **frame), "base", "base", "wheel", 300, "")
    # local y (200 mm) maps to world −x, local x (80 mm) maps to world y.
    out += V.boughts("battery", V.place(V.battery(), (BATT_C[0], BATT_C[1], BATT_Z0), xdir=(0, 1, 0), zdir=(0, 0, 1)),
                     "base", "base", "battery", P.BATT_MASS, "battery")
    out += V.boughts("charge_socket", V.place(V.gx16(), (P.CHARGE_XY[0], P.CHARGE_XY[1], P.BASE_TOP)), "base", "base", "electronics", 20, "gx16")
    out += V.boughts("lidar", V.place(V.rplidar_c1(), (P.LIDAR_X, 0, P.LIDAR_Z0)), "base", "base", "electronics", 110, "lidar")
    z = SHELF_Z + SHELF_T
    # −y bay, above the pan, inside the Ø400 shell and clear of the column (r = 50).
    boards = [
        ("ddsm_driver", (0, -104), V.small_board(40, 24, (10, 8, 3), look="pcb_black"), 20, "ddsmdriver"),
        ("imu", (-130, -45), V.small_board(22, 18, (4, 4, 1)), 5, "imu"),
        ("tmc2209", (-130, -20), V.small_board(16, 14, (4, 4, 1), look="pcb_black"), 5, "tmc"),
        ("reg_5v", (0, -162), V.small_board(22, 22, (8, 8, 3), look="pcb_blue"), 8, "pololu5"),
        ("reg_12v", (0, -132), V.small_board(22, 22, (8, 8, 3), look="pcb_blue"), 8, "pololu12"),
        ("fuse_block", (0, -72), V.fuse_block(40, 20, 24), 40, "fuse"),
        ("contactor_relay", (-130, -96), V.contactor(32, 22, 24), 60, "relay"),
        ("buck_12v", (-72, -112), V.finned_buck(74, 74, 32), 220, "buck12"),
        ("buck_12v_r", (72, -112), V.finned_buck(74, 74, 32), 220, "buck12"),
    ]
    for name, (x, y), pcs, m, key in boards:
        zz = z + (8.5 if name == "esp32" else 0.0)  # the devkit stands on its pin headers
        out += V.boughts(name, V.place(pcs, (x, y, zz)), "base", "base", "electronics", m, key)
    out += V.boughts("estop", V.place(V.estop(), (ESTOP_XY[0], ESTOP_XY[1], P.BASE_TOP)), "base", "base", "electronics", 80, "estop")
    glow = rrect_shell(BX, 0, LIGHT_Z[0] + 0.5, LIGHT_Z[1] - 0.5, SHELL_LX - 0.6, SHELL_LY - 0.6, P.BASE_R - 0.3, 1.2, open_top=True, open_bot=True)
    out.append(Bought("light_base", glow, "base", "base", "electronics", 15, "ledstrip", look="glow"))
    for cx in CASTERS:
        s = "f" if cx > 0 else "r"
        lx, ly, h = P.BALL_XFER
        r = P.CASTER_WHEEL / 2
        flange = rrect(cx, 0, h - 3, h, lx, ly, 6)
        flange = cut(flange, *[cyl((x, y, h - 4), "z", 4.0, 6) for x, y in _caster_pts(cx)])
        cup = cyl((cx, 0, r + 1), "z", 24, h - 3 - r - 1)
        ball = cq.Workplane("XY").sphere(r).translate((cx, 0, r)).val()
        out.append(Bought(f"ball_caster_{s}", fuse(flange, cup, ball), "base", "base", "metal", 35, "ballxfer", look="steel"))
    # No steel ballast. The three 1018 pads (about 5 kg) are gone; the smaller base
    # keeps the pack, the drivers and the lift motor low instead.
    return out


def drag_link() -> cq.Shape:
    """One link of the column service-loop chain. Six of them fold in the base trough.

    The chain is the slack for the 22 in of column travel. Each stage also has a
    zip-tie bar, so the sleeve cannot pull out of the chain or into a tube joint.
    """
    outer = rrect(0, 0, 0, 8, 18, 11, 2.4)
    inner = rrect(0, 0, -1, 9, 9, 4, 1.2)
    s = cut(outer, inner)
    s = cut(s, cyl((-6.5, 0, -1), "z", 2.2, 12), cyl((6.5, 0, -1), "z", 2.2, 12))
    return s


def cable_trough() -> cq.Shape:
    """Folded service loop behind the column. Open toward the rear window and open on top.

    The sleeve is clamped here and again on the cap. Slack stays in this channel, not in the bore.
    """
    outer = box(-90, -66, 12, 100, 42, 88)
    inner = box(-86, -62, 18, 94, 48, 100)  # open +x, toward the column window, and open on top
    s = cut(outer, inner)
    # Tongue into the outer-tube window. The flange below z=43 stays clear.
    s = fuse(s, box(-70, -48, 16, 28, 64, 86))
    for y in (24.0, 42.0):
        s = fuse(s, cyl((-78, y, P.PAN_TOP), "z", 12, 42 - P.PAN_TOP + 2))
    tools = []
    for y in (24.0, 42.0):
        tools.append(cyl((-78, y, P.PAN_TOP - 1), "z", P.M3, 24))
        tools.append(cyl((-78, y, P.PAN_TOP + 6), "z", P.M3_HEAD, 14))
    tools.append(cyl_between("y", (-72, 70), 96, 104, 4.2))
    hw("M3x12 socket head", 2)
    hw("4 in zip tie (column umbilical)", 1)
    return cut(s, *tools)


def parts() -> list[Part]:
    out = []
    out += shell_parts()
    out += pan_parts()
    for side, s in ((1, "l"), (-1, "r")):
        out.append(Part(f"wheel_bracket_{s}", wheel_bracket(side), "base", "base", color="frame",
                        note="Holds a DDSM115 by its stub (3 x M2.5 x 10). 5 walls, 40% infill."))
    out.append(Part("lidar_mount", lidar_mount(P.LIDAR_X), "base", "base", color="dark", rot=(0, 0, 0),
                    note="Lifts the RPLIDAR C1 to the slot in the shell. Three M3 into the pan."))
    cradle = battery_cradle()
    for sy, s in ((1, "l"), (-1, "r")):
        # The pack sits on +y, so the two halves meet on x = 0, not on the centreline.
        region = box(0, 400, -400, 400, 0, 400) if sy > 0 else box(-400, 0, -400, 400, 0, 400)
        half = split_one(cradle, region, f"battery_cradle_{s}")
        out.append(Part(f"battery_cradle_{s}", half, "base", "base", color="frame",
                        note="Two halves meet under the pack; the strap holds them together."))
    for side, s in ((1, "l"), (-1, "r")):
        out.append(Part(f"shelf_front_{s}", front_shelf(side), "base", "base", color="frame", rot=(180, 0, 0),
                        note="Motor drivers and the ESP32 on the 20 mm grid."))
        if side > 0:  # the +y rear corner is battery and e-stop only, so it has no shelf
            out.append(Part(f"shelf_rear_{s}", rear_shelf(side), "base", "base", color="frame", rot=(180, 0, 0),
                            note="Bucks, fuse block, contactor."))
    out.append(Part("cable_trough", cable_trough(), "base", "base", color="frame", rot=(0, 0, 0),
                    note="Service loop for the column umbilical. Zip-tie the sleeve at the closed end. 4 walls."))
    link = drag_link()
    for i, y in enumerate((26.0, 38.0, 50.0, 62.0, 74.0, 86.0)):
        placed = link.translate((-74.0, y, 56.0))
        out.append(Part(f"drag_link_{i}", placed, "base", "base", color="dark", rot=(0, 0, 0),
                        print_as="col_draglink", print_solid=link, walls=4, infill=30,
                        note="Drag-chain link. Six of them fold in the base trough for the column sleeve."))
    return out
