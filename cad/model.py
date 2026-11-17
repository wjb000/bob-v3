"""Printable Bob v3 chassis.

The deck drives. One SO-101 hand does the chores. No vac shoe, no dish tray,
no laundry bay. Vision is the cameras already on Bob v2, plus a shoe if you
move the Pi camera to the nose.

Robot frame: +X nose, +Y left, +Z up, ground z=0, origin at the deck centre.
Print copies are rotated onto the bed by export.py.
"""

from __future__ import annotations

import math

import cadquery as cq

import params as P


class Part:
    def __init__(self, name, solid, qty=1, note="", rot=(0.0, 0.0, 0.0)):
        self.name = name
        self.solid = solid
        self.qty = qty
        self.note = note
        self.rot = rot  # degrees about X, then Y, then Z, before dropping onto the bed


def cub(x0, y0, z0, x1, y1, z1):
    x0, x1 = sorted((float(x0), float(x1)))
    y0, y1 = sorted((float(y0), float(y1)))
    z0, z1 = sorted((float(z0), float(z1)))
    if min(x1 - x0, y1 - y0, z1 - z0) < 0.05:
        raise ValueError("degenerate box")
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0).translate(cq.Vector(x0, y0, z0))


def cyl_z(x, y, z0, z1, d):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def cyl_y(x, y0, y1, z, d):
    return cq.Solid.makeCylinder(d / 2, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))


def cyl_x(x0, x1, y, z, d):
    return cq.Solid.makeCylinder(d / 2, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0))


def fuse(shapes):
    acc = shapes[0]
    for s in shapes[1:]:
        acc = acc.fuse(s)
    return acc


def hex_z(cx, cy, z0, z1, af):
    # polygon() diameter is the across-corners circle. Flats = af.
    ac = af * 2 / math.sqrt(3)
    h = z1 - z0
    wp = cq.Workplane("XY").workplane(offset=z0).center(cx, cy).polygon(6, ac).extrude(h)
    return wp.val()


def cut_z(solid, x, y, z0, z1, d):
    return solid.cut(cyl_z(x, y, z0 - 1, z1 + 1, d))


def nut_pocket(solid, x, y, z_open, af=P.NUT_POCKET_AF, depth=P.NUT_POCKET_T):
    """Hex pocket opening downward. z_open is the bottom face the nut slides into."""
    return solid.cut(hex_z(x, y, z_open - 0.4, z_open + depth, af))


def nut_cup(solid, x, y, z_top, af=P.NUT_POCKET_AF, depth=P.NUT_POCKET_T):
    """Hex pocket opening upward. z_top is the face the nut drops into."""
    return solid.cut(hex_z(x, y, z_top - depth, z_top + 0.4, af))


# ---------------------------------------------------------------- holes

def _offsets(cell):
    return [(f - 0.5) * cell for f in (0.22, 0.50, 0.78)]


def deck_holes():
    """(x, y, kind) in the deck. kind is 'nut' or 'splice'."""
    holes = []
    # tile joints
    for row in range(P.NY):
        y0 = -P.DECK_W / 2 + row * P.CELL_Y
        cy = y0 + P.CELL_Y / 2
        for col in range(P.NX - 1):
            xj = -P.DECK_L / 2 + (col + 1) * P.CELL_X
            for dy in _offsets(P.CELL_Y):
                holes.append((xj - P.JOINT_OFF, cy + dy, "splice"))
                holes.append((xj + P.JOINT_OFF, cy + dy, "splice"))
    for col in range(P.NX):
        x0 = -P.DECK_L / 2 + col * P.CELL_X
        cx = x0 + P.CELL_X / 2
        yj = 0.0
        for dx in _offsets(P.CELL_X):
            holes.append((cx + dx, yj - P.JOINT_OFF, "splice"))
            holes.append((cx + dx, yj + P.JOINT_OFF, "splice"))
    # tower flange
    for dx in (-40.0, 40.0):
        for dy in (-40.0, 40.0):
            holes.append((P.TOWER_X + dx, P.TOWER_Y + dy, "nut"))
    # pods, four bolts each side, on the outer tiles of column 1
    for side in (1, -1):
        edge = side * P.DECK_W / 2
        for dx in (-24.0, 24.0):
            for inset in (16.0, 34.0):
                holes.append((P.TOWER_X + dx, edge - side * inset, "nut"))
    # casters
    for x in (-368.0, 368.0):
        for y in (-20.0, 20.0):
            holes.append((x, y, "nut"))
    # electronics, right-hand tile of column 2
    ex, ey = 97.5, -90.0
    for dx in (-50.0, 50.0):
        for dy in (-35.0, 35.0):
            holes.append((ex + dx, ey + dy, "nut"))
    # camera shoe, nose, left of centre so it misses the caster
    for dx in (-12.0, 12.0):
        holes.append((336.0 + dx, 55.0, "nut"))
    return holes


