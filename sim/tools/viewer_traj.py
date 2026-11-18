#!/usr/bin/env python3
"""Record a simulated pick for the web viewer: joint values and the cube pose at 25 Hz.

    .venv/bin/python sim/tools/viewer_traj.py docs/sim_pick.json
"""
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bob_env  # noqa: E402
import expert  # noqa: E402

out = Path(sys.argv[1])
env = bob_env.BobV3Env("pick", max_steps=400)
ex = expert.Expert(env)
for seed in range(7, 40):
    obs, _ = env.reset(seed=seed)
    m, d = env.m, env.d
    names = [m.joint(j).name for j in range(m.njnt) if m.jnt_type[j] in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_SLIDE)]
    frames, ok, extra = [], False, 0
    for _ in range(400):
        q = {n: round(float(d.qpos[m.jnt_qposadr[m.joint(n).id]]), 4) for n in names if not n.startswith("wheel")}
        c = d.xpos[env.cube_body] * 1000
        frames.append({"q": q, "cube": [round(float(v), 1) for v in c], "quat": [round(float(v), 4) for v in d.xquat[env.cube_body]]})
        obs, r, term, trunc, info = env.step(ex.act())
        ok = ok or info["is_success"]
        extra += ok
        if extra > 40 or (trunc and not ok):
            break
    if ok:
        break
data = {"dt": 0.04, "seed": seed, "frames": frames,
        "table": {"center": [620, 0, 730], "size": [600, 900, 40], "legs": [[880, 410], [880, -410], [360, 410], [360, -410]]},
        "cube": 45}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, separators=(",", ":")))
print(f"seed {seed}, {len(frames)} frames -> {out} ({out.stat().st_size // 1024} KB)")
