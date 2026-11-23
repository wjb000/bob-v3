"""Joint-range clearance sweep for the left arm (the right arm is its mirror).

Each arm joint is swept through its full range from several base poses, plus random whole-arm
samples. Objects: per arm link the structure (every non-cover item merged) and each cover on its
own; the torso + head as one static body; the base as another (lift at 0, the worst case).
Pairs that touch at every pose (mated parts at a joint) are reported once and not counted.
usage: arm_sweep.py scene.json [--json out.json] [--n N]"""
import json, sys, itertools, numpy as np, trimesh, fcl
from pathlib import Path
args = sys.argv[1:]
scene = Path(args[0])
out = args[args.index("--json") + 1] if "--json" in args else None
N = int(args[args.index("--n") + 1]) if "--n" in args else 800
s = json.loads(scene.read_text())
J = {j["name"]: j for j in s["joints"]}
chain = ["l_shoulder_pitch", "l_shoulder_roll", "l_upper_arm_yaw", "l_elbow", "l_wrist_pitch", "l_wrist_roll"]
arm_links = ["l_link%d" % i for i in range(1, 9)]
pdir = scene.parent / "placed"

def bvh(m):
    g = fcl.BVHModel(); g.beginModel(len(m.vertices), len(m.faces)); g.addSubModel(m.vertices, m.faces); g.endModel(); return g

groups = {}
for it in s["items"]:
    if not it.get("file"): continue
    L = it["link"]
    if L in arm_links:
        key = (it["name"], L) if "cover" in it["name"] else ("struct:" + L, L)
    elif L in ("lift", "head_pan", "head_tilt"):
        key = ("torso/head", None)
    elif L == "base" and it["kind"] == "print" and "--base" in args:
        key = ("base", None)
    else:
        continue
    groups.setdefault(key, []).append(trimesh.load_mesh(pdir / it["file"]))
objs = [(n, L, bvh(trimesh.util.concatenate(ms))) for (n, L), ms in groups.items()]
print("objects:", [o[0] for o in objs])

def rot(axis, a):
    return trimesh.transformations.rotation_matrix(a, axis)

def fk(q):
    T = {}; cur = np.eye(4)
    for n in chain:
        j = J[n]; A = np.array(j["anchor"], float)
        M = trimesh.transformations.translation_matrix(A) @ rot(j["axis"], q.get(n, 0.0)) @ trimesh.transformations.translation_matrix(-A)
        cur = cur @ M; T[j["child"]] = cur.copy()
    T["l_link7"] = T["l_link8"] = T["l_link6"]
    return T

req = fcl.CollisionRequest()
def hits(q):
    T = fk(q); I = np.eye(4); out = set()
    cos = [(n, fcl.CollisionObject(g, fcl.Transform(T[L][:3, :3], T[L][:3, 3]) if L else fcl.Transform())) for n, L, g in objs]
    link = {n: L for n, L, _ in objs}
    for (n1, o1), (n2, o2) in itertools.combinations(cos, 2):
        if link[n1] is not None and link[n1] == link[n2]: continue
        if link[n1] is None and link[n2] is None: continue
        if {link[n1], link[n2]} == {"l_link7", "l_link8"}: continue
        if fcl.collide(o1, o2, req, fcl.CollisionResult()):
            out.add(tuple(sorted((n1, n2))))
    return out

lim = {n: J[n]["range"] for n in chain}
zero = {}
mated = hits(zero)
print("touching at the zero pose (mated or pre-existing):", sorted(mated))
bases = {"hanging": {}, "forward": dict(l_shoulder_pitch=-1.57), "forward+bent": dict(l_shoulder_pitch=-1.57, l_elbow=-1.2),
         "out+bent": dict(l_shoulder_roll=0.8, l_elbow=-1.0)}
STEPS = 47
sweep = {}
pair_stats = {}
onset = {}
for bn, b in bases.items():
    for n in chain:
        lo, hi = lim[n]
        angs = np.linspace(lo, hi, STEPS)
        free = []
        for a in angs:
            q = dict(b); q[n] = float(a)
            h = hits(q) - mated
            free.append(len(h) == 0)
            for p in h:
                pair_stats.setdefault(" | ".join(p), set()).add(f"{bn}:{n}")
                onset.setdefault(" | ".join(p), {}).setdefault(f"{bn}:{n}", []).append(round(float(a), 3))
        # free interval around the base value
        i0 = int(np.argmin(abs(angs - b.get(n, 0.0))))
        if not free[i0]:
            sweep[f"{bn}:{n}"] = None
            continue
        i, k = i0, i0
        while i > 0 and free[i - 1]: i -= 1
        while k < STEPS - 1 and free[k + 1]: k += 1
        sweep[f"{bn}:{n}"] = [round(float(angs[i]), 2), round(float(angs[k]), 2), [lo, hi]]
rng = np.random.default_rng(1)
rand_hits = {}
for _ in range(N):
    q = {n: float(rng.uniform(*lim[n])) for n in chain}
    for p in hits(q) - mated:
        rand_hits[" | ".join(p)] = rand_hits.get(" | ".join(p), 0) + 1
print("\nfree range per joint sweep (from the base pose):")
for k, v in sweep.items():
    print(f"  {k:36s} {v}")
print("\npairs that touch during sweeps (nearest touching angle below / above the base value):")
for k, d in sorted(onset.items()):
    for sk, angs in sorted(d.items()):
        b0 = bases[sk.split(":")[0]].get(sk.split(":")[1], 0.0)
        lo = max([a for a in angs if a <= b0], default=None); hi = min([a for a in angs if a > b0], default=None)
        print(f"  {k:46s} {sk:34s} below {lo}  above {hi}")
print(f"\nrandom poses ({N}): pairs touching, count")
for k, v in sorted(rand_hits.items(), key=lambda x: -x[1]):
    print(f"  {v:5d} {k}")
if out:
    json.dump(dict(mated=[" | ".join(p) for p in sorted(mated)], sweep=sweep, steps=STEPS, random=N, random_hits=rand_hits,
                   sweep_pairs=onset), open(out, "w"), indent=1)