def motor_window():
    return (P.TOWER_X + P.ROD_X, 0.0, 52.0, 52.0)


def _tile_box(col, row):
    x0 = -P.DECK_L / 2 + col * P.CELL_X + P.GAP / 2
    y0 = -P.DECK_W / 2 + row * P.CELL_Y + P.GAP / 2
    return x0, y0, x0 + P.CELL_X - P.GAP, y0 + P.CELL_Y - P.GAP


def _in(x, y, box):
    x0, y0, x1, y1 = box
    return x0 + 2 < x < x1 - 2 and y0 + 2 < y < y1 - 2


# ---------------------------------------------------------------- deck

def _deck_tile(col, row):
    x0, y0, x1, y1 = _tile_box(col, row)
    top = P.DECK_TOP
    skin0 = top - P.SKIN
    shapes = [cub(x0, y0, skin0, x1, y1, top)]
    # two long ribs and one cross rib, kept off the holes by cutting later
    rib0 = skin0 - P.RIB_H
    for frac in (0.34, 0.66):
        y = y0 + (y1 - y0) * frac
        shapes.append(cub(x0 + 8, y - P.RIB_T / 2, rib0, x1 - 8, y + P.RIB_T / 2, skin0 + 0.3))
    x = (x0 + x1) / 2
    shapes.append(cub(x - P.RIB_T / 2, y0 + 8, rib0, x + P.RIB_T / 2, y1 - 8, skin0 + 0.3))
    # outer skirt
    sk = P.RIB_T
    if col == 0:
        shapes.append(cub(x0, y0, rib0, x0 + sk, y1, skin0 + 0.3))
    if col == P.NX - 1:
        shapes.append(cub(x1 - sk, y0, rib0, x1, y1, skin0 + 0.3))
    if row == 0:
        shapes.append(cub(x0, y0, rib0, x1, y0 + sk, skin0 + 0.3))
    if row == P.NY - 1:
        shapes.append(cub(x0, y1 - sk, rib0, x1, y1, skin0 + 0.3))
    # bosses under nut holes
    box = (x0, y0, x1, y1)
    local = [(x, y, k) for x, y, k in deck_holes() if _in(x, y, box)]
    for x, y, kind in local:
        if kind != "nut":
            continue
        shapes.append(cyl_z(x, y, top - P.SKIN - P.BOSS_EXTRA, skin0 + 0.3, P.BOSS_D))
    solid = fuse(shapes)
    # motor window. It straddles the centre joint, so each tile cuts its own overlap.
    wx, wy, ww, wd = motor_window()
    wx0, wy0, wx1, wy1 = wx - ww / 2, wy - wd / 2, wx + ww / 2, wy + wd / 2
    if min(x1, wx1) - max(x0, wx0) > 1 and min(y1, wy1) - max(y0, wy0) > 1:
        solid = solid.cut(cub(wx0, wy0, rib0 - 1, wx1, wy1, top + 1))
    for x, y, kind in local:
        solid = cut_z(solid, x, y, rib0 - 2, top + 1, P.M3)
        if kind == "nut":
            solid = nut_pocket(solid, x, y, top - P.SKIN - P.BOSS_EXTRA)
    return solid


