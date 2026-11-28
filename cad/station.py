"""Floor dock. A separate station, not a part of the robot.

Bob reverses until his origin is at DOCK_X. Two brass strips under the pan
then sit on the two pads, and the pack charges through the BMS.

The plate is two islands. The wheels (y = ±185) and the casters (y = 0)
stay on the bare floor, so he does not have to climb.
"""

from __future__ import annotations

from lib import Part, box, fuse

# Robot origin when the strips are on the pads. CAD frame, mm.
DOCK_X = -550.0

# Strips in the robot frame. The pan ribs sit on x = 0 and x = 60, y = 0 and y = 60.
# This bay is the open cell between those ribs, under the centre tile.
STRIP_X = (10.0, 46.0)
STRIP_YS = ((26.0, 42.0), (-42.0, -26.0))  # +Y is pack positive, -Y is pack negative
SHOE_Z = (15.5, 17.5)  # 2 mm brass shoe. Floor clearance is 15.5 mm.
STEM_X = (24.0, 32.0)
STEM_YS = ((30.0, 38.0), (-38.0, -30.0))
STEM_Z = (17.5, 33.8)  # up into a pocket in the pan skin, 0.4 mm short of the pocket roof

# Pads in the world. Same footprint as the shoes, shifted by DOCK_X.
# Top is the shoe top, so a docked robot crushes the shoe 2 mm into the pad.
PAD_Z = (8.05, 17.0)

# Inner islands carry the pads and stay clear of the wheels (|y| = 185) and the casters (y = 0).
# Outer rails sit outside the tires so the plate is visible beside the shell.
# The rear lip is on the wall side, outside the shell even if he overshoots by 20 mm.
X0, X1 = -840.0, -280.0
ISLANDS = ((24.0, 156.0), (-156.0, -24.0), (214.0, 340.0), (-340.0, -214.0))
T = 8.0
NX = 3
BED = 200.0


def contacts_meet(origin_x: float = DOCK_X) -> bool:
    """True when a robot at origin_x has both shoes overlapping the pads."""
    sx0, sx1 = STRIP_X[0] + origin_x, STRIP_X[1] + origin_x
    px0, px1 = STRIP_X[0] + DOCK_X, STRIP_X[1] + DOCK_X
    z_overlap = SHOE_Z[0] < PAD_Z[1] and PAD_Z[0] < SHOE_Z[1]
    x_overlap = sx0 < px1 and px0 < sx1
    return bool(z_overlap and x_overlap)


def pockets():
    """Blind pockets in the pan skin. Each stem has 0.6 mm clearance."""
    out = []
    for y0, y1 in STEM_YS:
        out.append((STEM_X[0] - 0.6, STEM_X[1] + 0.6, y0 - 0.6, y1 + 0.6, 30.0, 34.2))
    return out


def _strip(sign: int):
    shoe_y = STRIP_YS[0] if sign > 0 else STRIP_YS[1]
    stem_y = STEM_YS[0] if sign > 0 else STEM_YS[1]
    shoe = box(*STRIP_X, *shoe_y, *SHOE_Z)
    stem = box(*STEM_X, *stem_y, *STEM_Z)
    return fuse(shoe, stem)


def strips():
    """(name, solid) in the robot frame."""
    return [("charge_strip_pos", _strip(1)), ("charge_strip_neg", _strip(-1))]


def _pad(sign: int):
    y0, y1 = STRIP_YS[0] if sign > 0 else STRIP_YS[1]
    return box(STRIP_X[0] + DOCK_X, STRIP_X[1] + DOCK_X, y0, y1, *PAD_Z)


def pads():
    return [("dock_pad_pos", _pad(1)), ("dock_pad_neg", _pad(-1))]


def _tiles():
    dx = (X1 - X0) / NX
    out = []
    # pi/ni are the pad islands. po/no are the rails outside the tires.
    for tag, (ya, yb) in zip(("pi", "ni", "po", "no"), ISLANDS):
        for i in range(NX):
            xa, xb = X0 + i * dx, X0 + (i + 1) * dx
            s = box(xa, xb, ya, yb, 0, T)
            if i == 0:
                s = fuse(s, box(xa, xa + 12, ya, yb, 0, T + 12))  # wall lip, behind the shell
            out.append((f"dock_{i}{tag}", s))
    return out


def parts():
    made = []
    for name, s in _tiles():
        made.append(Part(
            name, s, "world", "station", color="frame",
            note="Charge-dock tile. Prints flat. Screw it to the next tile from below.",
        ))
    for name, s in pads():
        made.append(Part(
            name, s, "world", "station", color="brass",
            note="Glue a brass shim here. The strip under the base lands on it and the pack charges.",
        ))
    return made


def fits_bed() -> bool:
    for _, s in _tiles() + pads():
        bb = s.BoundingBox()
        if max(bb.xlen, bb.ylen, bb.zlen) > BED:
            return False
    return True


def dock_spec() -> dict:
    """Numbers the viewer uses to drive him on and to call it charging. Metres and radians."""
    return {
        "x": DOCK_X / 1000.0,
        "y": 0.0,
        "tol": 0.02,
        "yTol": 0.04,
        "yawTol": 0.08,
    }
