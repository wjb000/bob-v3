"""Cable harness check: every wire path in sim/harness.json against the meshes in sim/assets.

harness.json is written by docs/harness.py. Points are mm in each link's zero-pose frame (the CAD
frame, +Z up). A link's meshes in sim/assets are in metres, relative to the link's joint anchor.

check() reports two things for every wire:
  clearance  no fixed segment or service loop comes closer to a part than the wire's radius plus
             MARGIN at the named poses and across the lift travel (the wire's own end parts and
             the drag chain it rides in are skipped)
  length     at every joint and lift limit, the straight distance across each joint is shorter
             than the cable left there (the chord at zero plus the service loop)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
MARGIN = 1.0  # mm, clear of every surface beyond the wire or bundle radius
SPACING = 0.9  # mm, surface sample spacing


def _rot(axis, ang):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    x, y, z = a
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def link_transforms(joints, pose):
    """4x4 transforms (mm) that move zero-pose points of each link to the posed robot. Same as cad/robot.py."""
    T = {"base": np.eye(4)}
    pending = list(joints)
    while pending:
        for j in list(pending):
            if j["parent"] not in T:
                continue
            q = pose.get(j["mimic"], 0.0) * j.get("mimic_coef", 1.0) if j.get("mimic") else pose.get(j["name"], 0.0)
            local = np.eye(4)
            if j["kind"] == "slide":
                local[:3, 3] = np.asarray(j["axis"], float) * q * 1000.0
            else:
                R = _rot(j["axis"], q)
                a = np.asarray(j["anchor"], float)
                local[:3, :3] = R
                local[:3, 3] = a - R @ a
            T[j["child"]] = T[j["parent"]] @ local
            pending.remove(j)
    return T


class Parts:
    """Surface samples with outward normals, per link, in the link's zero-pose frame (mm)."""

    def __init__(self, items, anchors, assets=HERE / "assets", skip=()):
        self.link = {}
        for it in items:
            if it["name"] in skip:
                continue
            m = trimesh.load_mesh(assets / it["file"])
            m.apply_scale(1000.0)
            m.apply_translation(anchors.get(it["link"], (0, 0, 0)))
            n = int(max(60, m.area / SPACING ** 2))
            p, fi = trimesh.sample.sample_surface_even(m, n, seed=1) if m.area > 0 else (np.zeros((0, 3)), [])
            p = np.vstack([p, m.vertices])
            nn = np.vstack([m.face_normals[fi], m.vertex_normals])
            L = self.link.setdefault(it["link"], ([], [], []))
            L[0].append(p), L[1].append(nn), L[2].extend([it["name"]] * len(p))
        self.tree = {}
        for k, (p, nn, names) in self.link.items():
            P = np.vstack(p)
            self.tree[k] = (cKDTree(P), P, np.vstack(nn), np.array(names))

    def clearance(self, q, links=None):
        """Signed distance (mm, negative inside) and the nearest part name, for points q (N,3) in one frame."""
        n = len(next(iter(q.values()))) if isinstance(q, dict) else len(q)
        best = np.full(n, np.inf)
        name = np.array([""] * n, dtype=object)
        for k, (tree, P, N, names) in self.tree.items():
            if (links is not None and k not in links) or (isinstance(q, dict) and k not in q):
                continue
            qq = q[k] if isinstance(q, dict) else q
            dk, ik = tree.query(qq, k=8)
            d, i = dk[:, 0], ik[:, 0]
            # inside only if every nearby surface faces away (an outside point near an edge sees both faces)
            inside = np.all(np.einsum("ikj,ikj->ik", qq[:, None, :] - P[ik], N[ik]) < -0.3, axis=1)
            d = np.where(inside, -d, d)
            take = d < best
            best[take], name[take] = d[take], names[i[take]]
        return best, name


def _dense(pts, step=1.5):
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        out.extend(a + (b - a) * (t / n) for t in range(1, n + 1))
    return np.array(out)