def _splice(along, across_cell):
    """Bar that bridges one joint. along is 'x' or 'y' of the joint line."""
    length = across_cell - 28
    thick = 6.0
    width = 28.0
    z0, z1 = 0.0, thick
    if along == "y":
        # joint runs along Y, bar's long axis is Y
        solid = cub(-width / 2, -length / 2, z0, width / 2, length / 2, z1)
        for dy in _offsets(across_cell):
            for x in (-P.JOINT_OFF, P.JOINT_OFF):
                solid = cut_z(solid, x, dy, -1, thick + 1, P.M3)
                solid = nut_pocket(solid, x, dy, 0.0)
    else:
        solid = cub(-length / 2, -width / 2, z0, length / 2, width / 2, z1)
        for dx in _offsets(across_cell):
            for y in (-P.JOINT_OFF, P.JOINT_OFF):
                solid = cut_z(solid, dx, y, -1, thick + 1, P.M3)
                solid = nut_pocket(solid, dx, y, 0.0)
    return solid


def _place_splices():
    """Robot-frame copies. Print solids stay in their local frames.

    The long splice under the lift is split so it does not run through the motor.
    """
    thick = 6.0
    z = P.DECK_TOP - P.SKIN - thick
    placed = []
    sx = _splice("y", P.CELL_Y)
    for row in range(P.NY):
        cy = -P.DECK_W / 2 + (row + 0.5) * P.CELL_Y
        for col in range(P.NX - 1):
            xj = -P.DECK_L / 2 + (col + 1) * P.CELL_X
            placed.append(sx.translate(cq.Vector(xj, cy, z)))
    sy = _splice("x", P.CELL_X)
    stubs = []
    for col in range(P.NX):
        cx = -P.DECK_L / 2 + (col + 0.5) * P.CELL_X
        if abs(cx - P.TOWER_X) < 1.0:
            notched = sy.cut(cub(P.ROD_X - 32, -20, -1, P.ROD_X + 28, 20, thick + 2))
            pieces = [s for s in notched.Solids() if s.Volume() > 200]
            pieces.sort(key=lambda s: s.Center().x)
            if len(pieces) != 2:
                raise RuntimeError(f"tower splice split into {len(pieces)} pieces")
            stubs = pieces
            for piece in pieces:
                placed.append(piece.translate(cq.Vector(cx, 0.0, z)))
        else:
            placed.append(sy.translate(cq.Vector(cx, 0.0, z)))
    return sx, sy, stubs, placed


# ---------------------------------------------------------------- drive

def _pod(side):
    """side +1 is left. Axle along Y, plate stands in XZ."""
    axle_y = side * (P.DECK_W / 2 + 8 + P.WHEEL_WIDTH / 2)
    axle_x = P.TOWER_X
    plate_y0 = axle_y - side * P.POD_T / 2
    plate_y1 = axle_y + side * P.POD_T / 2
    z0 = P.DECK_TOP
    z1 = P.AXLE_Z + 18
    shapes = [cub(axle_x - 52, min(plate_y0, plate_y1), z0, axle_x + 52, max(plate_y0, plate_y1), z1)]
    # flange back onto the deck
    edge = side * P.DECK_W / 2
    fy_in = edge - side * 40
    fy_out = plate_y0 + side * 2  # overlap the upright so the fuse is one piece
    fy0, fy1 = sorted((fy_in, fy_out))
    shapes.append(cub(axle_x - 36, fy0, P.DECK_TOP, axle_x + 36, fy1, P.DECK_TOP + 5))
    gy0, gy1 = sorted((edge, plate_y0))
    shapes.append(cub(axle_x - 8, gy0, P.DECK_TOP, axle_x + 8, gy1, P.AXLE_Z - 10))
    solid = fuse(shapes)
    # axle bore, slit to the top, pinch screw
    solid = solid.cut(cyl_y(axle_x, min(plate_y0, plate_y1) - 2, max(plate_y0, plate_y1) + 2, P.AXLE_Z, P.AXLE_D))
    slit_y0, slit_y1 = sorted((plate_y0, plate_y1))
    solid = solid.cut(cub(axle_x - 1.2, slit_y0 - 1, P.AXLE_Z, axle_x + 1.2, slit_y1 + 1, z1 + 1))
    solid = solid.cut(cyl_y(axle_x, slit_y0 - 2, slit_y1 + 2, P.AXLE_Z + 12, P.M3))
    for dx in (-24.0, 24.0):
        for inset in (16.0, 34.0):
            solid = cut_z(solid, axle_x + dx, edge - side * inset, P.DECK_TOP - 1, P.DECK_TOP + 8, P.M3)
    return solid


