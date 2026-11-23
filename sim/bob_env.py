"""Gymnasium environments for Bob v3 in MuJoCo.

    import gymnasium as gym, bob_env
    env = gym.make("BobV3Pick-v0", render_mode="rgb_array")

Tasks
  BobV3Reach-v0  move the right hand's tool point to a random target in front of the robot
  BobV3Pick-v0   pick a 45 mm cube off a 0.75 m table and lift it 10 cm

Action (both tasks): 8 numbers in [-1, 1]
  0..5  right arm joint target deltas (pitch, roll, yaw, elbow, wrist pitch, wrist roll), 0.05 rad per step max
  6     gripper target, absolute (-1 closed .. 1 open)
  7     lift target delta, LIFT_SPEED per step max
The left arm, head and wheels hold their home targets. Control runs at 25 Hz (20 physics steps).

Observation (dict flattened to a vector): arm joints, velocities, gripper, lift, tool position,
tool-to-target vector, object pose (pick), finger touch (pick).
Add obs_images=True to also get head_cam and wrist_cam_r images (for imitation learning).
"""

from __future__ import annotations

from pathlib import Path

import gymnasium as gym
import mujoco
import numpy as np
from gymnasium import spaces

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from interlock import Interlock  # noqa: E402

ROOT = Path(__file__).resolve().parent
ARM = ["shoulder_pitch", "shoulder_roll", "upper_arm_yaw", "elbow", "wrist_pitch", "wrist_roll"]
CTRL_DT = 0.04
LIFT_SPEED = 0.025  # m/s, the stepper's real speed
MAX_DQ = 0.05


def scene_xml(task: str) -> str:
    """Robot plus a table and, for pick, a cube. Written next to bob_v3.xml so mesh paths resolve."""
    table = """
    <body name="table" pos="0.62 0 0">
      <geom name="table_top" type="box" size="0.30 0.45 0.02" pos="0 0 0.73" rgba="0.62 0.47 0.33 1" contype="8" conaffinity="15"/>
      <geom name="table_leg1" type="box" size="0.02 0.02 0.355" pos="0.26 0.41 0.355" rgba="0.3 0.3 0.3 1"/>
      <geom name="table_leg2" type="box" size="0.02 0.02 0.355" pos="0.26 -0.41 0.355" rgba="0.3 0.3 0.3 1"/>
      <geom name="table_leg3" type="box" size="0.02 0.02 0.355" pos="-0.26 0.41 0.355" rgba="0.3 0.3 0.3 1"/>
      <geom name="table_leg4" type="box" size="0.02 0.02 0.355" pos="-0.26 -0.41 0.355" rgba="0.3 0.3 0.3 1"/>
    </body>"""
    cube = """
    <body name="cube" pos="0.45 -0.2 0.7725">
      <freejoint name="cube"/>
      <geom name="cube" type="box" size="0.0225 0.0225 0.0225" mass="0.08" rgba="0.95 0.35 0.1 1"
            contype="8" conaffinity="15" friction="1.0 0.01 0.001" condim="4"/>
    </body>""" if task == "pick" else ""
    target = '<site name="target" pos="0.45 -0.2 0.9" size="0.02" rgba="0 1 0 0.5"/>'
    return f"""<mujoco model="bob_v3_{task}">
  <include file="bob_v3.xml"/>
  <worldbody>{table}{cube}
    {target}
  </worldbody>
</mujoco>
"""


def load_model(task: str) -> mujoco.MjModel:
    path = ROOT / f"scene_{task}.xml"
    path.write_text(scene_xml(task))
    return mujoco.MjModel.from_xml_path(str(path))


