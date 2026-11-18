#!/usr/bin/env python3
"""Record scripted pick demonstrations for imitation learning.

    .venv/bin/python sim/record_demos.py --episodes 200 [--images] [--gif docs/img/pick.gif]

Writes sim/data/pick_demos.npz with obs, action, episode index and success flag per step.
With --images it also stores the head and right-wrist camera frames (160 x 120), which is the
input an ACT / diffusion policy (e.g. LeRobot) trains on.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import bob_env
import expert

HERE = Path(__file__).resolve().parent  # works in the repo and in bob-v3-sim.zip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=100)
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--gif", type=str, default="")
    ap.add_argument("--out", type=str, default=str(HERE / "data" / "pick_demos.npz"))
    a = ap.parse_args()
    env = bob_env.BobV3Env("pick", max_steps=400, obs_images=a.images, image_size=(120, 160))
    obs_l, act_l, ep_l, head_l, wrist_l = [], [], [], [], []
    wins = 0
    ex = expert.Expert(env)
    for ep in range(a.episodes):
        frames = [] if (a.gif and ep == 0) else None
        ok, _, traj = expert.run_episode(env, seed=ep, frames=frames, expert=ex)
        if frames:
            import imageio.v2 as imageio
            Path(a.gif).parent.mkdir(parents=True, exist_ok=True)
            imageio.mimsave(a.gif, [f[::2, ::2] for f in frames], duration=0.08, loop=0)
            print("wrote", a.gif)
        if not ok:
            continue
        wins += 1
        obs_l.append(np.array(traj["obs"], np.float32))
        act_l.append(np.array(traj["act"], np.float32))
        ep_l.append(np.full(len(traj["act"]), ep, np.int32))
    if a.images:
        # replay successful episodes deterministically to grab frames
        for ep in sorted(set(np.concatenate(ep_l).tolist())):
            env.reset(seed=int(ep))
            acts = np.concatenate(act_l)[np.concatenate(ep_l) == ep]
            obs, _ = env.reset(seed=int(ep))
            for act in acts:
                head_l.append(obs["head_cam"])
                wrist_l.append(obs["wrist_cam_r"])
                obs, *_ = env.step(act)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    data = dict(obs=np.concatenate(obs_l), action=np.concatenate(act_l), episode=np.concatenate(ep_l))
    if a.images:
        data["head_cam"] = np.array(head_l, np.uint8)
        data["wrist_cam_r"] = np.array(wrist_l, np.uint8)
    np.savez_compressed(a.out, **data)
    print(f"{wins}/{a.episodes} successful episodes, {len(data['action'])} steps -> {a.out}")


if __name__ == "__main__":
    main()