def caster_axle_x(x_bolt):
    """Axle sits past the deck end so the roller can touch the floor."""
    direction = 1.0 if x_bolt > 0 else -1.0
    reach = P.CASTER_ROLLER_OD / 2 + 8.0
    return direction * P.DECK_L / 2 + direction * reach


def _caster_at(x_bolt):
    """Bolt plate in the rib bay, rails under the skirt, roller past the deck end."""
    direction = 1.0 if x_bolt > 0 else -1.0
    # Sit under the deck's nut bosses. The bosses already occupy the skin bay.
    plate_top = P.DECK_TOP - P.SKIN - P.BOSS_EXTRA - 0.4
    plate_bot = plate_top - 5.0
    edge = direction * P.DECK_L / 2
    plate_out = edge - direction * (P.RIB_T + 2.0)
    plate_in = x_bolt - direction * 20.0
    axle_x = caster_axle_x(x_bolt)
    axle_z = P.CASTER_AXLE_Z
    inner = P.CASTER_ROLLER_W / 2 + 2.0
    outer = inner + 4.0
    axle_end = axle_x + direction * 14.0
    shapes = [cub(plate_in, -28, plate_bot, plate_out, 28, plate_top)]
    for sign in (1.0, -1.0):
        y0, y1 = sign * inner, sign * outer
        shapes.append(cub(x_bolt - direction * 6, y0, 10, plate_out, y1, plate_top))
        shapes.append(cub(plate_out - direction * 6, y0, 10, axle_end, y1, 18))
        shapes.append(cub(axle_x - direction * 12, y0, axle_z - 8, axle_end, y1, axle_z + 8))
    solid = fuse(shapes)
    for y in (-20.0, 20.0):
        solid = cut_z(solid, x_bolt, y, plate_bot - 1, plate_top + 1, P.M3)
    solid = solid.cut(cyl_y(axle_x, -24, 24, axle_z, 8.4))
    return solid


def _roller():
    """Bore already vertical for the printer. Assembly rotates it onto the axle."""
    body = cyl_z(0, 0, 0, P.CASTER_ROLLER_W, P.CASTER_ROLLER_OD)
    return body.cut(cyl_z(0, 0, -1, P.CASTER_ROLLER_W + 2, 8.4))


# ---------------------------------------------------------------- lift

def _ear_xy():
    return [
        (-P.TD / 2 - 7, -46.0),
        (-P.TD / 2 - 7, 46.0),
        (8.0, -P.TW / 2 - 7),
        (8.0, P.TW / 2 + 7),
    ]


