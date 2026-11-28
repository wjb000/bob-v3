"""What the one chore needs, without a desktop GPU.

The physical robot is not built. These are the checks and the loops that have to be
true on the machine, written so they run on the Pi from numbers the robot already has:
servo load, finger touch, the head camera, the base lidar, and the wheel pose.

The public viewer column travels the CAD distance, 0.650 m. column_matches()
is how the page is checked against the CAD.
"""

from __future__ import annotations

import numpy as np

# cad/params.py LIFT_TRAVEL. The published GLB is still the previous column.
CAD_LIFT_M = 0.650
PUBLISHED_VIEWER_LIFT_M = 0.650

# Printed GM-5 teeth. Back off before the servo is asked for a stall.
GEAR_LOAD_LIMIT = 0.45

# 480 mm base. The dock sits behind the robot; he reverses onto it.
BASE_R_M = 0.240
DOCK_X_M = -0.55
DOCK_TOL_M = 0.02
DOCK_Y_TOL_M = 0.04
DOCK_YAW_TOL = 0.08

# A person or a chair inside this forward wedge stops the base.
PERSON_STOP_M = 0.40
PERSON_HALF_RAD = np.deg2rad(30)

# Orange cube in the pick scene, used by the onboard finder.
CUP_RGB = np.array([0.95, 0.35, 0.10])


def column_matches(viewer_lift_m: float, cad_lift_m: float = CAD_LIFT_M, tol: float = 0.01) -> bool:
    """True when the viewer's column travel is the CAD travel."""
    return abs(float(viewer_lift_m) - float(cad_lift_m)) <= tol


def over_current(load_frac: float, limit: float = GEAR_LOAD_LIMIT) -> bool:
    """Servo load register, 0 at rest and 1 at stall."""
    return float(load_frac) >= limit


def arm_bumped(pairs) -> bool:
    """True when the arm hits something that is not the floor, the object, or its own fingers.

    pairs are (geom_a, geom_b) name strings from the contact set.
    """
    hints = ("shoulder", "upper_arm", "forearm", "elbow", "wrist", "palm", "yoke", "link")
    for a, b in pairs:
        names = f"{a} {b}".lower()
        if any(s in names for s in ("floor", "cube", "finger", "pad", "wheel", "caster")):
            continue
        if any(h in names for h in hints):
            return True
    return False


def backoff_action(n_arm: int = 6) -> np.ndarray:
    """Eight-number viewer action: reverse the arm, open the hand, hold the column."""
    a = np.zeros(8)
    a[:n_arm] = -0.6
    a[6] = 1.0
    return a


def grasped(pad_hits: int, opening_m: float, pads: int = 2, empty_close_m: float = 0.002) -> bool:
    """Both pads are on the object, and the jaw stopped before the empty-close stop.

    An empty close reaches opening_m near 0. A cup holds the fingers open, and the
    servo load climbs. pad_hits is how many finger-pad touch sensors are over their threshold.
    """
    return int(pad_hits) >= pads and float(opening_m) > empty_close_m


def find_blob(rgb: np.ndarray, color=CUP_RGB, tol: float = 0.28):
    """Pixel (u, v) of the largest patch close to color, or None. rgb is uint8 or 0..1."""
    img = np.asarray(rgb)
    if img.dtype == np.uint8:
        img = img.astype(np.float32) / 255.0
    if img.ndim != 3 or img.shape[2] < 3:
        return None
    err = np.linalg.norm(img[:, :, :3] - np.asarray(color, float), axis=2)
    mask = err < tol
    if not np.any(mask):
        return None
    ys, xs = np.nonzero(mask)
    return float(xs.mean()), float(ys.mean())


def ray_to_counter(uv, K, cam_axes, cam_pos, counter_z: float):
    """Where the camera ray through pixel uv meets the counter plane.

    cam_axes columns are the camera's right, down, and forward axes in the world.
    Returns the hit point, or None if the ray is parallel to the counter or behind the camera.
    """
    K = np.asarray(K, float)
    x = (uv[0] - K[0, 2]) / K[0, 0]
    y = (uv[1] - K[1, 2]) / K[1, 1]
    d_cam = np.array([x, y, 1.0], float)
    d_cam /= np.linalg.norm(d_cam)
    direction = np.asarray(cam_axes, float) @ d_cam
    direction /= np.linalg.norm(direction)
    if abs(direction[2]) < 1e-6:
        return None
    t = (counter_z - cam_pos[2]) / direction[2]
    if t <= 0:
        return None
    return np.asarray(cam_pos, float) + t * direction


