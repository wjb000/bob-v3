#!/usr/bin/env python3
"""Render every recorded viewer task into one MP4 reel.

    .venv/bin/python sim/tools/reel.py docs/sim_tasks.json docs/img/reel.mp4
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import mujoco

sys.path.insert(0, str(Path(__file__).resolve().parent))
import viewer_tasks as VT  # noqa: E402

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
tasks = json.loads(src.read_text())["tasks"]
W, H, FPS, MAX_S = 960, 720, 25, 6.0
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
                       "-preset", "slow", "-movflags", "+faststart", "-an", str(dst)], stdin=subprocess.PIPE)
opt = mujoco.MjvOption()
opt.geomgroup[:] = [1, 1, 1, 0, 0, 0]
for t in tasks:
    ncube = sum(1 for o in t["objs"] if o == "cube")
    cubes = [(1.0 + i, 0, 0.1) for i in range(ncube)]
    m, d = VT.scene(table=t["props"].get("table", False), shelf=t["props"].get("shelf", False), cubes=cubes)
    r = mujoco.Renderer(m, H, W)
    cam = mujoco.MjvCamera()
    cam.azimuth, cam.elevation, cam.distance = 145, -12, 2.4
    fr = t["frames"]
    stride = max(1, math.ceil(len(fr) / (MAX_S * FPS)))
    for f in fr[::stride] + [fr[-1]] * 12:
        for n, v in f["q"].items():
            d.qpos[m.jnt_qposadr[m.joint(n).id]] = v
        b = f["base"]
        d.qpos[:3] = [b[0] / 1000, b[1] / 1000, b[2] / 1000]
        d.qpos[3:7] = b[3:7]
        for i in range(ncube):
            o = f["objs"][i]
            a = m.jnt_qposadr[m.body(f"cube{i}").jntadr[0]]
            d.qpos[a:a + 3] = [o[0] / 1000, o[1] / 1000, o[2] / 1000]
            d.qpos[a + 3:a + 7] = o[3:7]
        mujoco.mj_forward(m, d)
        cam.lookat[:] = (d.qpos[0] + 0.15, d.qpos[1], 0.75)
        r.update_scene(d, cam, opt)
        ff.stdin.write(r.render().tobytes())
    r.close()
    print(t["id"], len(fr[::stride]), "frames")
ff.stdin.close()
ff.wait()
print("->", dst, dst.stat().st_size // 1024, "KB")