def _tower_local(kind, z0, z1):
    shapes = []
    # back and side walls. Front (+X) stays open so the carriage can pass.
    shapes.append(cub(-P.TD / 2, -P.TW / 2, z0, -P.TD / 2 + P.WALL, P.TW / 2, z1))
    shapes.append(cub(-P.TD / 2, -P.TW / 2, z0, P.TD / 2, -P.TW / 2 + P.WALL, z1))
    shapes.append(cub(-P.TD / 2, P.TW / 2 - P.WALL, z0, P.TD / 2, P.TW / 2, z1))
    # Short collars only. A full-height tube would fill the path the bearings ride.
    if kind == "bottom":
        collar = (z0, P.ROD_Z0 + 18.0)
    elif kind == "top":
        collar = (P.ROD_Z1 - 2.0, z1)
    else:
        collar = None
    if collar is not None:
        c0, c1 = collar
        for s in (1, -1):
            y = s * P.ROD_PITCH / 2
            shapes.append(cyl_z(P.ROD_X, y, c0, c1, 18))
            shapes.append(cub(-P.TD / 2, y - 4, c0, P.ROD_X, y + 4, c1))
    if kind == "bottom":
        shapes.append(cub(-P.TD / 2 - 6, -P.TW / 2 - 6, P.DECK_TOP, P.TD / 2 + 6, P.TW / 2 + 6, P.DECK_TOP + 6))
        # motor plate, shaft up, body hangs through the deck window
        shapes.append(cub(-P.TD / 2, -30, P.MOTOR_FACE_Z - 5, 24, 30, P.MOTOR_FACE_Z))
    if kind == "top":
        shapes.append(cub(-P.TD / 2, -P.TW / 2, z1 - 14, P.TD / 2, P.TW / 2, z1))
    if kind != "top":
        for x, y in _ear_xy():
            shapes.append(cub(x - 9, y - 9, z1 - 8, x + 9, y + 9, z1))
    if kind != "bottom":
        for x, y in _ear_xy():
            shapes.append(cub(x - 9, y - 9, z0, x + 9, y + 9, z0 + 12))
    solid = fuse(shapes)
    # rod holes
    for s in (1, -1):
        y = s * P.ROD_PITCH / 2
        if kind == "bottom":
            solid = solid.cut(cyl_z(P.ROD_X, y, P.ROD_Z0, z1 + 1, P.ROD_HOLE))
        elif kind == "top":
            solid = solid.cut(cyl_z(P.ROD_X, y, z0 - 1, P.ROD_Z1, P.ROD_HOLE))
        else:
            solid = solid.cut(cyl_z(P.ROD_X, y, z0 - 1, z1 + 1, P.ROD_HOLE))
    # screw clearance. The top lid stays an 8.6 mm printed bushing.
    if kind == "top":
        solid = solid.cut(cyl_z(P.ROD_X, 0, z0 - 1, z1 - 14, 12))
        solid = solid.cut(cyl_z(P.ROD_X, 0, z1 - 14.4, z1 + 1, 8.6))
    elif kind != "bottom":
        solid = solid.cut(cyl_z(P.ROD_X, 0, z0 - 1, z1 + 1, 12))
    else:
        solid = solid.cut(cyl_z(P.ROD_X, 0, P.MOTOR_FACE_Z - 1, z1 + 1, 12))
        # NEMA face: 4 bolts and a pilot recess on the underside of the plate
        for dx in (-P.MOTOR_BOLT / 2, P.MOTOR_BOLT / 2):
            for dy in (-P.MOTOR_BOLT / 2, P.MOTOR_BOLT / 2):
                solid = cut_z(solid, P.ROD_X + dx, dy, P.MOTOR_FACE_Z - 6, P.MOTOR_FACE_Z + 1, P.M3)
        solid = solid.cut(cyl_z(P.ROD_X, 0, P.MOTOR_FACE_Z - 6, P.MOTOR_FACE_Z - 3, P.MOTOR_PILOT))
        # deck bolts
        for dx in (-40.0, 40.0):
            for dy in (-40.0, 40.0):
                solid = cut_z(solid, dx, dy, P.DECK_TOP - 1, P.DECK_TOP + 8, P.M3)
        # motor window through the flange
        solid = solid.cut(cub(P.ROD_X - 26, -26, P.DECK_TOP - 1, P.ROD_X + 26, 26, P.DECK_TOP + 6.2))
        # limit switch slots on the left wall, slide 8 mm
        sw_z = P.LOWER_BEARING_MIN - 18
        for dz in (-P.SW_PITCH / 2, P.SW_PITCH / 2):
            solid = solid.cut(cub(-2, -P.TW / 2 - 1, sw_z + dz - 1.2, 8, -P.TW / 2 + P.WALL + 1, sw_z + dz + 8))
    if kind != "bottom":
        for x, y in _ear_xy():
            solid = cut_z(solid, x, y, z0 - 1, z0 + 14, P.M3)
    if kind != "top":
        for x, y in _ear_xy():
            solid = cut_z(solid, x, y, z1 - 10, z1 + 1, P.M3)
            solid = nut_cup(solid, x, y, z1)
    solid = solid.translate(cq.Vector(P.TOWER_X, P.TOWER_Y, 0))
    return solid


def _bearing_cap():
    solid = cyl_z(0, 0, 0, 3.5, 28)
    solid = cut_z(solid, 0, 0, -1, 5, P.ROD_HOLE)
    for x in (-12.0, 12.0):
        solid = cut_z(solid, x, 0, -1, 5, P.M3)
    return solid