class Ik:
    """Damped least squares on one arm's six joints, position plus orientation of the tool point."""

    def __init__(self, m: mujoco.MjModel, side: str = "r"):
        self.m = m
        self.d = mujoco.MjData(m)
        self.site = m.site(f"tcp_{side}").id
        self.joints = [m.joint(f"{side}_{n}").id for n in ARM]
        self.qadr = np.array([m.jnt_qposadr[j] for j in self.joints])
        self.dadr = np.array([m.jnt_dofadr[j] for j in self.joints])
        self.lo = np.array([m.jnt_range[j][0] for j in self.joints])
        self.hi = np.array([m.jnt_range[j][1] for j in self.joints])

    def solve(self, qpos, pos, rot=None, iters=200, tol=2e-3, w_rot=0.25):
        d = self.d
        d.qpos[:] = qpos
        jp = np.zeros((3, self.m.nv))
        jr = np.zeros((3, self.m.nv))
        for _ in range(iters):
            mujoco.mj_kinematics(self.m, d)
            mujoco.mj_comPos(self.m, d)
            p = d.site_xpos[self.site]
            R = d.site_xmat[self.site].reshape(3, 3)
            e = pos - p
            er = np.zeros(3)
            if rot is not None:
                Rerr = rot @ R.T
                quat = np.zeros(4)
                mujoco.mju_mat2Quat(quat, Rerr.flatten())
                er = np.zeros(3)
                mujoco.mju_quat2Vel(er, quat, 1.0)
            if np.linalg.norm(e) < tol and np.linalg.norm(er) < 0.03:
                return d.qpos[self.qadr].copy(), True
            mujoco.mj_jacSite(self.m, d, jp, jr, self.site)
            J = np.vstack([jp[:, self.dadr], w_rot * jr[:, self.dadr]])
            err = np.concatenate([e, w_rot * er])
            lam = 0.03
            dq = J.T @ np.linalg.solve(J @ J.T + lam ** 2 * np.eye(6), err)
            d.qpos[self.qadr] = np.clip(d.qpos[self.qadr] + np.clip(dq, -0.2, 0.2), self.lo, self.hi)
        return d.qpos[self.qadr].copy(), False


