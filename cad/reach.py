#!/usr/bin/env python3
"""Fail if the hand cannot work in front of the bumper.

Joint frames are so101_new_calib.urdf, the same numbers as the viewer.
The gripper point is the gripper-joint origin, not the fingertip.
Run: python3 cad/reach.py
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import params as P  # noqa: E402

# xyz metres, rpy radians, joint limits. Fixed frames, then rotation about Z.
JOINTS = [
    ([0.0388353, 0.0, 0.0624], [math.pi, 0.0, -math.pi], (-1.92, 1.92)),
    ([-0.0303992, -0.0182778, -0.0542], [-math.pi / 2, -math.pi / 2, 0.0], (-1.75, 1.75)),
    ([-0.11257, -0.028, 0.0], [0.0, 0.0, math.pi / 2], (-1.75, 1.75)),
    ([-0.1349, 0.0052, 0.0], [0.0, 0.0, -math.pi / 2], (-1.66, 1.66)),
    ([0.0, -0.0611, 0.0181], [math.pi / 2, 0.0486795, math.pi], (0.0, 0.0)),
    ([0.0202, 0.0188, -0.0234], [math.pi / 2, 0.0, 0.0], (0.0, 0.0)),
]


def _mul(a, b):
    c = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            c[i][j] = sum(a[i][k] * b[k][j] for k in range(4))
    return c


def _rpy(roll, pitch, yaw):
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    # R = Rz @ Ry @ Rx
    r = [
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr, 0.0],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr, 0.0],
        [-sp, cp * sr, cp * cr, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
    return r


def _trans(x, y, z):
    return [
        [1.0, 0.0, 0.0, x],
        [0.0, 1.0, 0.0, y],
        [0.0, 0.0, 1.0, z],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _rotz(q):
    c, s = math.cos(q), math.sin(q)
    return [
        [c, -s, 0.0, 0.0],
        [s, c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def grip(qs):
    t = _trans(0, 0, 0)
    for (xyz, rpy, _lim), q in zip(JOINTS, qs):
        t = _mul(t, _mul(_mul(_trans(*xyz), _rpy(*rpy)), _rotz(q)))
    return t[0][3] * 1000.0, t[1][3] * 1000.0, t[2][3] * 1000.0


def main() -> None:
    px, _py = P.plate_center()
    nose = P.DECK_L / 2
    z_lo = P.PLATE_TOP_LO
    z_hi = P.PLATE_TOP_HI
    zero = grip([0, 0, 0, 0, 0, 0])
    if abs(zero[0] - 316.6) > 0.2 or abs(zero[2] - 255.5) > 0.2:
        raise SystemExit(f"zero pose grip moved: {zero}")

    rng = random.Random(0)
    lims = [j[2] for j in JOINTS[:4]]
    best_past = -1e9
    floor = False
    counter = False
    table = False
    for _ in range(20000):
        q = [rng.uniform(a, b) for a, b in lims] + [0.0, 0.0]
        lx, _ly, lz = grip(q)
        for base_z in (z_lo, (z_lo + z_hi) / 2, z_hi):
            x = lx + px
            z = lz + base_z
            past = x - nose
            if past > best_past:
                best_past = past
            if past > 80 and z < 40:
                floor = True
            if past > 120 and 860 <= z <= 980:
                counter = True
            if past > 150 and 700 <= z <= 800:
                table = True
    print(f"plate x {px:.1f} mm  nose {nose:.1f}  best past nose {best_past:.0f} mm")
    print(f"floor {floor}  table {table}  counter {counter}")
    if best_past < 200:
        raise SystemExit("hand does not reach 200 mm past the nose")
    if not floor:
        raise SystemExit("hand does not reach the floor in front of the nose")
    if not table:
        raise SystemExit("hand does not reach a 750 mm table past the nose")
    if not counter:
        raise SystemExit("hand does not reach a 900 mm counter past the nose")
    cols = [-P.DECK_L / 2 + (i + 0.5) * P.CELL_X for i in range(P.NX)]
    if not any(abs(c - P.TOWER_X) < 1 for c in cols):
        raise SystemExit("tower is not on a tile centre")
    if P.CELL_X > P.BED or P.CELL_Y > P.BED:
        raise SystemExit("a deck tile exceeds the bed")


if __name__ == "__main__":
    main()
