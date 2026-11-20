"""Printed cups for Feetech STS-series bus servos.

Nori A3 style: the servo sits in a printed sleeve, the horn screws to the
next link, and the STS3095's rear shaft runs in a printed hole. No printed
planetaries, no 6807 bearings, no hall homing. The servo's own encoder is
the joint encoder.

Local frame matches vendor.sts3215 / vendor.sts3095: shaft along +z at the
origin, horn face at z = 0, body in −z, length along +x.
"""

from __future__ import annotations

import cadquery as cq

import params as P
from lib import box, cyl, cut, fuse, rrect


# Cup "diameter" the arm bridges were drawn around (J2 3095).
D = 66.0


def dims(kind: str):
    """L, W, H, shaft_from_end, tab spacing along L, across W."""
    if kind == "sts3095":
        return (P.STS3095_L, P.STS3095_W, P.STS3095_H, P.STS3095_SHAFT_FROM_END,
                P.STS3095_HOLE_L, P.STS3095_HOLE_W)
    return (P.STS_L, P.STS_W, P.STS_H, P.STS_SHAFT_FROM_END, P.STS_HOLE_L, P.STS_HOLE_W)


def _placed(shape, origin, zdir, xdir):
    import vendor as V

    return V.place([("", shape, "")], origin, xdir=xdir, zdir=zdir)[0][1]


def mount(origin, zdir, xdir, kind="sts3095"):
    """For the parent link: (cup to fuse, insert holes to cut, keep-out to cut)."""
    L, W, H, s, hole_l, hole_w = dims(kind)
    wall = 3.5 if kind == "sts3095" else 3.0
    x0, x1 = -s, L - s
    cx = (x0 + x1) / 2
    flange_d = max(L + 2 * wall, W + 2 * wall, D)  # ≥66 mm so the old arm bridges still catch the cup
    sleeve = rrect(cx, 0, -H - wall, -2.0, L + 2 * wall, W + 2 * wall, 7.0)
    flange = cyl((0, 0, -5.0), "z", flange_d, 3.0)
    body = fuse(sleeve, flange)
    cavity = box(x0 - 0.35, x1 + 0.35, -W / 2 - 0.35, W / 2 + 0.35, -H - 0.35, 0.4)
    cable = box(x1 - 1.5, x1 + wall + 2, -6.5, 6.5, -H - wall - 1, -H + 14)
    tools = [cavity, cable]
    if kind == "sts3095":
        tools.append(cyl((0, 0, -H - wall - 1), "z", 8.4, wall + 6))  # rear shaft in printed hole
    cup = cut(body, *tools)
    inserts = []
    for dx in (-hole_l / 2, hole_l / 2):
        for dy in (-hole_w / 2, hole_w / 2):
            inserts.append(cyl((cx + dx, dy, -H - wall), "z", P.M3_INSERT, P.M3_INSERT_DEPTH + 0.4))
    horn_r = (P.STS3095_HORN_D if kind == "sts3095" else P.STS_HORN_D) / 2 + 2.0
    keep_bits = [
        cavity,
        cyl((0, 0, -0.2), "z", 2 * horn_r, 4.2),  # horn volume; child disc starts past this
        box(x0 - wall - 0.5, x1 + wall + 0.5, -W / 2 - wall - 0.5, W / 2 + wall + 0.5, -H - wall - 0.8, -2.0),
    ]
    if kind == "sts3095":
        keep_bits.append(cyl((0, 0, -H - 10), "z", 8.6, 12))  # rear shaft through the cup floor
    keep = fuse(*keep_bits)
    return _placed(cup, origin, zdir, xdir), _placed(fuse(*inserts), origin, zdir, xdir), _placed(keep, origin, zdir, xdir)


def instance(prefix, origin, zdir, xdir, parent, child, group, kind="sts3095"):
    """Bought servo in the parent cup. No printed gears."""
    import vendor as V

    if kind == "sts3095":
        pcs = V.sts3095()
        mass, key = P.STS3095_MASS, "sts3095"
    elif kind == "sts3250":
        pcs = [(sfx, shp, "alu" if not sfx else look) for sfx, shp, look in V.sts3215()]
        mass, key = P.STS3250_MASS, "sts3250"
    else:
        pcs = V.sts3215()
        mass, key = P.STS_MASS, "sts3215"
    placed = V.place(pcs, origin, xdir=xdir, zdir=zdir)
    return [], V.boughts(prefix, placed, parent, group, "actuator", mass, key)


def mirror_frame(origin, zdir, xdir):
    m = lambda v: (v[0], -v[1], v[2])  # noqa: E731
    return m(origin), m(zdir), m(xdir)