def axes_from_mujoco(xmat) -> np.ndarray:
    """MuJoCo camera matrix (row-major, looks down its -Z, Y up) to right, down, forward columns."""
    R = np.asarray(xmat, float).reshape(3, 3)
    right, up, backward = R[:, 0], R[:, 1], R[:, 2]
    return np.column_stack([right, -up, -backward])


def locate_on_counter(rgb, K, cam_axes, cam_pos, counter_z: float, color=CUP_RGB):
    """Head-camera loop for one object on a counter. None if the colour is not in frame."""
    uv = find_blob(rgb, color)
    if uv is None:
        return None
    return ray_to_counter(uv, K, cam_axes, cam_pos, counter_z)


def track_blob(uv, size, pan: float, tilt: float, gain: float = 0.4):
    """Pan and tilt step that puts the blob on the centre of the head camera."""
    w, h = size
    du = (uv[0] - (w - 1) / 2) / max(w / 2, 1)
    dv = (uv[1] - (h - 1) / 2) / max(h / 2, 1)
    return float(pan - gain * du), float(tilt - gain * dv)


def _inside(p, hull) -> bool:
    """Even-odd test. hull is an (n, 2) loop in order."""
    x, y = p
    n = len(hull)
    c = False
    for i in range(n):
        x0, y0 = hull[i]
        x1, y1 = hull[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xcross = x0 + (y - y0) / (y1 - y0) * (x1 - x0)
            if x < xcross:
                c = not c
    return c


def _edge_distance(com, hull) -> float:
    best = 1e9
    n = len(hull)
    for i in range(n):
        a, b = hull[i], hull[(i + 1) % n]
        ab = b - a
        t = np.clip(np.dot(com - a, ab) / max(np.dot(ab, ab), 1e-12), 0.0, 1.0)
        best = min(best, np.linalg.norm(com - (a + t * ab)))
    return float(best)


def tip_margin(com_xy, hull) -> float:
    """Metres from the CoM to the support polygon. Negative means the base is already tipping."""
    com = np.asarray(com_xy, float)
    hull = np.asarray(hull, float)
    dist = _edge_distance(com, hull)
    return dist if _inside(com, hull) else -dist


def person_ahead(ranges_m, angles_rad, stop_m: float = PERSON_STOP_M, half_rad: float = PERSON_HALF_RAD) -> bool:
    """True if any return in the forward wedge is closer than stop_m. Angle 0 is straight ahead."""
    r = np.asarray(ranges_m, float)
    a = np.asarray(angles_rad, float)
    if r.size == 0:
        return False
    close = (np.abs(a) <= half_rad) & (r > 0.05) & (r < stop_m)
    return bool(np.any(close))


def docked(x: float, y: float, yaw: float, dock_x: float = DOCK_X_M) -> bool:
    return abs(x - dock_x) < DOCK_TOL_M and abs(y) < DOCK_Y_TOL_M and abs(yaw) < DOCK_YAW_TOL


def dock_drive(x, y, yaw, ranges_m, angles_rad, com_xy, hull, dock_x: float = DOCK_X_M):
    """Wheel command (forward m/s, yaw rad/s). Zero if a person is ahead, the base would tip, or he is on the dock.

    Positive forward drives the robot toward +x. The dock is behind him, so the approach is negative forward speed.
    """
    if person_ahead(ranges_m, angles_rad) or tip_margin(com_xy, hull) < 0.04 or docked(x, y, yaw, dock_x):
        return 0.0, 0.0
    # Face the dock, then reverse onto it. Yaw 0 faces +x, so the dock behind him is yaw pi.
    target_yaw = np.arctan2(0.0 - y, dock_x - x)
    # Drive backward along the line to the dock: heading should be target_yaw + pi (nose away from the dock).
    nose = _ang(yaw - (target_yaw + np.pi))
    along = np.hypot(dock_x - x, 0.0 - y)
    v = -0.15 if abs(nose) < 0.4 else 0.0
    if along < 0.08:
        v = -0.05
    w = float(np.clip(-1.2 * nose, -0.6, 0.6))
    return float(v), w


def _ang(a: float) -> float:
    return (a + np.pi) % (2 * np.pi) - np.pi
