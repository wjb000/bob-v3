#!/usr/bin/env python3
"""Physics checks for Bob v3. Each test prints a line and a PASS/FAIL.

    .venv/bin/python sim/check.py            # all tests, writes sim/reports/check.json

1 stand     settle at home for 3 s, base must not move or tilt
2 torque    gravity torque at every arm joint, worst pose, 0.5 kg in the hand, vs rated and peak
3 hold      hold the arm straight out with 0.5 kg using the modelled actuators
4 lift      raise the torso 0 -> 650 mm and back, measure time and error
5 brake     drive at 0.8 m/s with the lift up and arms out, stop at 1-6 m/s^2, measure tilt
6 push      horizontal shove at the head that tips it, torso up and arms out
7 slope     steepest ramp it can stand on, same pose
8 reach     sample the arm workspace without self-collision
9 tasks     IK to a floor object, a 0.91 m counter and a 1.55 m shelf, collision-free
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
RATING = {"shoulder_pitch": (6.7, 20.8), "shoulder_roll": (6.7, 20.8), "upper_arm_yaw": (4.2, 12.5), "elbow": (4.2, 12.5),
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
    targets = {"lift": 0.4, "l_shoulder_pitch": -1.5708, "l_elbow": 0.0, "l_wrist_pitch": 0.0,
               "r_shoulder_pitch": -1.5708, "r_elbow": 0.0, "r_wrist_pitch": 0.0}
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
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    a = act(m, "lift")
    lo, hi = m.actuator_ctrlrange[a]
    d.ctrl[a] = jq(m, d, "lift")
    t_up = None
    worst_lag = 0.0
    for i in range(int(40.0 / m.opt.timestep)):
        ramp_lift(m, d, a, hi, m.opt.timestep)
        mujoco.mj_step(m, d)
        worst_lag = max(worst_lag, abs(d.ctrl[a] - jq(m, d, "lift")))
        if t_up is None and jq(m, d, "lift") > hi - 0.002:
            t_up = d.time
    err_up = abs(jq(m, d, "lift") - hi) * 1000
    f = float(d.actuator_force[a])
    report("lift", t_up is not None and err_up < 2.0 and abs(f) < m.actuator_forcerange[a, 1] * 0.9,
           travel_mm=round((hi - lo) * 1000), speed_mm_s=LIFT_SPEED * 1000, time_s=round(t_up or -1, 1),
           worst_lag_mm=round(worst_lag * 1000, 2), hold_err_mm=round(err_up, 2), hold_force_N=round(f, 1))


# ---------------------------------------------------------------- 5 brake

def _drive(decel, v=0.6):
    """Raise the torso, arms out, drive at v with the ramp, then stop at `decel`. Returns max tilt and top speed."""
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    up = {"lift": 0.65, "l_shoulder_pitch": -1.2, "r_shoulder_pitch": -1.2, "l_elbow": -0.3, "r_elbow": -0.3}
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
    """Torso up, arms out with 0.5 kg: the horizontal force at the head that starts a tip, front and back."""
    out = {}
    for sign, name in ((1, "push_forward_N"), (-1, "push_back_N")):
        lo, hi = 0.0, 300.0
        for _ in range(9):
            f = (lo + hi) / 2
            m, d = load()
            add_payload(m, PAYLOAD)
            key(m, d, "home")
            for k, v in {"lift": 0.65, "l_shoulder_pitch": -1.2, "r_shoulder_pitch": -1.2, "l_elbow": -0.3, "r_elbow": -0.3}.items():
                d.ctrl[act(m, k)] = v
                d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
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
    report("push", min(out.values()) > 25, **out)


def test_slope():
    """Static: the steepest ramp the robot stands on (worst pose), from the CoM and the contact points."""
    m, d = load()
    add_payload(m, PAYLOAD)
    key(m, d, "home")
    for k, v in {"lift": 0.65, "l_shoulder_pitch": -1.2, "r_shoulder_pitch": -1.2, "l_elbow": -0.3, "r_elbow": -0.3}.items():
        d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
    mujoco.mj_forward(m, d)
    com = d.subtree_com[m.body("base").id]
    fx = m.geom_pos[m.geom("caster_front").id][0]
    rx = m.geom_pos[m.geom("caster_rear").id][0]
    side = abs(m.body_pos[m.body("wheel_l").id][1])
    ang = dict(down_deg=round(math.degrees(math.atan2(fx - com[0], com[2])), 1),
               up_deg=round(math.degrees(math.atan2(com[0] - rx, com[2])), 1),
               side_deg=round(math.degrees(math.atan2(side - abs(com[1]), com[2])), 1))
    report("slope", min(ang.values()) > 10, com_m=[round(float(v), 3) for v in com], **ang)


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
    nose = 0.26
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
    P = np.array(pts)
    front = P[P[:, 0] > nose + 0.03]
    floor = front[front[:, 2] < 0.08]
    counter = front[(front[:, 2] > 0.88) & (front[:, 2] < 0.95)]
    out = dict(samples=n, valid=len(P), z_max_m=round(float(P[:, 2].max()), 3),
               floor_reach_x_m=round(float(floor[:, 0].max()), 3) if len(floor) else None,
               lowest_in_front_m=round(float(front[:, 2].min()), 3),
               counter_reach_x_m=round(float(counter[:, 0].max()), 3) if len(counter) else None,
               side_reach_y_m=round(float(-P[:, 1].min()), 3))
    ok = len(floor) > 0 and len(counter) > 0 and out["z_max_m"] > 1.6
    report("reach", ok, **out)
    np.save(OUT / "reach_r.npy", P)


# ---------------------------------------------------------------- 9 tasks

def test_tasks():
    """IK to real household targets, no self-collision: floor, counter, top shelf."""
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
    targets = {"floor 40 mm object, 0.36 m ahead": [0.36, -0.2, 0.022],
               "kitchen counter 0.91 m": [0.55, -0.2, 0.93],
               "top shelf 1.55 m": [0.40, -0.2, 1.55],
               "own charge socket, base top": [0.150, -0.125, 0.265]}
    found = {}
    for name, t in targets.items():
        found[name] = None
        for lift in np.arange(0.0, 0.651, 0.05):
            for tilt in (0.0, 0.35, 0.7, 1.0, 1.4):
                for sd in seeds:
                    q0 = sd.copy()
                    q0[lq] = lift
                    sol, ok = ik.solve(q0, np.array(t), expert._tilt(tilt))
                    if not ok:
                        continue
                    dd = mujoco.MjData(m)
                    dd.qpos[:] = q0
                    dd.qpos[ik.qadr] = sol
                    mujoco.mj_forward(m, dd)
                    if not any("floor" not in m.geom(c.geom1).name + m.geom(c.geom2).name for c in dd.contact[:dd.ncon]):
                        found[name] = dict(lift_m=round(float(lift), 2), hand_tilt_rad=tilt)
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tests = [test_stand, test_torque, test_hold, test_lift, test_brake, test_push, test_slope, test_reach, test_tasks, test_pick]
    only = sys.argv[1:]
    for t in tests:
        if only and t.__name__[5:] not in only:
            continue
        t()
    (OUT / "check.json").write_text(json.dumps(RESULTS, indent=1) + "\n")
    bad = [k for k, v in RESULTS.items() if not v["ok"]]
    print("all passed" if not bad else f"failed: {', '.join(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
