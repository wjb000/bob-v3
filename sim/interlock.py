"""Reach-limit interlock: with a load in a hand the arms may not reach out, and once the column
leaves the bottom the hands stay close in.

The base is 360 x 360 mm, so a load held out in front with the torso raised moves the centre of
mass toward the front ball transfer. The controller checks every new arm target before it is sent:

* LOADED means either hand holds more than PAYLOAD_MIN_KG (gripper current or the touch pads).
* Loaded, lift <= LIFT_FREE_M: each tool point stays X_REAR_M..X_CAP_LOW_M in front of the wheel
  axle and no higher than its shoulder (carry pose and floor pick are inside).
* Loaded, lift > LIFT_FREE_M: X_REAR_M..X_CAP_HIGH_M in front of the axle and no higher than
  the shoulder (hands tucked at the chest or down by the sides).
* A target that breaks the rule is cut short along the move. If a hand is already outside (it
  grasped something further out), moves that do not take it further forward are allowed, so the
  grasp can be lifted and pulled in.

Numbers come from tests/interlock_study.py and tests/envelope_scan.py on the 360 x 360 MJCF.
"""
import mujoco
import numpy as np

PAYLOAD_MIN_KG = 0.05
LIFT_FREE_M = 0.01  # column at the bottom
X_CAP_LOW_M = 0.53
X_CAP_HIGH_M = 0.16
X_REAR_M = 0.04
Z_CAP_LOW_M = 0.0  # hands no higher than the shoulder
Z_CAP_HIGH_M = 0.0  # hands no higher than the shoulder
REACH_SLACK_M = 0.01
SIDES = ("l", "r")


class Interlock:
    def __init__(self, m: mujoco.MjModel):
        self.m = m
        self.d = mujoco.MjData(m)
        self.tcp = {s: m.site(f"tcp_{s}").id for s in SIDES}
        self.shoulder = {s: m.joint(f"{s}_shoulder_pitch").id for s in SIDES}
        self.lift_q = m.jnt_qposadr[m.joint("lift").id]
        self.grasp_x = None

    def hands(self, qpos):
        d = self.d
        d.qpos[:] = qpos
        mujoco.mj_kinematics(self.m, d)
        mujoco.mj_comPos(self.m, d)
        base = d.xpos[self.m.body("base").id]
        R = d.xmat[self.m.body("base").id].reshape(3, 3)
        out = {}
        for s in SIDES:
            p = R.T @ (d.site_xpos[self.tcp[s]] - base)
            sh = R.T @ (d.xanchor[self.shoulder[s]] - base)
            out[s] = (p, sh)
        return out

    def ok(self, qpos, loaded: bool, lift: float | None = None) -> bool:
        if not loaded:
            return True
        lift = float(qpos[self.lift_q]) if lift is None else lift
        for p, sh in self.hands(qpos).values():
            if p[0] > (X_CAP_LOW_M if lift <= LIFT_FREE_M else X_CAP_HIGH_M) or p[0] < X_REAR_M:
                return False
            if p[2] > sh[2] + (Z_CAP_LOW_M if lift <= LIFT_FREE_M else Z_CAP_HIGH_M):
                return False
        return True

    def clamp(self, q_now, q_target, loaded: bool):
        """Largest step from q_now toward q_target that keeps the rule (or that does not make it worse)."""
        q_now = np.asarray(q_now, float)
        q_target = np.asarray(q_target, float)
        if not loaded:
            self.grasp_x = None
        elif self.grasp_x is None:
            # how far forward each hand was when it closed on the load
            self.grasp_x = {s: p[0] for s, (p, _) in self.hands(q_now).items()}
        if not self.ok(q_now, loaded):
            # grasped further out than the envelope: no hand may go further forward than where it
            # gripped (1 cm of slack for servo sag); lifting it and pulling it in are free
            lim = {s: x + REACH_SLACK_M for s, x in self.grasp_x.items()}
            fits = lambda q: all(p[0] <= lim[s] for s, (p, _) in self.hands(q).items())  # noqa: E731
        else:
            fits = lambda q: self.ok(q, loaded)  # noqa: E731
        if fits(q_target):
            return q_target, False
        lo, hi = 0.0, 1.0
        for _ in range(12):
            t = (lo + hi) / 2
            if fits(q_now + t * (q_target - q_now)):
                lo = t
            else:
                hi = t
        return q_now + lo * (q_target - q_now), True

    def _excess(self, qpos, reach_only=False):
        lift = float(qpos[self.lift_q])
        e = 0.0
        for p, sh in self.hands(qpos).values():
            cap = X_CAP_LOW_M if lift <= LIFT_FREE_M else X_CAP_HIGH_M
            e += max(0.0, p[0] - cap)
            if reach_only:
                continue
            e += max(0.0, X_REAR_M - p[0])
            e += max(0.0, p[2] - sh[2] - (Z_CAP_LOW_M if lift <= LIFT_FREE_M else Z_CAP_HIGH_M))
        return e