class BobV3Env(gym.Env):
    metadata = {"render_modes": ["rgb_array"], "render_fps": int(1 / CTRL_DT)}

    def __init__(self, task: str = "pick", render_mode: str | None = None, obs_images: bool = False,
                 max_steps: int = 250, image_size=(240, 320)):
        self.task = task
        self.m = load_model(task)
        self.d = mujoco.MjData(self.m)
        self.render_mode = render_mode
        self.obs_images = obs_images
        self.max_steps = max_steps
        self.nsub = int(round(CTRL_DT / self.m.opt.timestep))
        self.arm_act = np.array([self.m.actuator(f"r_{n}").id for n in ARM])
        self.arm_q = np.array([self.m.jnt_qposadr[self.m.joint(f"r_{n}").id] for n in ARM])
        self.arm_v = np.array([self.m.jnt_dofadr[self.m.joint(f"r_{n}").id] for n in ARM])
        self.grip_act = self.m.actuator("r_gripper").id
        self.grip_q = self.m.jnt_qposadr[self.m.joint("r_gripper").id]
        self.lift_act = self.m.actuator("lift").id
        self.lift_q = self.m.jnt_qposadr[self.m.joint("lift").id]
        self.tcp = self.m.site("tcp_r").id
        self.target_site = self.m.site("target").id
        self.cube_body = self.m.body("cube").id if task == "pick" else -1
        self.cube_q = self.m.jnt_qposadr[self.m.joint("cube").id] if task == "pick" else -1
        self.touch = [self.m.sensor("touch_a_r").id, self.m.sensor("touch_b_r").id]
        self.interlock = Interlock(self.m)
        self.interlock_hits = 0
        self.action_space = spaces.Box(-1.0, 1.0, (8,), np.float32)
        self.target = np.zeros(3)
        mujoco.mj_forward(self.m, self.d)
        n = len(self._obs_vec())
        vec = spaces.Box(-np.inf, np.inf, (n,), np.float32)
        if obs_images:
            h, w = image_size
            self.observation_space = spaces.Dict({
                "state": vec,
                "head_cam": spaces.Box(0, 255, (h, w, 3), np.uint8),
                "wrist_cam_r": spaces.Box(0, 255, (h, w, 3), np.uint8),
            })
            self._cam_renderer = mujoco.Renderer(self.m, h, w)
        else:
            self.observation_space = vec
        self._renderer = None
        self.steps = 0

    # ------------------------------------------------------------ helpers
    def _obs_vec(self):
        d = self.d
        tcp = d.site_xpos[self.tcp]
        obj = d.xpos[self.cube_body] if self.cube_body >= 0 else self.target
        parts = [d.qpos[self.arm_q], d.qvel[self.arm_v] * 0.1, [d.qpos[self.grip_q], d.qpos[self.lift_q]], tcp,
                 self.target - tcp, obj - tcp, obj]
        if self.cube_body >= 0:
            parts.append(d.xquat[self.cube_body])
            parts.append(np.tanh(np.array([d.sensordata[self.m.sensor_adr[s]] for s in self.touch]) / 5.0))
        return np.concatenate([np.ravel(p) for p in parts]).astype(np.float32)

    def _obs(self):
        if not self.obs_images:
            return self._obs_vec()
        out = {"state": self._obs_vec()}
        for cam in ("head_cam", "wrist_cam_r"):
            self._cam_renderer.update_scene(self.d, camera=cam)
            out[cam] = self._cam_renderer.render().copy()
        return out

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetDataKeyframe(self.m, self.d, self.m.key("home").id)
        rng = self.np_random
        lhi = float(self.m.jnt_range[self.m.joint("lift").id][1])
        lift = min(0.50, lhi) if self.task == "pick" else rng.uniform(0.0, min(0.4, lhi))  # shoulder ~0.27 m above the table top
        self.d.qpos[self.lift_q] = lift
        self.d.ctrl[self.lift_act] = lift
        if self.task == "pick":
            # right-hand side of the robot; objects nearer the centreline are the left hand's job
            p = np.array([rng.uniform(0.40, 0.55), rng.uniform(-0.30, -0.12), 0.75 + 0.0225])
            self.d.qpos[self.cube_q:self.cube_q + 3] = p
            self.d.qpos[self.cube_q + 3:self.cube_q + 7] = [1, 0, 0, 0]
            self.target = p + np.array([0, 0, 0.10])
            self.cube_start = p.copy()
        else:
            self.target = np.array([rng.uniform(0.35, 0.65), rng.uniform(-0.45, 0.05), rng.uniform(0.45, 1.25)])
        self.m.site_pos[self.target_site] = self.target
        mujoco.mj_forward(self.m, self.d)
        for _ in range(20):
            mujoco.mj_step(self.m, self.d)
        self.steps = 0
        self.interlock.grasp_x = None
        return self._obs(), {}

    def step(self, action):
        a = np.clip(np.asarray(action, float), -1, 1)
        d = self.d
        lo = self.m.actuator_ctrlrange[self.arm_act, 0]
        hi = self.m.actuator_ctrlrange[self.arm_act, 1]
        d.ctrl[self.arm_act] = np.clip(d.ctrl[self.arm_act] + a[:6] * MAX_DQ, lo, hi)
        glo, ghi = self.m.actuator_ctrlrange[self.grip_act]
        d.ctrl[self.grip_act] = glo + (a[6] + 1) / 2 * (ghi - glo)
        llo, lhi = self.m.actuator_ctrlrange[self.lift_act]
        d.ctrl[self.lift_act] = np.clip(d.ctrl[self.lift_act] + a[7] * LIFT_SPEED * CTRL_DT, llo, lhi)
        # reach-limit interlock (sim/interlock.py): a loaded hand may not reach out
        q_t = d.qpos.copy()
        q_t[self.arm_q] = d.ctrl[self.arm_act]
        q_t[self.lift_q] = d.ctrl[self.lift_act]
        q_c, hit = self.interlock.clamp(d.qpos, q_t, self.loaded())
        if hit:
            self.interlock_hits += 1
            d.ctrl[self.arm_act] = q_c[self.arm_q]
            d.ctrl[self.lift_act] = q_c[self.lift_q]
        for _ in range(self.nsub):
            mujoco.mj_step(self.m, d)
        self.steps += 1
        reward, success = self._reward()
        terminated = bool(success)
        truncated = self.steps >= self.max_steps
        return self._obs(), reward, terminated, truncated, {"is_success": success}

    def loaded(self) -> bool:
        """The controller's payload flag: both pads pressed (a real build reads gripper current)."""
        return self.cube_body >= 0 and all(self.d.sensordata[self.m.sensor_adr[s]] > 0.5 for s in self.touch)

    def _reward(self):
        d = self.d
        tcp = d.site_xpos[self.tcp]
        if self.task == "reach":
            dist = np.linalg.norm(self.target - tcp)
            return float(-dist), bool(dist < 0.02)
        cube = d.xpos[self.cube_body]
        reach = np.linalg.norm(cube - tcp)
        touch = sum(d.sensordata[self.m.sensor_adr[s]] > 0.5 for s in self.touch)
        lifted = cube[2] - 0.7725
        r = -reach + 0.25 * touch + 5.0 * max(0.0, lifted) * (touch == 2)
        return float(r), bool(lifted > 0.08 and touch == 2)

    def render(self):
        if self._renderer is None:
            self._renderer = mujoco.Renderer(self.m, 480, 640)
        cam = mujoco.MjvCamera()
        cam.azimuth, cam.elevation, cam.distance = 150, -18, 2.2
        cam.lookat[:] = (0.3, -0.05, 0.75)
        self._renderer.update_scene(self.d, cam)
        return self._renderer.render()


gym.register("BobV3Reach-v0", entry_point=lambda **kw: BobV3Env(task="reach", **kw))
gym.register("BobV3Pick-v0", entry_point=lambda **kw: BobV3Env(task="pick", **kw))