def _carriage():
    ox = P.TOWER_X + P.ROD_X
    lo = P.LOWER_BEARING_MIN
    span = P.BEARING_SPAN
    h = P.HOUSING
    shapes = []
    for s in (1, -1):
        y = P.TOWER_Y + s * P.ROD_PITCH / 2
        # column ties the two bearings. 22 mm stays outside the 15.6 mm bore.
        shapes.append(cub(ox - 11, y - 11, lo - 16, ox + 11, y + 11, lo + span + 16))
        for zc in (lo, lo + span):
            shapes.append(cub(ox - h / 2, y - h / 2, zc - 16, ox + h / 2, y + h / 2, zc + 16))
        # lip under each housing so the LM8UU cannot fall through
        shapes.append(cyl_z(ox, y, lo - 18, lo - 14, 22))
        shapes.append(cyl_z(ox, y, lo + span - 18, lo + span - 14, 22))
    # bridge that holds the T8 nut, between the lower housings
    shapes.append(cub(ox - 16, -P.ROD_PITCH / 2, lo - 14, ox + 16, P.ROD_PITCH / 2, lo + 16))
    # spine starts in front of the leadscrew and climbs to the arm-plate pad
    pcx, pcy = P.plate_center()
    pad_top = P.PLATE_TOP_LO - P.PLATE_T
    shapes.append(cub(ox + 14, -14, lo - 8, pcx - 30, 14, pad_top))
    shapes.append(cub(pcx - 84, -56, pad_top - 8, pcx + 84, 56, pad_top))
    # homing tab stays inside the tower opening, just clear of the left wall
    sw_z = P.LOWER_BEARING_MIN - 18
    shapes.append(cub(ox + 6, -62, sw_z + 1, ox + 20, -P.ROD_PITCH / 2 + 14, sw_z + 7))
    solid = fuse(shapes)
    for s in (1, -1):
        y = P.TOWER_Y + s * P.ROD_PITCH / 2
        solid = solid.cut(cyl_z(ox, y, lo - 20, lo + span + 20, P.BEARING_BORE))
        solid = solid.cut(cyl_z(ox, y, lo - 22, lo - 14, P.ROD_HOLE))
        solid = solid.cut(cyl_z(ox, y, lo + span - 20, lo + span - 13, P.ROD_HOLE))
        for zc in (lo, lo + span):
            for dx in (-12.0, 12.0):
                solid = cut_z(solid, ox + dx, y, zc + 10, zc + 18, P.M3)
                solid = nut_cup(solid, ox + dx, y, zc + 16)
    # T8 flange nut drops in from the underside of the bridge
    solid = solid.cut(cub(
        ox - P.T8_POCKET / 2, -P.T8_POCKET / 2, lo - 14.2,
        ox + P.T8_POCKET / 2, P.T8_POCKET / 2, lo - 14 + P.T8_POCKET_D,
    ))
    solid = solid.cut(cyl_z(ox, 0, lo - 20, lo + 20, P.T8_HOLE))
    # Screws thread into the T8 nut. No extra hex nuts.
    r = P.T8_PCD / 2 / math.sqrt(2)
    for sx in (1, -1):
        for sy in (1, -1):
            solid = cut_z(solid, ox + sx * r, sy * r, lo - 16, lo + 18, P.M3)
    # arm plate bolts, nuts in the pad
    for dx in (-74.0, 74.0):
        for dy in (-46.0, 46.0):
            solid = cut_z(solid, pcx + dx, pcy + dy, pad_top - 12, pad_top + 2, P.M3)
            solid = nut_pocket(solid, pcx + dx, pcy + dy, pad_top - 8)
    # windows under the strap slots so those screws nut against the plate
    half = P.STRAP_LEN / 2
    for y in (-P.STRAP_Y, P.STRAP_Y):
        for xoff in (-half + 10, half - 10):
            solid = solid.cut(cub(
                pcx + xoff - 9, pcy + y - 9, pad_top - 12,
                pcx + xoff + 9, pcy + y + 9, pad_top + 1,
            ))
    return solid


def _arm_plate():
    pcx, pcy = P.plate_center()
    z0 = P.PLATE_TOP_LO - P.PLATE_T
    z1 = P.PLATE_TOP_LO
    solid = cub(pcx - P.PLATE_L / 2, pcy - P.PLATE_W / 2, z0, pcx + P.PLATE_L / 2, pcy + P.PLATE_W / 2, z1)
    for dx in (-74.0, 74.0):
        for dy in (-46.0, 46.0):
            solid = cut_z(solid, pcx + dx, pcy + dy, z0 - 1, z1 + 1, P.M3)
    # strap feet. Slots so the strap can slide off the SO-101 foot.
    for y in (-P.STRAP_Y, P.STRAP_Y):
        for x in (-P.STRAP_LEN / 2 + 10, P.STRAP_LEN / 2 - 10):
            solid = solid.cut(cub(pcx + x - 5, pcy + y - P.M3 / 2, z0 - 1, pcx + x + 5, pcy + y + P.M3 / 2, z1 + 1))
    return solid


