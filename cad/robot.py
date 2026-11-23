"""The whole robot: parts, bought envelopes, links, joints, poses, forward kinematics."""

from __future__ import annotations

import math

import numpy as np

import params as P
import arm
import base
import column
import head
import torso
from lib import HARDWARE, Joint, Part


def joints() -> list[Joint]:
    out = [
        Joint("lift", "slide", "base", "lift", (P.COL_X, 0.0, 0.0), (0, 0, 1), P.LIMITS["lift"], "nema"),
        Joint("lift_mid", "slide", "base", "lift_mid", (P.COL_X, 0.0, 0.0), (0, 0, 1),
              (0.0, P.STAGE_TRAVEL / 1000.0), mimic="lift", mimic_coef=1.0 / 3.0),
        Joint("lift_upper", "slide", "base", "lift_upper", (P.COL_X, 0.0, 0.0), (0, 0, 1),
              (0.0, 2 * P.STAGE_TRAVEL / 1000.0), mimic="lift", mimic_coef=2.0 / 3.0),
        Joint("wheel_l", "hinge", "base", "wheel_l", (0.0, P.WHEEL_Y, P.AXLE_Z), (0, 1, 0), (-1e9, 1e9), "hub"),
        Joint("wheel_r", "hinge", "base", "wheel_r", (0.0, -P.WHEEL_Y, P.AXLE_Z), (0, 1, 0), (-1e9, 1e9), "hub"),
    ]
    out += head.joints()
    out += arm.joints("l")
    out += arm.joints("r")
    return out


def parts() -> list[Part]:
    HARDWARE.clear()
    out = []
    out += base.parts()
    out += column.parts()
    out += torso.torso_parts()
    out += head.parts()
    out += arm.parts("l")
    out += arm.parts("r")
    return out


def bought():
    return base.bought() + column.bought() + torso.bought() + head.bought() + arm.bought("l") + arm.bought("r")


def joiners():
    """Placed joiner tabs: (link, solid). Every one is the same printed part."""
    out = [("base", s) for s in base.joiner_placed()]
    out += [("lift", s) for s in torso.torso_joiners()]
    out += [("head_tilt", s) for s in head.head_joiners()]
    return out


# A pose is a dict joint name -> value (rad or m). Missing joints are zero.
HOME = {
    "lift": 0.10,
    "head_tilt": 0.25,
    **{f"{s}_{k}": v for s in ("l", "r") for k, v in {
        "shoulder_pitch": -0.80, "shoulder_roll": 0.10, "elbow": -1.40, "wrist_pitch": 0.35, "gripper": 0.012, "gripper_b": 0.012}.items()},
}
# HOME is also the carry pose: elbows forward and above the base top, so the lift can run
# its whole travel (0 to LIFT_TRAVEL) in this pose without an arm touching the base.
# export.py checks it at the bottom and the top of travel.
POSES = {
    "zero": {"lift": 0.455},  # arms hang straight; any lower and the fingers meet the base shell
    "home": HOME,
    # counter, floor and shelf are IK solutions to the targets sim/check.py verifies (same values both arms: they mirror)
    "counter": {**HOME, "lift": 0.35, "head_tilt": 0.55,
                **{f"{s}_{k}": v for s in ("l", "r") for k, v in {
                    "shoulder_pitch": -1.492, "shoulder_roll": -0.008, "upper_arm_yaw": -0.015, "elbow": -1.403,
                    "wrist_pitch": 1.894, "wrist_roll": 0.016, "gripper": 0.03, "gripper_b": 0.03}.items()}},
    "floor": {**HOME, "lift": 0.0, "head_tilt": 0.55,
              **{f"{s}_{k}": v for s in ("l", "r") for k, v in {
                  "shoulder_pitch": -0.805, "shoulder_roll": 0.0, "upper_arm_yaw": 0.0, "elbow": 0.0,
                  "wrist_pitch": 0.0, "wrist_roll": 0.0, "gripper": 0.02, "gripper_b": 0.02}.items()}},
    "shelf": {**HOME, "lift": P.LIFT_TRAVEL / 1000.0, "head_tilt": -0.35,
              **{f"{s}_{k}": v for s in ("l", "r") for k, v in {
                  "shoulder_pitch": -2.9, "shoulder_roll": 0.0, "upper_arm_yaw": 0.0, "elbow": -0.45,
                  "wrist_pitch": 0.7, "wrist_roll": 0.0, "gripper": 0.02, "gripper_b": 0.02}.items()}},
    "wave": {**HOME, "lift": 0.30, "head_pan": 0.35, "l_shoulder_pitch": -0.25, "l_shoulder_roll": 1.45,
             "l_upper_arm_yaw": 0.0, "l_elbow": -1.4, "l_wrist_pitch": 0.0},
}


def _rot(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    x, y, z = a
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([
        [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
    ])


def link_transforms(pose: dict, js: list[Joint] | None = None) -> dict[str, np.ndarray]:
    """4x4 world transforms (mm) of every link for a pose. Base stays at the origin."""
    js = js or joints()
    T = {"base": np.eye(4)}
    pending = list(js)
    while pending:
        progress = False
        for j in list(pending):
            if j.parent not in T:
                continue
            q = pose.get(j.mimic, 0.0) * j.mimic_coef if j.mimic else pose.get(j.name, 0.0)
            local = np.eye(4)
            if j.kind == "slide":
                local[:3, 3] = np.asarray(j.axis, float) * q * 1000.0
            else:
                R = _rot(j.axis, q)
                a = np.asarray(j.anchor, float)
                local[:3, :3] = R
                local[:3, 3] = a - R @ a
            T[j.child] = T[j.parent] @ local
            pending.remove(j)
            progress = True
        if not progress:
            raise ValueError(f"joint tree is broken at {[j.name for j in pending]}")
    return T