def poses(data, sweep=False):
    """Named poses and the lift travel; with sweep, every joint at both limits (arms hanging, lift up)."""
    out = dict(data["poses"])
    top = data["lift_travel"] / 1000.0
    home = data["poses"].get("home", {})
    for f in (0.0, 0.5, 1.0):
        out[f"lift {f:.1f}"] = {**home, "lift": f * top}
    if sweep:
        hang = data["poses"].get("zero", {"lift": top})
        for j in data["joints"]:
            if j.get("mimic") or j["name"].startswith(("wheel", "lift")) or "gripper" in j["name"]:
                continue
            for v in j["range"]:
                out[f"{j['name']} {v:+.2f}"] = {**hang, j["name"]: v}
    return out


def check(data=None, parts=None, verbose=False):
    data = data or json.loads((HERE / "harness.json").read_text())
    anchors = {k: np.asarray(v, float) for k, v in data["anchors"].items()}
    parts = parts or Parts(data["items"], anchors, skip=data.get("skip", ()))
    res = {"wires": len(data["wires"]), "worst_clear_mm": 1e9, "hits": [], "short": [], "worst_slack_mm": 1e9}
    named = poses(data)
    sweep = poses(data, sweep=True)
    Ts = {k: link_transforms(data["joints"], p) for k, p in sweep.items()}
    links = list(parts.tree)
    for w in data["wires"]:
        need = w["radius_mm"] + MARGIN
        # fixed segments and loops: densify each entry on its own link
        segs = [(e["item"], _dense(np.asarray(e["pts"], float))) for e in w["path"] if len(e["pts"]) >= 2]
        for pname in named:
            T = Ts[pname]
            for link, P in segs:
                W = (T[link][:3, :3] @ P.T).T + T[link][:3, 3]
                q = {}
                for k in links:
                    Ti = np.linalg.inv(T[k])
                    q[k] = (Ti[:3, :3] @ W.T).T + Ti[:3, 3]
                d, nm = parts.clearance(q)
                # skip the wire's own terminations and parts it is allowed to touch
                el = [(T[e[0]][:3, :3] @ np.asarray(e[1:4]) + T[e[0]][:3, 3]) for e in w["ends_l"]]
                far = np.all([np.linalg.norm(W - e, axis=1) > w.get("end_skip", 14.0) for e in el], axis=0)
                ok_names = set(w.get("touch", ()))
                bad = far & (d < need) & ~np.isin(nm.astype(str), list(ok_names))
                if far.any():
                    m = float(np.min(np.where(far, d - w["radius_mm"], 1e9)))
                    res["worst_clear_mm"] = min(res["worst_clear_mm"], m)
                if bad.any():
                    i = int(np.argmin(np.where(bad, d, 1e9)))
                    if any(h["wire"] == w["id"] and h["part"] == str(nm[i]) for h in res["hits"]):
                        continue
                    res["hits"].append(dict(wire=w["id"], pose=pname, link=link, part=str(nm[i]), clear_mm=round(float(d[i] - w["radius_mm"]), 1),
                                            at=[round(float(v), 1) for v in P[i]]))
        # length across every joint and lift crossing
        for c in w["crossings"]:
            for pname, T in Ts.items():
                a = T[c["from"][0]] @ np.array([*c["from"][1:], 1.0])
                b = T[c["to"][0]] @ np.array([*c["to"][1:], 1.0])
                slack = c["cable_mm"] - float(np.linalg.norm(a[:3] - b[:3]))
                res["worst_slack_mm"] = min(res["worst_slack_mm"], slack)
                if slack < 3.0 and not any(x["wire"] == w["id"] and x["joint"] == c["joint"] for x in res["short"]):
                    res["short"].append(dict(wire=w["id"], joint=c["joint"], pose=pname, slack_mm=round(slack, 1)))
    res["worst_clear_mm"] = round(res["worst_clear_mm"], 1)
    res["worst_slack_mm"] = round(res["worst_slack_mm"], 1)
    res["ok"] = not res["hits"] and not res["short"]
    return res


if __name__ == "__main__":
    r = check(verbose=True)
    print({k: v for k, v in r.items() if k not in ("hits", "short")})
    for h in r["hits"][:40]:
        print("HIT", h)
    for s in r["short"][:20]:
        print("SHORT", s)
