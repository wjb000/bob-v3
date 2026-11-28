"""Checks for the chore loops. No MuJoCo and no display."""

import numpy as np

from practical import (
    CAD_LIFT_M,
    PUBLISHED_VIEWER_LIFT_M,
    arm_bumped,
    backoff_action,
    column_matches,
    dock_drive,
    docked,
    find_blob,
    grasped,
    locate_on_counter,
    over_current,
    person_ahead,
    ray_to_counter,
    tip_margin,
    track_blob,
)


def test_column():
    assert column_matches(CAD_LIFT_M)
    assert column_matches(PUBLISHED_VIEWER_LIFT_M)


def test_bump_and_grasp():
    assert over_current(0.5)
    assert not over_current(0.2)
    assert arm_bumped([("forearm_a_r", "chair")])
    assert not arm_bumped([("pad_a_r", "cube")])
    assert not arm_bumped([("wheel_l", "floor")])
    a = backoff_action()
    assert a[0] < 0 and a[6] == 1 and a[7] == 0
    assert grasped(2, 0.022)
    assert not grasped(2, 0.0)
    assert not grasped(1, 0.022)


def test_camera():
    rgb = np.zeros((120, 160, 3), np.uint8)
    rgb[50:70, 90:110] = (242, 89, 26)
    uv = find_blob(rgb)
    assert uv is not None and abs(uv[0] - 99.5) < 2 and abs(uv[1] - 59.5) < 2
    # Camera one metre above the origin, looking straight down.
    K = np.array([[100.0, 0, 80.0], [0, 100.0, 60.0], [0, 0, 1]])
    axes = np.column_stack([[1, 0, 0], [0, 1, 0], [0, 0, -1]])
    hit = ray_to_counter((80, 60), K, axes, (0, 0, 1), 0)
    assert np.allclose(hit, 0, atol=1e-6)
    hit = locate_on_counter(rgb, K, axes, (0, 0, 1), 0)
    assert hit is not None and hit[2] == 0 and abs(hit[0]) < 0.3
    pan, tilt = track_blob((159, 0), (160, 120), 0, 0)
    assert pan < 0 and tilt > 0


def test_dock_and_tip():
    hull = np.array([[-0.2, -0.2], [0.2, -0.2], [0.2, 0.2], [-0.2, 0.2]])
    assert tip_margin((0, 0), hull) == 0.2
    assert tip_margin((0.3, 0), hull) < 0
    assert person_ahead([0.2, 3.0], [0.0, 1.5])
    assert not person_ahead([2.0], [0.0])
    v, w = dock_drive(0, 0, 0, [2.0], [0.0], (0, 0), hull)
    assert v < 0  # reverse onto the dock behind the base
    assert dock_drive(0, 0, 0, [0.2], [0.0], (0, 0), hull) == (0.0, 0.0)
    assert dock_drive(0, 0, 0, [2.0], [0.0], (0.3, 0), hull) == (0.0, 0.0)
    assert docked(-0.55, 0.0, 0.0)


if __name__ == "__main__":
    test_column()
    test_bump_and_grasp()
    test_camera()
    test_dock_and_tip()
    print("ok")
