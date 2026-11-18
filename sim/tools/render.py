#!/usr/bin/env python3
"""Render Bob v3 poses to PNG with MuJoCo's offscreen renderer.

    .venv/bin/python sim/tools/render.py [out_dir]
"""
import sys
from pathlib import Path

import mujoco
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "img"
out.mkdir(parents=True, exist_ok=True)
m = mujoco.MjModel.from_xml_path(str(ROOT / "sim" / "bob_v3.xml"))
d = mujoco.MjData(m)
r = mujoco.Renderer(m, 1050, 1400)
opt = mujoco.MjvOption()
opt.geomgroup[:] = [1, 1, 1, 0, 0, 0]
views = {
    "hero": dict(az=148, el=-10, dist=1.75, look=(0.10, 0, 0.58)),
    "front": dict(az=180, el=-4, dist=2.6, look=(0.0, 0, 0.62)),
    "side": dict(az=90, el=-4, dist=2.7, look=(0.1, 0, 0.70)),
    "back": dict(az=-35, el=-12, dist=1.9, look=(0.0, 0, 0.58)),
    "tall": dict(az=140, el=-6, dist=2.3, look=(0.12, 0, 0.88)),
}
shots = [("home", "hero"), ("home", "front"), ("home", "side"), ("counter", "hero"), ("floor", "hero"), ("shelf", "tall"),
         ("wave", "hero"), ("home", "back")]
for key, view in shots:
    mujoco.mj_resetDataKeyframe(m, d, m.key(key).id)
    mujoco.mj_forward(m, d)
    cam = mujoco.MjvCamera()
    v = views[view]
    cam.azimuth, cam.elevation, cam.distance = v["az"], v["el"], v["dist"]
    cam.lookat[:] = v["look"]
    r.update_scene(d, cam, opt)
    img = r.render()
    Image.fromarray(img).save(out / f"{key}_{view}.png")
    print("wrote", out / f"{key}_{view}.png")
