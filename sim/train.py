#!/usr/bin/env python3
"""Train policies for Bob v3 in simulation.

Behaviour cloning from the scripted demos (fast, CPU is fine):
    .venv/bin/python sim/record_demos.py --episodes 200
    .venv/bin/python sim/train.py bc --steps 20000
    .venv/bin/python sim/train.py eval-bc --episodes 20

Reinforcement learning on the reach task with PPO (Stable-Baselines3):
    .venv/bin/python sim/train.py ppo --task reach --steps 500000

Models land in sim/models/. Requires: torch, stable-baselines3 (pip install -r requirements-sim.txt).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import bob_env

HERE = Path(__file__).resolve().parent  # works in the repo and in bob-v3-sim.zip
MODELS = HERE / "models"


def bc(steps: int, data: str):
    import torch
    from torch import nn

    d = np.load(data)
    X, Y = torch.tensor(d["obs"]), torch.tensor(d["action"])
    mu, sd = X.mean(0), X.std(0) + 1e-6
    net = nn.Sequential(nn.Linear(X.shape[1], 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, Y.shape[1]), nn.Tanh())
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    for i in range(steps):
        idx = torch.randint(0, len(X), (512,))
        loss = ((net((X[idx] - mu) / sd) - Y[idx]) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        if i % 2000 == 0:
            print(f"step {i:6d}  loss {loss.item():.4f}")
    MODELS.mkdir(parents=True, exist_ok=True)
    torch.save({"net": net.state_dict(), "mu": mu, "sd": sd, "dims": (X.shape[1], Y.shape[1])}, MODELS / "bc_pick.pt")
    print("saved", MODELS / "bc_pick.pt")


def eval_bc(episodes: int):
    import torch
    from torch import nn

    ck = torch.load(MODELS / "bc_pick.pt")
    nin, nout = ck["dims"]
    net = nn.Sequential(nn.Linear(nin, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, nout), nn.Tanh())
    net.load_state_dict(ck["net"])
    env = bob_env.BobV3Env("pick", max_steps=400)
    wins = 0
    for ep in range(episodes):
        obs, _ = env.reset(seed=50_000 + ep)
        done = False
        while not done:
            with torch.no_grad():
                a = net((torch.tensor(obs) - ck["mu"]) / ck["sd"]).numpy()
            obs, r, term, trunc, info = env.step(a)
            done = term or trunc
        wins += bool(info["is_success"])
    print(f"BC policy: {wins}/{episodes} picks on unseen cube positions")


def ppo(task: str, steps: int):
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    venv = make_vec_env(lambda: bob_env.BobV3Env(task, max_steps=150), n_envs=8)
    model = PPO("MlpPolicy", venv, n_steps=256, batch_size=512, learning_rate=3e-4, gamma=0.98, verbose=1)
    model.learn(total_timesteps=steps)
    MODELS.mkdir(parents=True, exist_ok=True)
    model.save(MODELS / f"ppo_{task}")
    print("saved", MODELS / f"ppo_{task}.zip")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["bc", "eval-bc", "ppo"])
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--episodes", type=int, default=20)
    ap.add_argument("--task", default="reach")
    ap.add_argument("--data", default=str(HERE / "data" / "pick_demos.npz"))
    a = ap.parse_args()
    if a.mode == "bc":
        bc(a.steps, a.data)
    elif a.mode == "eval-bc":
        eval_bc(a.episodes)
    else:
        ppo(a.task, a.steps)


if __name__ == "__main__":
    main()
