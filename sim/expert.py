"""Closed-loop scripted pick expert for BobV3Pick-v0.

The action depends only on what the robot can observe (tool point, cube, gripper, touch),
so its demonstrations are learnable by behaviour cloning. It drives the same 8-number
action the learner gets.

  approach: tool point to 10 cm above the cube, gripper open
  descend:  once over the cube, tool point to the cube centre
  close:    once at the cube, close the gripper
  lift:     once both pads touch, raise 13 cm
"""

from __future__ import annotations

import numpy as np

from bob_env import LIFT_SPEED, CTRL_DT, MAX_DQ, BobV3Env, Ik


def _tilt(a):
    """Tool frame pitched forward by a (rad) about world y: fingers reach out and down."""
    c, s = np.cos(-a), np.sin(-a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


class Expert:
    def __init__(self, env: BobV3Env):
        self.env = env
        self.ik = Ik(env.m, "r")
        self.plan_for = None
        self.lift = None
        self.rot = np.eye(3)
        self.bias = np.zeros(3)
        self.plan_q = {}

    def _plan(self, cube):
        """Choose the lift height and hand tilt once per cube position (deterministic in the cube pose)."""
        env, ik = self.env, self.ik
        q = env.d.qpos.copy()
        seeds = [q.copy()]
        s2 = q.copy()
        s2[ik.qadr] = [-0.9, 0.0, 0.0, -0.9, 1.6, 0.0]
        seeds.append(s2)
        lift_hi = float(env.m.jnt_range[env.m.joint("lift").id][1])
        lifts = sorted(set(np.round(np.arange(0.20, lift_hi + 1e-9, 0.05), 3)) | {round(lift_hi, 3)})
        for lift in sorted(lifts, key=lambda v: abs(v - min(0.5, lift_hi))):
            for tilt in (0.0, 0.35, 0.7):
                for seed in seeds:
                    q0 = seed.copy()
                    q0[env.lift_q] = lift
                    rot = _tilt(tilt)
                    good = True
                    sols = {}
                    for name, off in (("pre", [0, 0, 0.10]), ("grasp", [0, 0, 0.0]), ("up", [0, 0, 0.13])):
                        qa, ok = ik.solve(q0, cube + off, rot)
                        if not ok or not self._clear(q0, ik.qadr, qa):
                            good = False
                            break
                        q0 = q0.copy()
                        q0[ik.qadr] = qa
                        sols[name] = qa
                    if good:
                        self.plan_q = sols
                        return lift, rot
        return min(0.5, lift_hi), np.eye(3)

    def _clear(self, q, adr, qa) -> bool:
        """No contact except the fingers on the cube and the wheels on the floor, with 1 cm of margin to the joint limits."""
        import mujoco

        if np.any(qa < self.ik.lo + 0.01) or np.any(qa > self.ik.hi - 0.01):
            return False
        m = self.env.m
        d = self._scratch = getattr(self, "_scratch", None) or mujoco.MjData(m)
        d.qpos[:] = q
        d.qpos[adr] = qa
        mujoco.mj_forward(m, d)
        for c in d.contact[:d.ncon]:
            n = m.geom(c.geom1).name + "|" + m.geom(c.geom2).name
            if "floor" in n or "cube" in n:
                continue
            return False
        return True

    def act(self) -> np.ndarray:
        env, d = self.env, self.env.d
        cube = d.xpos[env.cube_body].copy()
        tcp = d.site_xpos[env.tcp].copy()
        key = tuple(np.round(env.cube_start, 4))
        if self.plan_for != key:
            self.lift, self.rot = self._plan(env.cube_start.copy())
            self.plan_for = key
            self.bias[:] = 0
        touch = [d.sensordata[env.m.sensor_adr[s]] > 0.5 for s in env.touch]
        grip_q = d.qpos[env.grip_q]
        lift_now = d.qpos[env.lift_q]
        grip = 1.0
        if all(touch) and grip_q < 0.03:
            target, phase = env.cube_start + [0, 0, 0.13], "up"
            grip = -1.0
        elif np.linalg.norm(tcp - cube) < 0.015 or (any(touch) and np.linalg.norm(tcp[:2] - cube[:2]) < 0.02):
            target, phase = cube, "grasp"
            grip = -1.0
        elif np.linalg.norm(tcp[:2] - cube[:2]) < 0.02 and tcp[2] > cube[2] - 0.005:
            target, phase = cube, "grasp"
        else:
            target, phase = cube + [0, 0, 0.10], "pre"
        a = np.zeros(8)
        if abs(lift_now - self.lift) > 0.004:
            a[7] = np.clip((self.lift - d.ctrl[env.lift_act]) / (LIFT_SPEED * CTRL_DT), -1, 1)
            a[6] = 1.0
            return a
        # integral term on the tool point soaks up servo sag and model error
        self.bias = np.clip(self.bias + 0.15 * (target - tcp), -0.04, 0.04)
        seed = d.qpos.copy()
        if phase in self.plan_q:
            seed[self.ik.qadr] = self.plan_q[phase]
        qa, _ = self.ik.solve(seed, target + self.bias, self.rot, iters=40)
        a[:6] = np.clip((qa - d.ctrl[env.arm_act]) / MAX_DQ, -1, 1)
        a[6] = grip
        return a


def run_episode(env: BobV3Env, seed=None, frames=None, expert: Expert | None = None):
    expert = expert or Expert(env)
    obs, _ = env.reset(seed=seed)
    traj = {"obs": [], "act": []}
    success = False
    while True:
        a = expert.act()
        traj["obs"].append(obs if not isinstance(obs, dict) else obs["state"])
        traj["act"].append(a.astype(np.float32))
        obs, r, term, trunc, info = env.step(a)
        if frames is not None and env.steps % 2 == 0:
            frames.append(env.render())
        success = success or info["is_success"]
        if term or trunc:
            break
    return success, True, traj
