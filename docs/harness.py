"""3D cable harness: a routed path for every wire in docs/wiring.py.

    python docs/harness.py        # route, check, write sim/harness.json, print the report

Each wire is a list of anchors: its two terminations and the openings it passes through (the base
trough and column bore, the torso, the neck, and down each arm past every joint). Between two
anchors on the same link the path is found on a 2 mm grid that keeps the wire or bundle clear of
every part. Where an anchor is on the next link, the path crosses a joint: a service loop sits on
the child link, sized so the cable never pulls tight anywhere in that joint's range. The column
umbilical stores its lift slack as the serpentine in the base trough.

Paths are polylines in each link's zero-pose CAD frame (mm, +Z up), the frame of every CAD item, so
the viewer moves each path entry with its link's matrix. See docs/harness_format.md.
sim/cables.py checks clearance and length; sim/check.py runs it as the "cables" test.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))
sys.path.insert(0, str(ROOT / "sim"))
import wiring as W  # noqa: E402
import cables as C  # noqa: E402

SCENE = json.loads((ROOT / "cad" / "scene.json").read_text())
ANCHOR = {"base": (0.0, 0.0, 0.0), **{j["child"]: tuple(j["anchor"]) for j in SCENE["joints"]}}
JOINT_OF = {j["child"]: j for j in SCENE["joints"]}
PITCH = 2.0
# Typical outside diameters (mm) of PVC hook-up wire by AWG, and of a USB cable. Design values for
# bundle sizes, not datasheet numbers.
OD = {12: 3.8, 14: 3.2, 16: 2.6, 18: 2.3, 20: 1.9, 22: 1.6, 26: 1.2, 28: 1.0}
USB_OD = 4.0
PACK = 0.6  # fill fraction of a round bundle
SKIP = {f"drag_link_{i}" for i in range(6)}  # the umbilical rides inside the drag chain


def awg(gauge: str) -> int:
    """Wire size as a number. USB cables have no gauge in wiring.py: 28 AWG is the USB 2.0 data pair."""
    for tok in gauge.replace("+", " ").split():
        if tok.isdigit():
            return int(tok)
    return 28


NCOND = {"signal": 2, "ttl": 3, "motor": 4}  # conductors in one run: UART pairs, 3-pin servo lead, stepper A/B


def wire_d2(row) -> float:
    """Sum of conductor diameters squared (mm2) for one wire row."""
    if row[2] == "usb":
        return USB_OD ** 2
    n = 4 if row[:2] == ("esp", "wheels") else NCOND.get(row[2], 1)
    return n * OD.get(awg(row[4]), 1.6) ** 2


def radius(d2: float, single: bool) -> float:
    return round(math.sqrt(d2) / 2 if single else 0.5 * math.sqrt(d2 / PACK), 1)


def A(link, x, y, z):
    return (link, float(x), float(y), float(z))


def mir(a, side):
    return a if side == "l" else (a[0].replace("l_", "r_", 1), a[1], -a[2], a[3])


# ---------------------------------------------------------------- terminations (zero-pose CAD frame, mm)
T = {
    "charge": A("base", 125, -110, 172), "batt": A("base", -88, 100, 190), "fuse": A("base", 0, -56, 158),
    "gnd": A("base", 24, -44, 156), "cont": A("base", -110, -96, 156), "estop": A("base", -122, 112, 150),
    "b12c": A("base", 0, -162, 156), "b18": A("base", 0, -132, 156), "esp": A("base", 0, -88, 156),
    "tmc": A("base", -130, -10, 156), "imu": A("base", -130, -32, 156), "lim": A("base", 13, 62, 349),
    "lidar": A("base", 116, 0, 128), "nema": A("base", 0, -30, 51),
    "wheel_l": A("base", 0, 108, 50), "wheel_r": A("base", 0, -108, 50),
    "pi": A("lift", 46, 90, 350), "pi_gpio": A("lift", -10, 76, 374), "hub": A("lift", 36, -83, 350),
    "hub_dc": A("lift", -36, -74, 350), "busl": A("lift", 56, 72, 290), "busr": A("lift", 56, -72, 290),
    # torso positions from wiring.py: the 5 V regulator beside the Pi and the two arm converters
    "b5": A("lift", -40, 84, 290), "b12a": A("lift", 0, -80, 276),
    "s3": A("head_tilt", 0, 0, 554), "audio": A("head_tilt", 20, 0, 636), "cam": A("head_tilt", 58, 0, 606),
    "eyes": A("head_tilt", 76, 0, 568), "pan": A("lift", 16, -18, 440), "tilt": A("head_pan", 16, -28, 510),
}
END_ITEMS = {"pi": "pi5", "hub": "usb_hub", "busl": "servo_bus", "busr": "servo_bus_r", "esp": "ddsm_driver", "tmc": "tmc2209",
             "imu": "imu", "lim": "limit_top", "lidar": "lidar", "nema": "lift_motor", "cont": "contactor_relay",
             "estop": "estop", "fuse": "fuse_block", "batt": "battery", "charge": "charge_socket_body", "b18": "reg_12v",
             "b12c": "reg_5v", "s3": "esp32s3_head", "audio": "mic_array", "cam": "head_cam", "eyes": "eye_plate"}

# ---------------------------------------------------------------- trunks
WINDOW = A("base", -46, 22, 100)  # outer-tube cable lane (y 14-30), above the trough tongue


def serpentine():
    """The lift slack: eight passes of the sleeve in the trough, inside the drag chain."""
    pts = [A("base", -58, 24, 104), A("base", -74, 40, 104)]
    for i in range(8):
        x = -79.0 if i // 4 == 0 else -69.0
        z = 54.0 + (i % 4) * 11.0
        y0, y1 = (36.0, 86.0) if i % 2 == 0 else (86.0, 36.0)
        pts += [A("base", x, y0, z), A("base", x, y1, z)]
    return pts


COLUMN = [*serpentine(), WINDOW, ("cross", "lift"), A("lift", -14, 18, 160), A("lift", -10, 16, 330), A("lift", 0, 0, 380),
          A("lift", 0, 0, 404)]  # bore lane past the T8 bridge, then the Ø18 hole in the cap
DOWN = [x for x in COLUMN[::-1] if x[0] == "lift"] + [("cross", "base")] + [x for x in COLUMN[::-1] if x[0] == "base"]
SERP_LEN = float(sum(np.linalg.norm(np.subtract(u[1:], v[1:])) for u, v in zip(serpentine()[:-1], serpentine()[1:])))
NECK = [A("lift", -24, 0, 420), A("lift", -24, 0, 455), ("cross", "head_pan"), A("head_pan", -24, 0, 470),
        A("head_pan", -14, -34, 500), A("head_pan", 5, -34, 510), ("cross", "head_tilt"), A("head_tilt", 5, -38, 512),
        A("head_tilt", 0, -20, 530)]


def arm(side):
    """Torso to the palm, left arm in the CAD frame (the right is the mirror)."""
    a = [A("lift", 20, 100, 436), ("cross", "l_link1"), A("l_link1", 14, 132, 434), A("l_link1", -12, 157, 384),
         ("cross", "l_link2"), A("l_link2", -26, 157, 384), A("l_link2", -16, 176, 300),
         ("cross", "l_link3"), A("l_link3", -14, 176, 286), A("l_link3", -14, 126, 200), A("l_link3", 9, 126, 172),
         ("cross", "l_link4"), A("l_link4", 9, 122, 158), A("l_link4", 9, 145, 110), A("l_link4", 9, 157, 92),
         A("l_link4", 9, 157, 60), A("l_link4", 9, 136, -20), A("l_link4", 9, 134, -42),
         ("cross", "l_link5"), A("l_link5", 9, 128, -42), A("l_link5", 9, 136, -95),
         ("cross", "l_link6"), A("l_link6", 9, 136, -132)]
    if side == "l":
        return a
    return [("cross", c[1].replace("l_", "r_")) if c[0] == "cross" else mir(c, side) for c in a]


ARM_END = {"wc": A("l_link6", -12, 157, -176), "bus": A("l_link6", 24, 140, -150)}


def anchors_for(row):
    a, b, kind = row[0], row[1], row[2]
    t = lambda n: T[n]  # noqa: E731
    up = lambda x, y: [t(x), *COLUMN, t(y)]  # noqa: E731  base device to the torso
    key = (a, b)
    if key in (("fuse", "b5"), ("cont", "b12a"), ("b12c", "hub"), ("gnd", "b5"), ("gnd", "b12a")):
        end = T["hub_dc"] if b == "hub" else t(b)
        return [t(a), *COLUMN, end], "column"
    if key == ("pi", "esp"):
        return [t("pi"), *DOWN, t("esp")], "column"
    if key == ("hub", "lidar"):
        return [t("hub"), *DOWN, t("lidar")], "column"
    if key in (("pi", "s3"), ("pi", "audio"), ("hub", "cam")):
        dst = {"s3": "s3", "audio": "audio", "cam": "cam"}[b]
        return [t(a), *NECK, t(dst)], "neck"
    if key == ("busl", "head"):
        return [t("busl"), t("pan"), A("lift", -24, 0, 420), *NECK[1:], t("tilt")], "neck"
    if key in (("hub", "wcl"), ("hub", "wcr"), ("busl", "stl"), ("busr", "str")):
        side = "l" if b in ("wcl", "stl") else "r"
        tail = mir(ARM_END["wc" if a == "hub" else "bus"], side)
        return [t(a), *arm(side), tail], f"arm_{side}"
    if key == ("esp", "wheels"):
        return [t("esp"), A("base", 30, -60, 60), A("base", 30, 60, 60), t("wheel_l"), A("base", 30, 60, 60),
                A("base", 30, -60, 60), t("wheel_r")], None
    if key == ("b5", "pi"):
        return [t("b5"), T["pi_gpio"]], None
    if key in (("pi", "busl"), ("pi", "busr")):
        return [T["pi_gpio"], t(b)], None
    if key == ("b18", "tmc"):
        return [t("b18"), t("tmc")], None
    return [t(a), t(b)], None


# ---------------------------------------------------------------- grid router
class Router:
    def __init__(self, parts):
        self.parts = parts
        self.cache = {}

    def leg(self, link, p0, p1, need):
        """Clear polyline from p0 to p1 on one link (zero-pose frame)."""
        from skimage.graph import MCP_Geometric
        from scipy import ndimage
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        lo = np.minimum(p0, p1) - 40.0
        hi = np.maximum(p0, p1) + 40.0
        shape = np.ceil((hi - lo) / PITCH).astype(int) + 1
        occ = np.zeros(shape, bool)
        group = self._group(link)
        for k, (tree, P, N, names) in self.parts.tree.items():
            if k not in group:
                continue
            m = np.all((P >= lo - 2) & (P <= hi + 2), axis=1)
            idx = np.round((P[m] - lo) / PITCH).astype(int)
            idx = idx[np.all((idx >= 0) & (idx < shape), axis=1)]
            occ[tuple(idx.T)] = True
        clear = ndimage.distance_transform_edt(~occ) * PITCH
        cost = 1.0 + 400.0 * (clear < need) + 3.0 * np.clip((need + 4 - clear) / (need + 4), 0, 1)
        i0 = tuple(np.clip(np.round((p0 - lo) / PITCH).astype(int), 0, shape - 1))
        i1 = tuple(np.clip(np.round((p1 - lo) / PITCH).astype(int), 0, shape - 1))
        mcp = MCP_Geometric(cost)
        mcp.find_costs([i0], [i1])
        path = np.array(mcp.traceback(i1), float) * PITCH + lo
        ok = lambda a, b: self._clear_line(clear, lo, a, b, need)  # noqa: E731
        out, i = [p0], 0
        pts = [p0, *path[1:-1], p1]
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not ok(pts[i], pts[j]):
                j -= 1
            out.append(pts[j])
            i = j
        return [np.round(p, 1) for p in out]

    @staticmethod
    def _clear_line(clear, lo, a, b, need):
        n = max(2, int(np.linalg.norm(b - a) / 1.0))
        t = np.linspace(0, 1, n)[:, None]
        q = np.round((a + (b - a) * t - lo) / PITCH).astype(int)
        q = np.clip(q, 0, np.array(clear.shape) - 1)
        c = clear[tuple(q.T)]
        # the ends sit at terminations; only the middle has to stay clear
        k = max(1, int(n * 0.08))
        return bool(np.all(c[k:-k] >= need)) if n > 2 * k else True

    @staticmethod
    def _group(link):
        if link.startswith(("l_", "r_")):
            return {k for k in ANCHOR if k.startswith(link[:2])} | {"lift"}
        return {k for k in ANCHOR if not k.startswith(("l_", "r_"))}


# ---------------------------------------------------------------- build
_SNAP = {}


def snap(parts, a, reach):
    """Move an anchor up to `reach` mm to the clearest spot nearby (the CAD openings are tight)."""
    if a in _SNAP:
        return _SNAP[a]
    c = np.array(a[1:], float)
    g = np.mgrid[-reach:reach + 0.1:2, -reach:reach + 0.1:2, -reach:reach + 0.1:2].reshape(3, -1).T + c
    d, _ = parts.clearance({k: g for k in parts.tree if k in Router._group(a[0])})
    score = np.minimum(d, 12.0) - 0.08 * np.linalg.norm(g - c, axis=1)
    p = g[int(np.argmax(score))]
    _SNAP[a] = (a[0], *map(float, np.round(p, 1)))
    return _SNAP[a]


def _loop(child, c, parts, need, extra):
    """A U-shaped service loop at c on the child link, extra mm long, turned to the clearest side."""
    j = JOINT_OF.get(child)
    axis = np.asarray(j["axis"], float) if j else np.array([0, 0, 1.0])
    axis /= np.linalg.norm(axis)
    c = np.asarray(c, float)
    h = max(6.0, extra / 2.0)
    best = None
    for d in (axis, -axis, *np.eye(3), *-np.eye(3)):
        d = np.asarray(d, float)
        s = np.cross(d, axis if abs(np.dot(d, axis)) < 0.9 else np.array([1.0, 0, 0]) if abs(axis[0]) < 0.9 else np.array([0, 1.0, 0]))
        s = s / np.linalg.norm(s) * 4.0
        pts = [c, c + d * h + s, c + d * h - s, c]
        P = C._dense(np.array(pts), 1.0)
        dd, _ = parts.clearance({k: P for k in parts.tree if k in Router._group(child)})
        score = float(np.min(dd[2:-2])) if len(dd) > 4 else 0
        if best is None or score > best[0]:
            best = (score, pts)
    return [np.round(p, 1) for p in best[1]]


def build(verbose=True):
    items = SCENE["items"]
    parts = C.Parts(items, {k: np.asarray(v) for k, v in ANCHOR.items()}, assets=ROOT / "sim" / "assets", skip=SKIP)
    router = Router(parts)
    rows = W.WIRES
    groups = {}
    plan = []
    for row in rows:
        anchors, bundle = anchors_for(row)
        n = len(anchors)
        anchors = [x if x[0] == "cross" else snap(parts, x, 4.0 if i in (0, n - 1) else 8.0) for i, x in enumerate(anchors)]
        plan.append((row, anchors, bundle))
        if bundle:
            groups.setdefault(bundle, []).append(row)
    brad = {g: radius(sum(wire_d2(r) for r in rs), False) for g, rs in groups.items()}
    data_wires, hj = [], []
    first = set()
    elec = W.elec()
    cache = {}
    for row, anchors, bundle in plan:
        a, b = row[0], row[1]
        r = brad[bundle] if bundle else radius(wire_d2(row), NCOND.get(row[2], 1) == 1 and row[2] != "usb")
        need = r + C.MARGIN
        path, crossings = [], []
        cur = None  # (link, pts)
        prev = None
        pending_cross = False
        for x in anchors:
            if x[0] == "cross":
                pending_cross = True
                continue
            link, p = x[0], np.array(x[1:])
            if cur is None:
                cur = [link, [p]]
            elif link == cur[0] and not pending_cross:
                key = (link, tuple(prev), tuple(p), round(need, 1))
                if key not in cache:
                    cache[key] = router.leg(link, prev, p, need + 1.5) if link != "base" or not _in_trough(prev, p) else [prev, p]
                cur[1].extend(cache[key][1:])
            else:  # joint or lift crossing: leave the parent here, service loop on the child
                path.append(dict(item=cur[0], pts=cur[1]))
                parent_end = (cur[0], *map(float, cur[1][-1]))
                chord0 = _chord(parent_end, (link, *p))
                worst = max(_chord(parent_end, (link, *p), pose) for pose in C.poses(_hdata(), sweep=True).values())
                if {link, cur[0]} == {"lift", "base"}:  # column: the serpentine in the trough is the slack
                    cable = chord0 + SERP_LEN
                    jn = "lift"
                else:
                    extra = max(0.0, worst - chord0) + 12.0
                    loop = _loop(link, p, parts, need, extra)
                    path.append(dict(item=link, pts=loop, loop=True))
                    cable = chord0 + 2 * (np.linalg.norm(loop[1] - loop[0]))
                    jn = JOINT_OF[link]["name"]
                if True:
                    crossings.append(dict(joint=jn, **{"from": list(parent_end)}, to=[link, *map(float, p)], cable_mm=round(cable, 1)))
                cur = [link, [p]]
                pending_cross = False
            prev = p
        path.append(dict(item=cur[0], pts=cur[1]))
        for e in path:
            e["pts"] = [[round(float(v), 1) for v in q] for q in e["pts"]]
        path = [e for e in path if len(e["pts"]) >= 2 or e is path[0] or e is path[-1]]
        L = _length(path, crossings)
        wid = f"{a}-{b}"
        ew = dict(id=wid, bundle=bundle, radius_mm=r, path=path, route_mm=int(round(L * 1.08)))
        data_wires.append(ew)
        hj.append(dict(id=wid, bundle=bundle, radius_mm=r, route_mm=ew["route_mm"], path=path, crossings=crossings,
                       ends_l=[list(anchors[0]), list(anchors[-1])],
                       touch=[END_ITEMS[n] for n in (a, b) if n in END_ITEMS]))
    hdata = _hdata()
    hdata.update(wires=hj, skip=sorted(SKIP))
    (ROOT / "sim" / "harness.json").write_text(json.dumps(hdata, separators=(",", ":")) + "\n")
    res = C.check(hdata, parts)
    if verbose:
        _report(data_wires, res)
    return data_wires, res


def _in_trough(p, q):
    return all(-90 <= v[0] <= -44 and 10 <= v[1] <= 96 and v[2] <= 104 for v in (p, q))


_HD = None


def _hdata():
    global _HD
    if _HD is None:
        js = [dict(name=j["name"], kind=j["kind"], parent=j["parent"], child=j["child"], anchor=j["anchor"], axis=j["axis"],
                   range=j["range"], **({"mimic": j["mimic"], "mimic_coef": j["mimic_coef"]} if j.get("mimic") else {}))
              for j in SCENE["joints"]]
        _HD = dict(anchors={k: list(v) for k, v in ANCHOR.items()}, joints=js, poses=SCENE["poses"],
                   lift_travel=SCENE["dims"]["lift_travel"],
                   items=[dict(name=it["name"], file=it["file"], link=it["link"]) for it in SCENE["items"]])
    return _HD


_TF = {}


def _chord(pa, pb, pose=None):
    key = json.dumps(pose, sort_keys=True)
    if key not in _TF:
        _TF[key] = C.link_transforms(_hdata()["joints"], pose or {})
    T = _TF[key]
    a = T[pa[0]] @ np.array([*pa[1:], 1.0])
    b = T[pb[0]] @ np.array([*pb[1:], 1.0])
    return float(np.linalg.norm(a[:3] - b[:3]))


def _length(path, crossings):
    """Cut length before the 8 percent: every fixed run and loop plus the cable across each crossing."""
    L = sum(np.linalg.norm(np.subtract(u, v)) for e in path for u, v in zip(e["pts"][:-1], e["pts"][1:]) if not e.get("loop"))
    L += sum(c["cable_mm"] for c in crossings)
    L += sum(2 * np.linalg.norm(np.subtract(e["pts"][1], e["pts"][0])) for e in path if e.get("loop"))
    return L


def _report(wires, res):
    rec = {f"{r[0]}-{r[1]}": x for r, x in zip(W.WIRES, W.wire_records())}
    print(f"{'wire':14} {'bundle':8} {'r mm':>5} {'route':>6} {'wiring.py':>9}")
    for w in wires:
        print(f"{w['id']:14} {str(w['bundle']):8} {w['radius_mm']:5.1f} {w['route_mm']:6d} {str(rec[w['id']]['len_mm']):>9}")
    print({k: v for k, v in res.items() if k not in ("hits", "short")})
    for h in res["hits"][:60]:
        print("HIT", h)
    for s in res["short"][:30]:
        print("SHORT", s)


if __name__ == "__main__":
    _, r = build()
    sys.exit(0 if r["ok"] else 1)
