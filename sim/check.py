#!/usr/bin/env python3
"""Physics checks for Bob v3. Each test prints a line and a PASS/FAIL.

    .venv/bin/python sim/check.py            # all tests, writes sim/reports/check.json

1 stand     settle at home for 3 s, base must not move or tilt
2 torque    gravity torque at every arm joint, worst pose, 0.5 kg in the hand, vs rated and peak
3 hold      hold 0.5 kg per hand at the furthest pose the interlock allows, modelled actuators
4 lift      raise the torso over its full travel and back, measure time and error
5 brake     drive at 0.6 m/s with the lift up, 0.5 kg per hand in the worst pose the interlock allows, stop at 1-6 m/s^2
6 push      horizontal shove at the head that tips it, same pose
7 slope     steepest ramp it can stand on, same pose
11 interlock reach-limit interlock: blocks reaching out with a load, and push/slope at the worst allowed pose by lift
8 reach     sample the arm workspace without self-collision
9 tasks     IK to a floor object, a 0.91 m counter and a 1.25 m shelf, collision-free
10 pick     scripted pick of a cube off a 0.75 m table, 40 random placements
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent  # works in the repo and in bob-v3-sim.zip
XML = HERE / "bob_v3.xml"
OUT = HERE / "reports"
PAYLOAD = 0.5  # kg
RESULTS = {}

# Worst poses the reach-limit interlock (sim/interlock.py) still allows with a load, from
# tests/envelope_scan.py (random arm poses, ranked by the static nose-down ramp angle).
IL_WORST_LOW = {"shoulder_pitch": -1.63, "shoulder_roll": -0.09, "upper_arm_yaw": 0.39, "elbow": -0.35, "wrist_pitch": 1.54}  # column at the bottom
# Above the bottom the worst allowed pose is the same at every height: hands tucked at the chest.
IL_WORST_TUCK = {"shoulder_pitch": -1.16, "shoulder_roll": 0.38, "upper_arm_yaw": -1.24, "elbow": -1.56, "wrist_pitch": -1.95}
IL_WORST_MID = IL_WORST_TUCK  # lift 0.3 m
IL_WORST_TOP = IL_WORST_TUCK  # top of the lift


def both(pose):
    """The same arm pose on both sides (roll mirrored)."""
    out = {}
    for k, v in pose.items():
        out[f"r_{k}"] = v
        out[f"l_{k}"] = -v if k in ("shoulder_roll", "upper_arm_yaw") else v
    return out


def load():
    m = mujoco.MjModel.from_xml_path(str(XML))
    return m, mujoco.MjData(m)


def key(m, d, name):
    mujoco.mj_resetDataKeyframe(m, d, m.key(name).id)
    mujoco.mj_forward(m, d)


def act(m, name):
    return m.actuator(name).id


def jq(m, d, name):
    return d.qpos[m.jnt_qposadr[m.joint(name).id]]


def tilt_deg(d):
    w, x, y, z = d.qpos[3:7]
    zz = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1, min(1, zz))))


def report(name, ok, **kw):
    RESULTS[name] = dict(ok=bool(ok), **kw)
    extras = "  ".join(f"{k}={v}" for k, v in kw.items() if not isinstance(v, (list, dict)))
    print(f"{'PASS' if ok else 'FAIL'}  {name:8s} {extras}", flush=True)


def add_payload(m, kg):
    for s in ("l", "r"):
        b = m.body(f"{s}_link6").id
        tcp = m.site(f"tcp_{s}").id
        m0 = m.body_mass[b]
        c0 = m.body_ipos[b].copy()
        p = m.site_pos[tcp]
        m.body_mass[b] = m0 + kg
        m.body_ipos[b] = (m0 * c0 + kg * p) / (m0 + kg)
    # Recompute the derived constants (subtree masses), or subtree_com ignores the payload.
    mujoco.mj_setConst(m, mujoco.MjData(m))


# ---------------------------------------------------------------- 1 stand

def test_stand():
    m, d = load()
    key(m, d, "home")
    p0 = d.qpos[:3].copy()
    for _ in range(int(3.0 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    drift = float(np.linalg.norm(d.qpos[:2] - p0[:2]) * 1000)
    err = max(abs(jq(m, d, m.joint(m.actuator_trnid[i, 0]).name) - d.ctrl[i]) for i in range(m.nu)
              if not m.actuator(i).name.startswith("wheel"))
    t = tilt_deg(d)
    report("stand", drift < 5 and t < 1.5 and err < 0.03, drift_mm=round(drift, 2), tilt_deg=round(t, 2),
           max_track_err=round(float(err), 4))


# ---------------------------------------------------------------- 2 torque

ARM_J = ["shoulder_pitch", "shoulder_roll", "upper_arm_yaw", "elbow", "wrist_pitch", "wrist_roll", "gripper"]
RATING = {"shoulder_pitch": (2.21, 9.32), "shoulder_roll": (2.21, 9.32), "upper_arm_yaw": (1.57, 4.9), "elbow": (2.21, 9.32),
          "wrist_pitch": (1.57, 4.9), "wrist_roll": (0.98, 2.94), "gripper": (0.98, 2.94)}


def gravity_torques(m, d, pose):
    key(m, d, "home")
    for k, v in pose.items():
        d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
    d.qvel[:] = 0
    d.qacc[:] = 0
    mujoco.mj_inverse(m, d)
    return {j: float(d.qfrc_inverse[m.jnt_dofadr[m.joint(j).id]]) for j in (f"l_{n}" for n in ARM_J if n != "gripper")}


def test_torque():
    m, d = load()
    add_payload(m, PAYLOAD)
    poses = {
        "arm forward": {"lift": 0.4, "l_shoulder_pitch": -1.5708, "l_elbow": 0.0, "l_wrist_pitch": 0.0},
        "arm sideways": {"lift": 0.4, "l_shoulder_roll": 1.5708, "l_elbow": 0.0},
        "forearm out": {"lift": 0.4, "l_shoulder_pitch": 0.0, "l_elbow": -1.5708, "l_wrist_pitch": 0.0},
        "wrist out": {"lift": 0.4, "l_shoulder_pitch": 0.0, "l_elbow": -1.5708, "l_wrist_pitch": -1.5708 * 0 + 0.0},
        "yaw loaded": {"lift": 0.4, "l_shoulder_pitch": -1.5708, "l_upper_arm_yaw": 1.5708, "l_elbow": -1.5708},
    }
    worst = {j: 0.0 for j in ARM_J if j != "gripper"}
    table = {}
    for pname, pose in poses.items():
        tau = gravity_torques(m, d, pose)
        table[pname] = {k[2:]: round(v, 2) for k, v in tau.items()}
        for k, v in tau.items():
            worst[k[2:]] = max(worst[k[2:]], abs(v))
    rows = []
    ok = True
    for j in worst:
        rated, peak = RATING[j]
        r = worst[j] / rated
        rows.append(dict(joint=j, worst_Nm=round(worst[j], 2), rated_Nm=rated, peak_Nm=peak, of_rated=round(r, 2),
                         of_peak=round(worst[j] / peak, 2)))
        ok &= worst[j] <= peak * 0.8
    for r in rows:
        print(f"        {r['joint']:15s} {r['worst_Nm']:6.2f} N·m  rated {r['rated_Nm']:5.2f}  peak {r['peak_Nm']:5.2f}"
              f"  {100 * r['of_rated']:5.0f}% of rated  {100 * r['of_peak']:4.0f}% of peak")
    report("torque", ok, payload_kg=PAYLOAD, rows=rows, poses=table)


# ---------------------------------------------------------------- 3 hold

def test_hold():
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    targets = {"lift": 0.0, **both(IL_WORST_LOW)}
    for k, v in targets.items():
        d.ctrl[act(m, k)] = v
    for _ in range(int(4.0 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    errs = {k: round(math.degrees(abs(jq(m, d, k) - v)), 2) for k, v in targets.items() if k != "lift"}
    sat = {m.actuator(i).name: round(float(d.actuator_force[i]), 2) for i in range(m.nu)
           if abs(d.actuator_force[i]) >= 0.99 * m.actuator_forcerange[i, 1] and not m.actuator(i).name.startswith("wheel")}
    t = tilt_deg(d)
    worst = max(errs.values())
    report("hold", worst < 3.0 and not sat and t < 3, worst_err_deg=worst, tilt_deg=round(t, 2), saturated=sat, errors=errs)


# ---------------------------------------------------------------- 4 lift

LIFT_SPEED = 0.025  # m/s: NEMA 17 at 750 rpm on a 2 mm lead. The controller ramps the target at this rate.
DRIVE_ACCEL = 1.0  # m/s^2, the base controller's ramp
WHEEL_R = 0.05035


def ramp_lift(m, d, a, target, dt):
    cur = d.ctrl[a]
    step = LIFT_SPEED * dt
    d.ctrl[a] = cur + max(-step, min(step, target - cur))


def test_lift():
    """Hands tucked at the chest (allowed by the reach limit at every height with a load), 0.5 kg in each hand: run the column bottom -> top -> bottom at the screw speed.

    Checks the torso tracks the ramp, the middle and upper tubes stay at 1/3 and 2/3 of the
    lift (the GT2 cascades), nothing but the wheels and casters touches anything, and the
    base does not rock.
    """
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    for k, v in both(IL_WORST_TOP).items():
        d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
        d.ctrl[act(m, k)] = v
    a = act(m, "lift")
    lo, hi = m.actuator_ctrlrange[a]
    jl, jm, ju = (m.jnt_qposadr[m.joint(n).id] for n in ("lift", "lift_mid", "lift_upper"))
    # start at the bottom, settled
    d.qpos[jl], d.qpos[jm], d.qpos[ju] = lo, lo / 3, 2 * lo / 3
    d.ctrl[a] = lo
    mujoco.mj_forward(m, d)
    for _ in range(int(1.0 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    t_up = t_down = None
    worst_lag = worst_stage = worst_pen = max_tilt = 0.0
    touching = set()
    leg, t0, err_up, f_top = "up", d.time, None, None
    for _ in range(int(60.0 / m.opt.timestep)):
        ramp_lift(m, d, a, hi if leg == "up" else lo, m.opt.timestep)
        mujoco.mj_step(m, d)
        L = d.qpos[jl]
        worst_lag = max(worst_lag, abs(d.ctrl[a] - L))
        worst_stage = max(worst_stage, abs(d.qpos[jm] - L / 3), abs(d.qpos[ju] - 2 * L / 3))
        max_tilt = max(max_tilt, tilt_deg(d))
        for c in d.contact[:d.ncon]:
            n1, n2 = m.geom(c.geom1).name, m.geom(c.geom2).name
            if "floor" in (n1, n2):
                continue
            touching.add(f"{m.body(m.geom_bodyid[c.geom1]).name}|{m.body(m.geom_bodyid[c.geom2]).name}")
            worst_pen = max(worst_pen, -c.dist)
        if leg == "up" and L > hi - 0.002 and d.ctrl[a] >= hi:
            t_up = d.time - t0
            for _ in range(int(1.0 / m.opt.timestep)):  # hold at the top
                mujoco.mj_step(m, d)
            err_up = abs(d.qpos[jl] - hi) * 1000
            f_top = float(d.actuator_force[a])
            leg, t0 = "down", d.time
        elif leg == "down" and L < lo + 0.002 and d.ctrl[a] <= lo:
            t_down = d.time - t0
            break
    err_down = abs(d.qpos[jl] - lo) * 1000
    ok = (t_up is not None and t_down is not None and err_up < 2.0 and err_down < 2.0 and worst_stage < 0.002
          and not touching and max_tilt < 1.0 and abs(f_top) < m.actuator_forcerange[a, 1] * 0.9)
    report("lift", ok, travel_mm=round((hi - lo) * 1000), speed_mm_s=LIFT_SPEED * 1000, time_s=round(t_up or -1, 1),
           down_time_s=round(t_down or -1, 1), worst_lag_mm=round(worst_lag * 1000, 2), hold_err_mm=round(err_up or -1, 2),
           bottom_err_mm=round(err_down, 2), hold_force_N=round(f_top or 0, 1), stage_err_mm=round(worst_stage * 1000, 2),
           base_tilt_deg=round(max_tilt, 3), contacts=sorted(touching), penetration_mm=round(worst_pen * 1000, 2))


# ---------------------------------------------------------------- 5 brake

def torso_up(m):
    """Top of the lift, 0.5 kg per hand, the worst arm pose the interlock allows up there."""
    hi = float(m.jnt_range[m.joint("lift").id][1])
    return {"lift": hi, **both(IL_WORST_TOP)}


def _drive(decel, v=0.6):
    """Raise the torso, arms out, drive at v with the ramp, then stop at `decel`. Returns max tilt and top speed."""
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    up = torso_up(m)
    for k, val in up.items():
        d.ctrl[act(m, k)] = val
    for _ in range(int(3.0 / m.opt.timestep)):
        mujoco.mj_step(m, d)
    wl, wr = act(m, "wheel_l"), act(m, "wheel_r")
    dt = m.opt.timestep
    cmd, max_tilt, top = 0.0, 0.0, 0.0
    for _ in range(int((v / DRIVE_ACCEL + 1.5) / dt)):
        cmd = min(v, cmd + DRIVE_ACCEL * dt)
        d.ctrl[wl] = d.ctrl[wr] = cmd / WHEEL_R
        mujoco.mj_step(m, d)
        max_tilt = max(max_tilt, tilt_deg(d))
        top = max(top, float(d.qvel[0]))
    for _ in range(int((v / decel + 2.0) / dt)):
        cmd = max(0.0, cmd - decel * dt)
        d.ctrl[wl] = d.ctrl[wr] = cmd / WHEEL_R
        mujoco.mj_step(m, d)
        max_tilt = max(max_tilt, tilt_deg(d))
    return max_tilt, top


def test_brake():
    rows = {}
    for dec in (1.0, 2.0, 4.0, 6.0):
        t, top = _drive(dec)
        rows[str(dec)] = round(t, 2)
    worst = max(rows.values())
    report("brake", worst < 5.0 and top > 0.55, speed_mps=round(top, 2), max_tilt_deg=worst, tilt_by_decel=rows)


def test_push():
    """Torso up, 0.5 kg per hand, worst allowed pose: the horizontal force at the head that starts a tip, front and back."""
    out = _push()
    report("push", min(out.values()) >= 25, **out)


def _push():
    out = {}
    for sign, name in ((1, "push_forward_N"), (-1, "push_back_N")):
        lo, hi = 0.0, 300.0
        for _ in range(9):
            f = (lo + hi) / 2
            m, d = load()
            add_payload(m, PAYLOAD)
            key(m, d, "home")
            up = torso_up(m)
            for k, v in up.items():
                d.ctrl[act(m, k)] = v
                d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
            L = up.get("lift", 0.0)
            d.qpos[m.jnt_qposadr[m.joint("lift_mid").id]] = L / 3
            d.qpos[m.jnt_qposadr[m.joint("lift_upper").id]] = 2 * L / 3
            for _ in range(int(1.0 / m.opt.timestep)):
                mujoco.mj_step(m, d)
            hb = m.body("head_tilt").id
            tip = False
            for _ in range(int(2.0 / m.opt.timestep)):
                d.xfrc_applied[hb, 0] = sign * f
                mujoco.mj_step(m, d)
                if tilt_deg(d) > 12:
                    tip = True
                    break
            lo, hi = (lo, f) if tip else (f, hi)
        out[name] = round(lo, 1)
    return out


def test_slope():
    """Static: the steepest ramp the robot stands on (worst pose), from the CoM and the contact points."""
    ang, com = _slope()
    report("slope", min(ang.values()) > 10, com_m=com, **ang)


def _slope():
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    up = torso_up(m)
    for k, v in up.items():
        d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
    d.qpos[m.jnt_qposadr[m.joint("lift_mid").id]] = up["lift"] / 3
    d.qpos[m.jnt_qposadr[m.joint("lift_upper").id]] = 2 * up["lift"] / 3
    mujoco.mj_forward(m, d)
    com = d.subtree_com[m.body("base").id]
    fx = m.geom_pos[m.geom("caster_front").id][0]
    rx = m.geom_pos[m.geom("caster_rear").id][0]
    side = abs(m.body_pos[m.body("wheel_l").id][1])
    ang = dict(down_deg=round(math.degrees(math.atan2(fx - com[0], com[2])), 1),
               up_deg=round(math.degrees(math.atan2(com[0] - rx, com[2])), 1),
               side_deg=round(math.degrees(math.atan2(side - abs(com[1]), com[2])), 1))
    return ang, [round(float(v), 3) for v in com]


def _support_polygon(m, d):
    """Floor contact points (x, y) of the two tires and two casters, counter-clockwise."""
    pts = []
    for c in d.contact[:d.ncon]:
        n1, n2 = m.geom(c.geom1).name, m.geom(c.geom2).name
        if "floor" in (n1, n2):
            pts.append((float(c.pos[0]), float(c.pos[1])))
    P_ = np.array(pts)
    c0 = P_.mean(axis=0)
    ang = np.arctan2(P_[:, 1] - c0[1], P_[:, 0] - c0[0])
    return P_[np.argsort(ang)]


def _margin(poly, com_xy):
    """Smallest distance from the CoM to any edge of the convex hull of the contacts (mm), and its edge."""
    import itertools
    pts = poly
    best = None
    n = len(pts)
    # convex hull edges: an edge (i, j) where every other point is on one side
    for i, j in itertools.combinations(range(n), 2):
        a, b = pts[i], pts[j]
        e = b - a
        L = float(np.hypot(*e))
        if L < 1e-6:
            continue
        side = [(e[0] * (p_[1] - a[1]) - e[1] * (p_[0] - a[0])) for k, p_ in enumerate(pts) if k not in (i, j)]
        if not (all(s >= -1e-9 for s in side) or all(s <= 1e-9 for s in side)):
            continue
        s_com = e[0] * (com_xy[1] - a[1]) - e[1] * (com_xy[0] - a[0])
        inside_sign = np.sign(sum(side)) if side else 1.0
        dist = s_com / L * inside_sign
        if best is None or dist < best:
            best = dist
    return best * 1000


def test_tip():
    """Static tip margin in the poses that load it most, 0.5 kg in each hand, after a 3 s settle.

    Margin is the shortest distance from the ground projection of the CoM to an edge of the
    contact polygon (two tires, two casters). Positive is inside. Tilt is the settled base tilt.
    """
    hi = None
    rows = {}
    for name, pose in (
        ("lift up, worst pose the interlock allows", {"lift": "hi", **IL_WORST_TOP}),
        ("lift mid, worst pose the interlock allows", {"lift": 0.3, **IL_WORST_MID}),
        ("lift down, worst pose the interlock allows", {"lift": 0.0, **IL_WORST_LOW}),
        ("lift down, floor pick", {"lift": 0.0, "shoulder_pitch": -0.805, "elbow": 0.0, "wrist_pitch": 0.0}),
    ):
        m, d = load()
        add_payload(m, PAYLOAD)
        key(m, d, "home")
        hi = float(m.jnt_range[m.joint("lift").id][1])
        tgt = {}
        for k, v in pose.items():
            v = hi if v == "hi" else v
            if k == "lift":
                tgt["lift"] = v
            else:
                for s in ("l", "r"):
                    tgt[f"{s}_{k}"] = -v if s == "l" and k in ("shoulder_roll", "upper_arm_yaw") else v
        for k, v in tgt.items():
            d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
            d.ctrl[act(m, k)] = v
        L = tgt.get("lift", jq(m, d, "lift"))
        d.qpos[m.jnt_qposadr[m.joint("lift_mid").id]] = L / 3
        d.qpos[m.jnt_qposadr[m.joint("lift_upper").id]] = 2 * L / 3
        mujoco.mj_forward(m, d)
        for _ in range(int(3.0 / m.opt.timestep)):
            mujoco.mj_step(m, d)
        com = d.subtree_com[m.body("base").id].copy()
        # include the payload bodies (children of the hands, so already in the base subtree)
        poly = _support_polygon(m, d)
        rows[name] = dict(com_mm=[round(float(v) * 1000, 1) for v in com], margin_mm=round(_margin(poly, com[:2]), 1),
                          tilt_deg=round(tilt_deg(d), 2))
    ok = all(r["margin_mm"] > 20 and r["tilt_deg"] < 1.0 for r in rows.values())
    report("tip", ok, poses=rows, worst_margin_mm=min(r["margin_mm"] for r in rows.values()))


# ---------------------------------------------------------------- 6 reach

def test_reach(n=6000, seed=0):
    m, d = load()
    rng = np.random.default_rng(seed)
    key(m, d, "home")
    names = [f"r_{j}" for j in ARM_J[:-1]]
    adr = [m.jnt_qposadr[m.joint(n_).id] for n_ in names]
    rng_lo = np.array([m.jnt_range[m.joint(n_).id][0] for n_ in names])
    rng_hi = np.array([m.jnt_range[m.joint(n_).id][1] for n_ in names])
    tcp = m.site("tcp_r").id
    lift_adr = m.jnt_qposadr[m.joint("lift").id]
    lift_hi = m.jnt_range[m.joint("lift").id][1]
    pts = []
    nose = 0.205  # front face of the base (cad/params.py BASE_L / 2 + BASE_CX)
    for i in range(n):
        key(m, d, "home")
        d.qpos[lift_adr] = rng.uniform(0, lift_hi)
        d.qpos[adr] = rng.uniform(rng_lo, rng_hi)
        mujoco.mj_forward(m, d)
        if any(m.geom(c.geom1).name != "floor" and m.geom(c.geom2).name != "floor" for c in d.contact[:d.ncon]):
            continue
        p = d.site_xpos[tcp].copy()
        if p[2] < 0.01:
            continue
        pts.append(p)
    # Arms-up overhead. Random samples rarely hit this pose, and it is the shelf reach.
    key(m, d, "home")
    d.qpos[lift_adr] = lift_hi
    overhead = {"shoulder_pitch": -3.00, "shoulder_roll": 0.0, "upper_arm_yaw": 0.0,
                "elbow": -0.20, "wrist_pitch": 0.0, "wrist_roll": 0.0}
    for n_, v in overhead.items():
        d.qpos[m.jnt_qposadr[m.joint(f"r_{n_}").id]] = v
    mujoco.mj_forward(m, d)
    pts.append(d.site_xpos[tcp].copy())
    P = np.array(pts)
    front = P[P[:, 0] > nose + 0.03]
    floor = front[front[:, 2] < 0.08]
    counter = front[(front[:, 2] > 0.88) & (front[:, 2] < 0.95)]
    out = dict(samples=n, valid=len(P), z_max_m=round(float(P[:, 2].max()), 3),
               floor_reach_x_m=round(float(floor[:, 0].max()), 3) if len(floor) else None,
               lowest_in_front_m=round(float(front[:, 2].min()), 3),
               counter_reach_x_m=round(float(counter[:, 0].max()), 3) if len(counter) else None,
               side_reach_y_m=round(float(-P[:, 1].min()), 3))
    ok = len(floor) > 0 and len(counter) > 0 and out["z_max_m"] > 1.45
    report("reach", ok, **out)
    np.save(OUT / "reach_r.npy", P)


# ---------------------------------------------------------------- 9 tasks

def test_tasks():
    """IK to real household targets, no self-collision: floor, counter, top shelf (the shorter column tops out near 1.5 m)."""
    sys.path.insert(0, str(HERE))
    import bob_env
    import expert
    m, d = load()
    key(m, d, "home")
    ik = bob_env.Ik(m, "r")
    lq = m.jnt_qposadr[m.joint("lift").id]
    seeds = [d.qpos.copy()]
    q2 = d.qpos.copy()
    q2[ik.qadr] = [-1.0, 0, 0, -0.6, 1.2, 0]
    seeds.append(q2)
    q3 = d.qpos.copy()
    q3[ik.qadr] = [-2.2, 0, 0, -0.3, 0.8, 0]
    seeds.append(q3)
    q4 = d.qpos.copy()
    q4[lq] = 0.0
    q4[ik.qadr] = [-0.805, 0.0, 0.0, 0.0, 0.0, 0.0]
    seeds.append(q4)
    targets = {"floor, in front of the nose": [0.420, -0.157, 0.016],
               "kitchen counter 0.91 m": [0.55, -0.2, 0.93],
               "top shelf 1.25 m": [0.30, -0.2, 1.25],
               "own charge socket, base top": [0.150, -0.125, 0.265]}
    l_adr = np.array([m.jnt_qposadr[m.joint(f"l_{n}").id] for n in
                      ("shoulder_pitch", "shoulder_roll", "upper_arm_yaw", "elbow", "wrist_pitch", "wrist_roll")])
    found = {}
    for name, t in targets.items():
        found[name] = None
        lift_hi = float(m.jnt_range[m.joint("lift").id][1])
        for lift in np.arange(0.0, lift_hi + 1e-9, 0.05):
            for tilt in (0.0, 0.35, 0.7, 0.8, 1.0, 1.4):
                for sd in seeds:
                    q0 = sd.copy()
                    q0[lq] = lift
                    sol, ok = ik.solve(q0, np.array(t), expert._tilt(tilt))
                    if not ok:
                        continue
                    # The square base is wider beside the shoulders than the old disc.
                    # A hanging other arm clips it, so the reach is checked with both arms in the same pose.
                    for mirror in (False, True):
                        dd = mujoco.MjData(m)
                        dd.qpos[:] = q0
                        dd.qpos[ik.qadr] = sol
                        if mirror:
                            dd.qpos[l_adr] = sol
                        mujoco.mj_forward(m, dd)
                        if not any("floor" not in m.geom(c.geom1).name + m.geom(c.geom2).name for c in dd.contact[:dd.ncon]):
                            found[name] = dict(lift_m=round(float(lift), 2), hand_tilt_rad=tilt)
                            break
                    if found[name]:
                        break
                if found[name]:
                    break
            if found[name]:
                break
    for k, v in found.items():
        print(f"        {k:36s} {'reached ' + str(v) if v else 'NOT reached'}")
    report("tasks", all(found.values()), targets=found)


def test_pick(n=40):
    sys.path.insert(0, str(HERE))
    import bob_env
    import expert
    env = bob_env.BobV3Env("pick", max_steps=400)
    ok = [expert.run_episode(env, seed=1000 + i)[0] for i in range(n)]
    rate = float(np.mean(ok))
    report("pick", rate >= 0.85, episodes=n, success_rate=round(rate, 3))


# ---------------------------------------------------------------- 11 interlock

def test_interlock():
    """The reach-limit interlock blocks reaching out with a load, and how stable the worst allowed pose is.

    Targets: 25 N shove at the head front and back, 20 degree nose-down ramp, 0.5 kg per hand.
    """
    sys.path.insert(0, str(HERE))
    import interlock as IL
    m, d = load()
    il = IL.Interlock(m)
    key(m, d, "home")
    lq = m.jnt_qposadr[m.joint("lift").id]
    hi = float(m.jnt_range[m.joint("lift").id][1])

    def q_of(lift, pose):
        q = d.qpos.copy()
        q[lq] = lift
        for k, v in both(pose).items():
            q[m.jnt_qposadr[m.joint(k).id]] = v
        return q

    straight = {"shoulder_pitch": -1.57, "elbow": 0.0, "wrist_pitch": 0.0}
    blocked = {}
    for lift, start in ((0.0, IL_WORST_LOW), (0.3, IL_WORST_MID), (hi, IL_WORST_TOP)):
        q0, q1 = q_of(lift, start), q_of(lift, straight)
        il.grasp_x = None
        qc, hit = il.clamp(q0, q1, loaded=True)
        x = max(p[0] for p, _ in il.hands(qc).values())
        free, _ = il.clamp(q0, q1, loaded=False)
        blocked[f"{lift:.2f}"] = dict(blocked=bool(hit), hand_x_m=round(float(x), 3),
                                      unloaded_x_m=round(float(max(p[0] for p, _ in il.hands(free).values())), 3))
    allowed = {n: il.ok(q_of(L, p), True) for n, L, p in (("low", 0.0, IL_WORST_LOW), ("mid", 0.3, IL_WORST_MID), ("top", hi, IL_WORST_TOP))}
    global torso_up
    keep = torso_up
    rows = {}
    try:
        for lift, pose in ((0.0, IL_WORST_LOW), (0.3, IL_WORST_MID), (hi, IL_WORST_TOP)):
            torso_up = lambda m_, L=lift, P_=pose: {"lift": L, **both(P_)}  # noqa: E731
            push = _push()
            ang, com = _slope()
            rows[f"{lift:.3f}"] = dict(**push, down_deg=ang["down_deg"], up_deg=ang["up_deg"],
                                       meets=bool(min(push.values()) >= 25 and ang["down_deg"] >= 20))
    finally:
        torso_up = keep
    for k, r in rows.items():
        print(f"        lift {k} m  {r}")
    ok = all(b["blocked"] for b in blocked.values()) and all(allowed.values())
    report("interlock", ok and all(r["meets"] for r in rows.values()), blocks_reach=blocked, worst_poses_allowed=allowed,
           stability_by_lift=rows, limits=dict(lift_free_m=IL.LIFT_FREE_M, x_cap_low_m=IL.X_CAP_LOW_M,
                                               x_cap_high_m=IL.X_CAP_HIGH_M, x_rear_m=IL.X_REAR_M,
                                               z_below_shoulder_high_m=-IL.Z_CAP_HIGH_M))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tests = [test_stand, test_torque, test_hold, test_lift, test_tip, test_brake, test_push, test_slope, test_reach, test_tasks, test_pick, test_interlock]
    only = sys.argv[1:]
    try:
        for t in tests:
            if only and t.__name__[5:] not in only:
                continue
            t()
    finally:
        if RESULTS:
            (OUT / "check.json").write_text(json.dumps(RESULTS, indent=1) + "\n")
    bad = [k for k, v in RESULTS.items() if not v["ok"]]
    print("all passed" if not bad else f"failed: {', '.join(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
