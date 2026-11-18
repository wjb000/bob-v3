#!/usr/bin/env python3
"""Record Bob v3's simulated tasks for the web viewer.

    .venv/bin/python sim/tools/viewer_tasks.py docs/sim_tasks.json

Every task runs in MuJoCo with the same model, actuator limits and speed limits as sim/check.py.
Each frame stores the joint values, the base pose, object poses and any applied force, at 25 Hz.
The 'result' line for each task is measured from the run, not written by hand.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import bob_env  # noqa: E402
import expert as E  # noqa: E402

DT = 0.04
LIFT_SPEED = 0.025
JOINT_NAMES = None


# ---------------------------------------------------------------- scene and recording helpers

def scene(table=False, shelf=False, cubes=()):
    parts = []
    if table:
        parts.append("""
    <body name="table" pos="0.62 0 0">
      <geom type="box" size="0.30 0.45 0.02" pos="0 0 0.73" rgba="0.62 0.47 0.33 1" contype="8" conaffinity="15"/>
    </body>""")
    if shelf:
        parts.append("""
    <body name="shelf" pos="0.56 -0.2 0">
      <geom type="box" size="0.14 0.25 0.012" pos="0 0 1.49" rgba="0.62 0.47 0.33 1" contype="8" conaffinity="15"/>
    </body>""")
    for i, (x, y, z) in enumerate(cubes):
        parts.append(f"""
    <body name="cube{i}" pos="{x} {y} {z}">
      <freejoint/>
      <geom name="cube{i}" type="box" size="0.0225 0.0225 0.0225" mass="0.08" rgba="0.95 0.35 0.1 1"
            contype="8" conaffinity="15" friction="1.0 0.01 0.001" condim="4"/>
    </body>""")
    xml = f'<mujoco model="bob_task">\n  <include file="bob_v3.xml"/>\n  <worldbody>{"".join(parts)}\n  </worldbody>\n</mujoco>\n'
    path = HERE / "scene_task.xml"
    path.write_text(xml)
    m = mujoco.MjModel.from_xml_path(str(path))
    return m, mujoco.MjData(m)


def joint_names(m):
    return [m.joint(j).name for j in range(m.njnt)
            if m.jnt_type[j] in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE) and not m.joint(j).name.startswith("wheel")]


class Rec:
    """Steps the sim and samples a frame every DT."""

    def __init__(self, m, d, payload_boxes=False):
        self.m, self.d = m, d
        self.frames = []
        self.names = joint_names(m)
        self.cubes = [b for b in range(m.nbody) if m.body(b).name.startswith("cube")]
        self.force = None
        self.payload = payload_boxes
        self.nsub = int(round(DT / m.opt.timestep))

    def snap(self):
        m, d = self.m, self.d
        f = {"q": {n: round(float(d.qpos[m.jnt_qposadr[m.joint(n).id]]), 4) for n in self.names},
             "base": [round(float(v), 4) for v in (*(d.qpos[:3] * 1000), *d.qpos[3:7])]}
        objs = []
        for b in self.cubes:
            objs.append([round(float(v), 4) for v in (*(d.xpos[b] * 1000), *d.xquat[b])])
        if self.payload:
            for s in ("l", "r"):
                sid = m.site(f"tcp_{s}").id
                q = np.zeros(4)
                mujoco.mju_mat2Quat(q, d.site_xmat[sid])
                objs.append([round(float(v), 4) for v in (*(d.site_xpos[sid] * 1000), *q)])
        f["objs"] = objs
        if self.force:
            f["force"] = self.force
        self.frames.append(f)

    def run(self, seconds, before_step=None):
        for _ in range(int(round(seconds / DT))):
            for _ in range(self.nsub):
                if before_step:
                    before_step()
                mujoco.mj_step(self.m, self.d)
            self.snap()


def act(m, name):
    return m.actuator(name).id


def move(rec, targets, seconds, lift_rate=True):
    """Ease the position targets to `targets` over `seconds` (lift capped at the stepper speed)."""
    m, d = rec.m, rec.d
    ids = {k: act(m, k) for k in targets}
    start = {k: float(d.ctrl[i]) for k, i in ids.items()}
    if "lift" in targets and lift_rate:
        seconds = max(seconds, abs(targets["lift"] - start["lift"]) / LIFT_SPEED)
    n = max(1, int(round(seconds / DT)))
    for k in range(1, n + 1):
        s = 0.5 - 0.5 * math.cos(math.pi * k / n)
        for name, i in ids.items():
            v = start[name] + (targets[name] - start[name]) * s
            if name == "lift" and lift_rate:
                v = start[name] + np.clip(targets[name] - start[name], -LIFT_SPEED * k * DT, LIFT_SPEED * k * DT)
            d.ctrl[i] = v
        rec.run(DT)


def home(m, d, extra=None):
    mujoco.mj_resetDataKeyframe(m, d, m.key("home").id)
    for k, v in (extra or {}).items():
        d.qpos[m.jnt_qposadr[m.joint(k).id]] = v
        d.ctrl[act(m, k)] = v
    mujoco.mj_forward(m, d)


def arm_targets(side, q):
    return {f"{side}_{n}": float(v) for n, v in zip(bob_env.ARM, q)}


def ik_both(m, d, targets, tilt, lift):
    """IK for one or both arms at a fixed lift, collision-free. targets: {'l': xyz, 'r': xyz}."""
    out = {}
    lq = m.jnt_qposadr[m.joint("lift").id]
    for side, xyz in targets.items():
        ik = bob_env.Ik(m, side)
        found = None
        tilts = tilt if isinstance(tilt, (list, tuple)) else [tilt]
        for seed, tl in [(sd, t) for t in tilts for sd in ([-0.3, 0.0, 0.0, -0.9, 1.15, 0.0], [-1.0, 0, 0, -0.6, 1.2, 0],
                                                           [-2.2, 0, 0, -0.3, 0.8, 0], [-2.6, 0, 0, -0.5, 1.7, 0], [-1.5, 0, 0, -1.4, 1.9, 0])]:
            if found is not None:
                break
            q0 = d.qpos.copy()
            q0[lq] = lift
            q0[ik.qadr] = seed
            sol, ok = ik.solve(q0, np.array(xyz), E._tilt(tl))
            if ok:
                dd = mujoco.MjData(m)
                dd.qpos[:] = q0
                dd.qpos[ik.qadr] = sol
                mujoco.mj_forward(m, dd)
                if not any("floor" not in m.geom(c.geom1).name + m.geom(c.geom2).name and "cube" not in m.geom(c.geom1).name + m.geom(c.geom2).name
                           for c in dd.contact[:dd.ncon]):
                    found = sol
        if found is None:
            raise RuntimeError(f"no IK for {side} at {xyz}")
        out[side] = found
    return out


def done(rec, task_id, title, desc, result, props, objs=None):
    return {"id": task_id, "title": title, "desc": desc, "result": result, "dt": DT, "props": props,
            "objs": objs or [], "frames": rec.frames}


# ---------------------------------------------------------------- tasks

def task_pick_expert():
    env = bob_env.BobV3Env("pick", max_steps=400)
    ex = E.Expert(env)
    for seed in range(7, 60):
        env.reset(seed=seed)
        rec = Rec(env.m, env.d)
        rec.snap()
        ok, extra = False, 0
        for _ in range(400):
            obs, r, term, trunc, info = env.step(ex.act())
            rec.snap()
            ok = ok or info["is_success"]
            extra += ok
            if extra > 40 or (trunc and not ok):
                break
        if ok:
            z = env.d.xpos[env.cube_body][2] - 0.7725
            return done(rec, "pick", "Pick a cube off a table",
                        "Scripted closed-loop expert: IK to above the cube, descend, close the rack-and-pinion gripper, lift. "
                        "This expert gets 97% over 100 random placements.",
                        f"Cube lifted {z * 1000:.0f} mm, held by both pads.", {"table": True}, ["cube"])
    raise RuntimeError("no successful pick")


def task_pick_policy():
    import torch
    from torch import nn

    ck = torch.load(HERE / "models" / "bc_pick.pt")
    nin, nout = ck["dims"]
    net = nn.Sequential(nn.Linear(nin, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, nout), nn.Tanh())
    net.load_state_dict(ck["net"])
    env = bob_env.BobV3Env("pick", max_steps=400)
    wins = 0
    best = None
    for ep in range(20):
        obs, _ = env.reset(seed=50_000 + ep)
        rec = Rec(env.m, env.d)
        rec.snap()
        ok, extra = False, 0
        for _ in range(400):
            with torch.no_grad():
                a = net((torch.tensor(obs) - ck["mu"]) / ck["sd"]).numpy()
            obs, r, term, trunc, info = env.step(a)
            rec.snap()
            ok = ok or info["is_success"]
            extra += ok
            if extra > 40 or (trunc and not ok):
                break
        wins += ok
        if ok and best is None:
            best = rec
    return done(best, "policy", "Pick by the learned policy",
                "A neural network trained by behaviour cloning on the expert's demos (MLP on joint state, cube and touch). "
                "No IK and no script: it outputs the 8 actions every 40 ms.",
                f"{wins}/20 picks on cube positions it never saw in training.", {"table": True}, ["cube"])


def task_floor():
    cube = (0.38, -0.20, 0.0225)
    m, d = scene(cubes=[cube])
    home(m, d)
    rec = Rec(m, d)
    rec.snap()
    move(rec, {"lift": 0.0, "head_tilt": 0.55}, 3.0)
    q = ik_both(m, d, {"r": (cube[0], cube[1], cube[2] + 0.10)}, 0.0, 0.0)
    move(rec, {**arm_targets("r", q["r"]), "r_gripper": 0.04}, 2.0)
    q2 = ik_both(m, d, {"r": cube}, 0.0, 0.0)
    move(rec, arm_targets("r", q2["r"]), 1.5)
    move(rec, {"r_gripper": 0.0}, 1.0)
    rec.run(0.4)
    q3 = ik_both(m, d, {"r": (cube[0], cube[1], cube[2] + 0.20)}, 0.0, 0.0)
    move(rec, arm_targets("r", q3["r"]), 1.6)
    rec.run(0.8)
    z = d.xpos[m.body("cube0").id][2] - cube[2]
    return done(rec, "floor", "Pick from the floor",
                "Lift all the way down, head tilted to the floor, right hand to a cube 0.38 m from the base centre, "
                "just past the front of the base.",
                f"Cube lifted {z * 1000:.0f} mm off the floor." if z > 0.05 else "Grasp missed in this run.",
                {}, ["cube"])


def task_shelf():
    m, d = scene(shelf=True)
    home(m, d)
    rec = Rec(m, d)
    rec.snap()
    q1 = ik_both(m, d, {"r": (0.38, -0.20, 1.58)}, [1.4, 1.2, 1.6, 1.0], 0.65)
    q = ik_both(m, d, {"r": (0.48, -0.20, 1.555)}, [1.4, 1.2, 1.6], 0.65)
    move(rec, {"lift": 0.65, "head_tilt": -0.35}, 4.0)
    # fold the arm up close to the body, rise in front of the shelf edge, then reach over it
    move(rec, {"r_shoulder_pitch": -2.6, "r_elbow": -1.9, "r_wrist_pitch": 1.2}, 2.5)
    move(rec, {**arm_targets("r", q1["r"]), "r_gripper": 0.035}, 2.5)
    move(rec, arm_targets("r", q["r"]), 2.0)
    rec.run(1.0)
    tip = d.site_xpos[m.site("tcp_r").id]
    return done(rec, "shelf", "Reach up to a 1.5 m shelf",
                "The stepper raises the torso the full 650 mm at its real 25 mm/s. The right arm folds up close to the body, then reaches to the shelf.",
                f"Hand at {tip[2]:.2f} m, {abs(tip[0] - 0.42) * 100:.0f} cm {'past' if tip[0] > 0.42 else 'short of'} the shelf's front edge. "
                f"The lift took {0.65 / LIFT_SPEED:.0f} s.",
                {"shelf": True})


def task_hold():
    m, d = scene()
    for s in ("l", "r"):  # 0.5 kg at each tool point
        b = m.body(f"{s}_link6").id
        tcp = m.site(f"tcp_{s}").id
        m0, c0 = m.body_mass[b], m.body_ipos[b].copy()
        m.body_mass[b] = m0 + 0.5
        m.body_ipos[b] = (m0 * c0 + 0.5 * m.site_pos[tcp]) / (m0 + 0.5)
    home(m, d)
    rec = Rec(m, d, payload_boxes=True)
    rec.snap()
    move(rec, {"lift": 0.4}, 3.0)
    out = {}
    for s in ("l", "r"):
        out.update({f"{s}_shoulder_pitch": -1.5708, f"{s}_elbow": 0.0, f"{s}_wrist_pitch": 0.0, f"{s}_shoulder_roll": 0.0, f"{s}_gripper": 0.0})
    move(rec, out, 3.0)
    rec.run(2.0)
    err = max(abs(math.degrees(d.qpos[m.jnt_qposadr[m.joint(k).id]] - v)) for k, v in out.items() if "gripper" not in k)
    tau = abs(d.actuator_force[act(m, "l_shoulder_pitch")])
    return done(rec, "hold", "Hold 0.5 kg in each hand, arms straight out",
                "The worst gravity load for the shoulders and elbows. The blue blocks are the 0.5 kg payloads.",
                f"Worst joint sag {err:.1f}°. Shoulder pitch at {tau:.1f} N·m of its 20.8 N·m peak.", {}, ["payload", "payload"])


def task_drive():
    m, d = scene()
    home(m, d)
    rec = Rec(m, d)
    rec.snap()
    move(rec, {"lift": 0.3}, 2.0)
    wl, wr = act(m, "wheel_l"), act(m, "wheel_r")
    state = {"v": 0.0, "w": 0.0}

    def drive(v_goal, w_goal, accel=1.0, seconds=1.0):
        n = int(round(seconds / DT))
        for _ in range(n):
            state["v"] += np.clip(v_goal - state["v"], -accel * DT, accel * DT)
            state["w"] += np.clip(w_goal - state["w"], -2.0 * DT, 2.0 * DT)
            half = 0.185
            d.ctrl[wl] = (state["v"] - state["w"] * half) / 0.0825
            d.ctrl[wr] = (state["v"] + state["w"] * half) / 0.0825
            rec.run(DT)

    drive(0.6, 0.0, seconds=2.5)
    drive(0.6, 0.9, seconds=2.0)
    drive(0.6, 0.0, seconds=1.0)
    tilt = 0.0
    drive(0.0, 0.0, accel=3.0, seconds=1.5)
    for f in rec.frames:
        w, x, y, z = f["base"][3:]
        tilt = max(tilt, math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * (x * x + y * y))))))
    rec.run(1.0)
    dist = float(np.linalg.norm(d.qpos[:2]))
    return done(rec, "drive", "Drive, turn, and stop hard",
                "Torso part way up. 0.6 m/s forward, a turn, then a 3 m/s² stop: harder than the base controller allows.",
                f"Travelled {dist:.1f} m. Worst body tilt {tilt:.1f}°.", {})


def task_push():
    m, d = scene()
    home(m, d)
    rec = Rec(m, d)
    rec.snap()
    move(rec, {"lift": 0.65, "l_shoulder_pitch": -1.2, "r_shoulder_pitch": -1.2, "l_elbow": -0.3, "r_elbow": -0.3}, 3.0)
    hb = m.body("head_tilt").id
    F = 25.0

    def push():
        d.xfrc_applied[hb, 0] = F

    rec.force = {"body": "head_tilt", "N": F, "dir": [1, 0, 0]}
    rec.run(1.5, push)
    d.xfrc_applied[hb, :] = 0
    rec.force = None
    max_t = 0.0
    for f in rec.frames:
        w, x, y, z = f["base"][3:]
        max_t = max(max_t, math.degrees(math.acos(max(-1.0, min(1.0, 1 - 2 * (x * x + y * y))))))
    rec.run(2.0)
    return done(rec, "push", "Shove at the head, worst pose",
                f"Torso at the top, arms forward. A {F:.0f} N push at the head for 1.5 s. The check finds the tipping point at about 30 N.",
                f"Worst tilt {max_t:.1f}°. It settles back.", {})


def task_wave():
    m, d = scene()
    home(m, d)
    rec = Rec(m, d)
    rec.snap()
    move(rec, {"lift": 0.3, "head_pan": 0.35, "l_shoulder_pitch": -0.25, "l_shoulder_roll": 1.45, "l_elbow": -1.4, "l_wrist_pitch": 0.0}, 2.5)
    for _ in range(3):
        move(rec, {"l_upper_arm_yaw": 0.5, "l_wrist_roll": 0.4}, 0.6, lift_rate=False)
        move(rec, {"l_upper_arm_yaw": -0.3, "l_wrist_roll": -0.4}, 0.6, lift_rate=False)
    move(rec, {"l_upper_arm_yaw": 0.0, "l_wrist_roll": 0.0, "head_pan": 0.0}, 0.8)
    rec.run(0.5)
    return done(rec, "wave", "Wave", "Shoulder roll up, then upper-arm yaw and wrist roll back and forth.", "Hello.", {})


def main():
    out = Path(sys.argv[1])
    tasks = []
    for fn in (task_pick_expert, task_pick_policy, task_floor, task_shelf, task_hold, task_drive, task_push, task_wave):
        t = fn()
        print(f"{t['id']:8s} {len(t['frames']):4d} frames  {t['result']}")
        tasks.append(t)
    data = {"cube": 45, "payload": 60,
            "table": {"center": [620, 0, 730], "size": [600, 900, 40], "legs": [[880, 410], [880, -410], [360, 410], [360, -410]]},
            "shelf": {"center": [560, -200, 1490], "size": [280, 500, 24]},
            "tasks": tasks}
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(f"-> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