def _strap():
    """One strap in the robot frame, on +Y. The other is a mirror."""
    pcx, pcy = P.plate_center()
    y = pcy + P.STRAP_Y
    z_bar = P.PLATE_TOP_LO + P.STRAP_CLEAR
    half = P.STRAP_LEN / 2
    bar = cub(pcx - half, y - P.STRAP_W / 2, z_bar, pcx + half, y + P.STRAP_W / 2, z_bar + P.STRAP_T)
    feet = []
    for x in (-half + 10, half - 10):
        feet.append(cub(pcx + x - 8, y - 8, P.PLATE_TOP_LO, pcx + x + 8, y + 8, z_bar + 0.2))
    solid = fuse([bar] + feet)
    for x in (-half + 10, half - 10):
        solid = solid.cut(cub(pcx + x - 5, y - P.M3 / 2, P.PLATE_TOP_LO - 1, pcx + x + 5, y + P.M3 / 2, z_bar + P.STRAP_T + 1))
    return solid


# ---------------------------------------------------------------- small parts

def _elec():
    ex, ey = 97.5, -90.0
    z0 = P.DECK_TOP
    z1 = z0 + 3.0
    solid = cub(ex - 70, ey - 52, z0, ex + 70, ey + 52, z1)
    # bosses
    shapes = [solid]
    for dx in (-50.0, 50.0):
        for dy in (-35.0, 35.0):
            shapes.append(cyl_z(ex + dx, ey + dy, z0, z0 + 6, 10))
    solid = fuse(shapes)
    for dx in (-50.0, 50.0):
        for dy in (-35.0, 35.0):
            solid = cut_z(solid, ex + dx, ey + dy, z0 - 1, z0 + 8, P.M3)
    # Pi 5 hole rectangle 58 x 49, M2.5, board kept inside the tray
    px, py = ex - 10, ey + 8
    for dx in (-29.0, 29.0):
        for dy in (-24.5, 24.5):
            solid = cut_z(solid, px + dx, py + dy, z0 - 1, z0 + 8, P.M25)
    # zip slots for the buck and the driver boards
    for x in (ex + 28, ex + 48):
        solid = solid.cut(cub(x, ey - 30, z0 - 1, x + 3.5, ey - 16, z1 + 1))
        solid = solid.cut(cub(x, ey + 16, z0 - 1, x + 3.5, ey + 30, z1 + 1))
    return solid


def _cam_shoe():
    """Cradle for the existing Pi camera. No new camera in the BOM."""
    x, y = 336.0, 55.0
    z0 = P.DECK_TOP
    # module is about 25 x 24. A U that aims it forward (+X).
    shapes = [cub(x - 20, y - 16, z0, x + 20, y + 16, z0 + 4)]
    shapes.append(cub(x - 16, y - 16, z0 + 3.7, x + 8, y - 12, z0 + 20))
    shapes.append(cub(x - 16, y + 12, z0 + 3.7, x + 8, y + 16, z0 + 20))
    shapes.append(cub(x - 16, y - 16, z0 + 3.7, x - 12, y + 16, z0 + 18))
    solid = fuse(shapes)
    for dx in (-12.0, 12.0):
        solid = cut_z(solid, x + dx, y, z0 - 1, z0 + 6, P.M3)
    return solid


def _pad_clip():
    """Cloth tab the gripper pinches. Not mounted on the base."""
    solid = cub(0, 0, 0, 48, 18, 8)
    # neck
    solid = solid.cut(cub(30, 0, 0, 48, 2, 8))
    solid = solid.cut(cub(30, 16, 0, 48, 18, 8))
    # cloth slot
    solid = solid.cut(cub(2, 7.5, 6.2, 26, 10.5, 9))
    return solid


