"""Small CadQuery helpers shared by every Bob v3 part.

Everything returns cq.Solid / cq.Shape in the robot frame (mm).
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

import cadquery as cq

import params as P

V = cq.Vector

# Fasteners and bought hardware are tallied while parts are built, so the BOM
# counts what the CAD actually drilled, not a guess.
HARDWARE: Counter = Counter()


def hw(item: str, n: int = 1) -> None:
    HARDWARE[item] += n


@dataclass
class Part:
    """One printed part, placed in the robot frame at the zero pose."""

    name: str
    solid: cq.Shape
    link: str
    group: str  # viewer layer: base, mast, torso, arm, head
    qty: int = 1
    note: str = ""
    material: str = "PETG"
    color: str = "shell"  # shell | dark | accent | frame
    rot: tuple | None = None  # print orientation override (deg about x, y, z)
    walls: int = 4
    infill: int = 20
    print_as: str = ""  # identical prints share one STL and a quantity
    print_solid: object = None  # canonical shape to orient and export for print_as (defaults to solid)


@dataclass
class Bought:
    """Envelope for a bought item, for the viewer and the sim (not printed)."""

    name: str
    solid: cq.Shape
    link: str
    group: str
    kind: str  # actuator | electronics | battery | metal | wheel
    mass_g: float = 0.0
    bom: str = ""
    look: str = ""  # material for the viewer and the sim; defaults to kind


@dataclass
class Joint:
    name: str
    kind: str  # hinge | slide
    parent: str
    child: str
    anchor: tuple  # mm, robot frame, zero pose
    axis: tuple
    range: tuple
    actuator: str = ""  # BOM key of the motor
    gear: dict = field(default_factory=dict)
    mimic: str = ""  # follows this joint (the second gripper finger, the column mid stage)
    mimic_coef: float = 1.0  # child = coef * mimic; 0.5 for the cascade middle tube


# ---------------------------------------------------------------- primitives

def box(x0, x1, y0, y1, z0, z1) -> cq.Solid:
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cbox(cx, cy, cz, sx, sy, sz) -> cq.Solid:
    return box(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2)


def cyl(p, axis, d, length) -> cq.Solid:
    """Cylinder from point p along unit axis ('x','y','z' or a tuple)."""
    a = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1), "-x": (-1, 0, 0), "-y": (0, -1, 0), "-z": (0, 0, -1)}.get(axis, axis)
    return cq.Solid.makeCylinder(d / 2.0, length, V(*p), V(*a))


def cyl_between(axis: str, c, a0, a1, d) -> cq.Solid:
    """Cylinder along a world axis from coordinate a0 to a1, centred on c (the other two coords)."""
    a0, a1 = sorted((a0, a1))
    if axis == "x":
        return cyl((a0, c[0], c[1]), "x", d, a1 - a0)
    if axis == "y":
        return cyl((c[0], a0, c[1]), "y", d, a1 - a0)
    return cyl((c[0], c[1], a0), "z", d, a1 - a0)


def tube_between(axis, c, a0, a1, od, idia) -> cq.Shape:
    return cyl_between(axis, c, a0, a1, od).cut(cyl_between(axis, c, a0 - 1, a1 + 1, idia))


def rrect(cx, cy, z0, z1, lx, ly, r, chamfer_top=0.0, chamfer_bot=0.0) -> cq.Shape:
    """Rounded-rectangle prism (vertical edges filleted), optional 45° chamfers."""
    r = min(r, lx / 2 - 0.01, ly / 2 - 0.01)
    wp = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .center(cx, cy)
        .sketch()
        .rect(lx, ly)
        .vertices()
        .fillet(r)
        .finalize()
        .extrude(z1 - z0)
    )
    if chamfer_top > 0:
        wp = wp.faces(">Z").edges().chamfer(chamfer_top)
    if chamfer_bot > 0:
        wp = wp.faces("<Z").edges().chamfer(chamfer_bot)
    return wp.val()


def rrect_shell(cx, cy, z0, z1, lx, ly, r, wall, chamfer_top=0.0, chamfer_bot=0.0, open_top=False, open_bot=False):
    outer = rrect(cx, cy, z0, z1, lx, ly, r, chamfer_top, chamfer_bot)
    k = math.sqrt(2) - 1
    iz0 = z0 - 1 if open_bot else z0 + wall
    iz1 = z1 + 1 if open_top else z1 - wall
    inner = rrect(
        cx, cy, iz0, iz1, lx - 2 * wall, ly - 2 * wall, max(r - wall, 1.0),
        0 if open_top else max(chamfer_top - wall * k, 0.0),
        0 if open_bot else max(chamfer_bot - wall * k, 0.0),
    )
    return outer.cut(inner)


def hexagon(cx, cy, z0, z1, af) -> cq.Shape:
    ac = af * 2 / math.sqrt(3)
    return cq.Workplane("XY").workplane(offset=z0).center(cx, cy).polygon(6, ac).extrude(z1 - z0).val()


def fuse(*shapes) -> cq.Shape:
    shapes = [s for s in shapes if s is not None]
    acc = shapes[0]
    if len(shapes) > 1:
        acc = acc.fuse(*shapes[1:])
    return acc.clean()


def cut(base, *tools) -> cq.Shape:
    tools = [t for t in tools if t is not None]
    if not tools:
        return base
    return base.cut(*tools).clean()


def bolt_circle(n, pcd, start_deg=0.0):
    out = []
    for i in range(n):
        a = math.radians(start_deg + 360.0 * i / n)
        out.append((pcd / 2 * math.cos(a), pcd / 2 * math.sin(a)))
    return out


def largest(shape) -> cq.Shape:
    """Keep the biggest solid. Used after splitting a shell into tiles."""
    solids = shape.Solids()
    if len(solids) <= 1:
        return shape if not solids else solids[0]
    return max(solids, key=lambda s: s.Volume())


def mirror_y(shape) -> cq.Shape:
    return shape.mirror("XZ", (0, 0, 0))


def rr_boundary(x_or_y: str, value: float, lx: float, ly: float, r: float) -> float:
    """Distance from centre to a rounded-rect boundary along a line.

    rr_boundary('y', y, ...) returns the |x| of the boundary at that y.
    """
    hx, hy = lx / 2, ly / 2
    if x_or_y == "y":
        a, ha, hb = abs(value), hy, hx
    else:
        a, ha, hb = abs(value), hx, hy
    if a <= ha - r:
        return hb
    d = a - (ha - r)
    return hb - r + math.sqrt(max(r * r - d * d, 0.0))