def _cable_clip():
    solid = cub(0, 0, 0, 18, 14, 8)
    solid = solid.cut(cyl_y(6, -1, 16, 4, 6))
    solid = cut_z(solid, 13, 7, -1, 10, P.M3)
    return solid


# ---------------------------------------------------------------- build

def build():
    """Return (print_parts, assembly_solids). Assembly solids are already placed."""
    prints = []
    assy = []

    for col in range(P.NX):
        for row in range(P.NY):
            name = f"deck_c{col}_r{row}"
            solid = _deck_tile(col, row)
            prints.append(Part(name, solid, note="Deck tile. Ribs down. Nuts in from below."))
            assy.append((name, solid))

    sx, sy, stubs, splices = _place_splices()
    prints.append(Part("splice_x", sx, qty=(P.NX - 1) * P.NY, note="Bridges the short joints. Nuts in from below."))
    prints.append(Part("splice_y", sy, qty=P.NX * (P.NY - 1) - 1, note="Bridges the long joints, except under the lift."))
    for i, stub in enumerate(stubs):
        side = "rear" if i == 0 else "front"
        prints.append(Part(
            f"splice_tower_{side}",
            stub,
            note="Short joint beside the motor window. Nuts in from below.",
        ))
    for i, s in enumerate(splices):
        assy.append((f"splice_{i}", s))

    for side, name in ((1, "pod_left"), (-1, "pod_right")):
        solid = _pod(side)
        prints.append(Part(name, solid, rot=(-90, 0, 0), note="Lay the plate flat. Drill AXLE_D to the hub."))
        assy.append((name, solid))

    nose = _caster_at(368.0)
    tail = _caster_at(-368.0)
    # print one caster in a local frame: shift the nose caster onto the origin for a cleaner STL
    bb = nose.BoundingBox()
    caster_print = nose.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))
    prints.append(Part("caster", caster_print, qty=2, rot=(-90, 0, 0), note="Nose and tail. Bore ends up vertical."))
    assy.append(("caster_nose", nose))
    assy.append(("caster_tail", tail))
    roller = _roller()
    prints.append(Part("roller", roller, qty=2, note="Bore already vertical. Sits past the deck end."))
    for x, tag in ((368.0, "nose"), (-368.0, "tail")):
        spun = roller.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
        spun = spun.translate(cq.Vector(caster_axle_x(x), -P.CASTER_ROLLER_W / 2, P.CASTER_AXLE_Z))
        assy.append((f"roller_{tag}", spun))

    zs = P.segment_zs()
    kinds = ["bottom"] + ["mid"] * (len(zs) - 2) + ["top"]
    for i, ((z0, z1), kind) in enumerate(zip(zs, kinds)):
        name = f"tower_{i}_{kind}"
        solid = _tower_local(kind, z0, z1)
        note = "Open front faces the nose. Rods align the stack."
        prints.append(Part(name, solid, note=note))
        assy.append((name, solid))

    prints.append(Part("bearing_cap", _bearing_cap(), qty=4, note="One on each LM8UU, rod hole up."))
    carriage = _carriage()
    prints.append(Part("carriage", carriage, note="Slide it onto the rods before the top cap."))
    assy.append(("carriage", carriage))
    plate = _arm_plate()
    prints.append(Part("arm_plate", plate, note="SO-101 base is clamped, not screwed. Straps are slotted."))
    assy.append(("arm_plate", plate))
    strap = _strap()
    strap_m = strap.mirror("XZ")
    prints.append(Part("arm_strap", strap, qty=2, note="Print two. One flips to the other side."))
    assy.append(("strap_left", strap))
    assy.append(("strap_right", strap_m))

    elec = _elec()
    prints.append(Part("elec_tray", elec, note="Pi 5 holes are 58 × 49, M2.5. Buck is zip-tied."))
    assy.append(("elec_tray", elec))
    cam = _cam_shoe()
    prints.append(Part("cam_shoe", cam, note="Existing Pi camera. No new camera."))
    assy.append(("cam_shoe", cam))
    prints.append(Part("pad_clip", _pad_clip(), note="Gripper pinches the neck. Cloth goes in the slot."))
    prints.append(Part("cable_clip", _cable_clip(), qty=8, note="Zip or M3. Cable along the tower."))
    return prints, assy
