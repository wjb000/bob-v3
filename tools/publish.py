#!/usr/bin/env python3
"""Package Bob v3 for the website and for download.

    .venv/bin/python tools/publish.py ~/Desktop/site-repo/bob-v3

Writes into the target folder:
  bob_v3.glb               every part and envelope, robot frame, mm, one node per item (viewer)
  data.json                scene (links, joints, poses), print list, BOM, sim checks (viewer + tables)
  stl/*.stl                print-ready STLs, one per unique part
  bob-v3-print-files.zip   the same STLs plus PRINT.md
  bob-v3-sim.zip           MuJoCo model, meshes, gym env, expert, training scripts
  img/*                    renders and the pick GIF
and fills the tables in index.html between <!--{{NAME}}--> markers.
"""

from __future__ import annotations

import html
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))
from bom import BOM  # noqa: E402
import wiring as WIRING  # noqa: E402

NW, NH, CW, RH, PAD = 150, 46, 176, 64, 16


def wiring_svg() -> str:
    """Lay the nodes out on the grid in docs/wiring.py and route every wire on its own lane, with right angles."""
    NW_, NH_, CW_, RH_, P_ = 172, 42, 232, 58, 24
    N = WIRING.NODES
    xy = {k: (P_ + c * CW_, P_ + 34 + r * RH_) for k, (_, _, c, r, _) in N.items()}
    cols = max(v[2] for v in N.values()) + 1
    rows = max(v[3] for v in N.values()) + 1
    W, H = P_ * 2 + (cols - 1) * CW_ + NW_, P_ + 34 + rows * RH_ + 64
    rects = {k: (x, y, x + NW_, y + NH_) for k, (x, y) in xy.items()}
    # which side of each node every wire end uses
    ends = []
    for i, (a, b, *_ ) in enumerate(WIRING.WIRES):
        ca, cb = N[a][2], N[b][2]
        if ca == cb:
            ends.append(((a, "r"), (b, "r")))
        elif ca < cb:
            ends.append(((a, "r"), (b, "l")))
        else:
            ends.append(((a, "l"), (b, "r")))
    side = {}
    for i, ((a, sa), (b, sb)) in enumerate(ends):
        side.setdefault((a, sa), []).append((xy[b][1], i, 0))
        side.setdefault((b, sb), []).append((xy[a][1], i, 1))
    port = {}
    for (k, sd), lst in side.items():
        lst.sort()
        for j, (_, i, e) in enumerate(lst):
            y = xy[k][1] + NH_ * (j + 1) / (len(lst) + 1)
            x = xy[k][0] + (NW_ if sd == "r" else 0)
            port[(i, e)] = (x, y)
    gapn, rown = {}, {}

    def lane(store, key, base, step=6):
        k = store.get(key, 0)
        store[key] = k + 1
        return base + ((k + 1) // 2) * step * (1 if k % 2 else -1)

    def gx(g):  # centre of the gap right of column g
        return P_ + g * CW_ + NW_ + (CW_ - NW_) / 2

    def ry(r):  # centre of the gap above row r
        return P_ + 34 + r * RH_ - (RH_ - NH_) / 2

    def clear(x1, x2, y, skip):
        lo, hi = sorted((x1, x2))
        return not any(k not in skip and r[0] - 4 < hi and r[2] + 4 > lo and r[1] - 3 < y < r[3] + 3 for k, r in rects.items())

    paths = []
    for i, (a, b, kind, what, wire, conn, fuse) in enumerate(WIRING.WIRES):
        (xa, ya), (xb, yb) = port[(i, 0)], port[(i, 1)]
        ca, cb = N[a][2], N[b][2]
        sk = {a, b}
        if ca == cb:
            x = lane(gapn, ca, gx(ca) - 12)
            pts = [(xa, ya), (x, ya), (x, yb), (xb, yb)]
        else:
            d = 1 if cb > ca else -1
            ga, gb = (ca if d > 0 else ca - 1), (cb - 1 if d > 0 else cb)
            if clear(xa, gx(gb), ya, sk):
                x = lane(gapn, gb, gx(gb))
                pts = [(xa, ya), (x, ya), (x, yb), (xb, yb)]
            elif clear(gx(ga), xb, yb, sk):
                x = lane(gapn, ga, gx(ga))
                pts = [(xa, ya), (x, ya), (x, yb), (xb, yb)]
            else:
                rb = N[b][3]
                y = lane(rown, rb, ry(rb), 5)
                x1, x2 = lane(gapn, ga, gx(ga)), lane(gapn, gb, gx(gb))
                pts = [(xa, ya), (x1, ya), (x1, y), (x2, y), (x2, yb), (xb, yb)]
        dd = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        col = WIRING.COLORS[kind]
        dash = ' stroke-dasharray="5 4"' if kind == "estop" else ""
        rec = WIRING.wire_records()[i]
        length = f" {rec['len_mm']} mm." if rec["len_mm"] else ""
        tip = html.escape(f"{N[a][0]} → {N[b][0]}: {what}. {wire} {conn} {fuse}.{length}".strip())
        lab = ""
        if kind.startswith("power") and wire:
            seg = max(zip(pts, pts[1:]), key=lambda s2: abs(s2[1][0] - s2[0][0]))
            if abs(seg[1][0] - seg[0][0]) > 60:
                lab = f'<text class="wl" x="{(seg[0][0] + seg[1][0]) / 2:.0f}" y="{seg[0][1] - 4:.0f}" fill="{col}">{html.escape(wire)}</text>'
        paths.append(f'<g class="wg" data-kind="{kind}" data-a="{a}" data-b="{b}"><polyline class="w" points="{dd}" stroke="{col}"{dash}><title>{tip}</title></polyline>{lab}'
                     f'<circle cx="{xa:.0f}" cy="{ya:.0f}" r="2.5" fill="{col}"/><circle cx="{xb:.0f}" cy="{yb:.0f}" r="2.5" fill="{col}"/></g>')
    nodes = []
    feed = {}
    for a, b, kind, *_ in WIRING.WIRES:
        feed.setdefault(b, kind)
        feed.setdefault(a, kind)
    for k, (label, sub, c, r, item) in N.items():
        x, y = xy[k]
        acc = WIRING.COLORS[feed.get(k, "usb")]
        nodes.append(f'<g class="wn" data-node="{k}" tabindex="0"><rect x="{x}" y="{y}" width="{NW_}" height="{NH_}" rx="8"/>'
                     f'<rect class="acc" x="{x}" y="{y + 8}" width="3" height="{NH_ - 16}" rx="1.5" fill="{acc}"/>'
                     f'<text class="t" x="{x + NW_ / 2}" y="{y + 18}">{html.escape(label)}</text>'
                     f'<text class="ts" x="{x + NW_ / 2}" y="{y + 33}">{html.escape(sub)}</text></g>')
    heads = ["Power in", "Safety", "Regulators", "Computer", "Controllers", "Devices", "Sensors"]
    hdr = "".join(f'<text class="hd" x="{P_ + i * CW_ + NW_ / 2}" y="{P_ + 6}">{h.upper()}</text>' for i, h in enumerate(heads[:cols]))
    lx = P_
    legend = []
    for k, lab in WIRING.LABELS.items():
        legend.append(f'<g><line x1="{lx}" y1="{H - 18}" x2="{lx + 22}" y2="{H - 18}" stroke="{WIRING.COLORS[k]}" stroke-width="3"'
                      + (' stroke-dasharray="5 4"' if k == "estop" else "") + f'/><text class="lg" x="{lx + 28}" y="{H - 14}">{lab}</text></g>')
        lx += 28 + 8 * len(lab) + 26
    zones = []
    for c0, c1, name in ((0, 2, "POWER"), (3, 4, "CONTROL"), (5, 6, "DEVICES")):
        x0, x1 = P_ + c0 * CW_ - 10, P_ + c1 * CW_ + NW_ + 10
        zones.append(f'<rect class="zone" x="{x0}" y="{P_ + 16}" width="{x1 - x0}" height="{rows * RH_ + 26}" rx="12"/>'
                     f'<text class="zt" x="{x0 + 12}" y="{P_ + 16 + rows * RH_ + 18}">{name}</text>')
    legend = [g.replace("<g>", f'<g class="lgi" data-kind="{k}" tabindex="0">', 1) for g, k in zip(legend, WIRING.LABELS)]
    return (f'<svg class="wiresvg" viewBox="0 0 {W} {H}" role="img" aria-label="Bob v3 wiring: every power, bus and signal wire">'
            f'{"".join(zones)}{hdr}<g class="ws">{"".join(paths)}</g><g>{"".join(nodes)}</g>{"".join(legend)}</svg>')


def wiring_table() -> str:
    rows = ["<tr><th></th><th>From</th><th>To</th><th>What</th><th>Wire</th><th>Length</th><th>Connector</th><th>Fuse</th></tr>"]
    for (a, b, kind, what, wire, conn, fuse), rec in zip(WIRING.WIRES, WIRING.wire_records()):
        rows.append(f'<tr><td><i class="sw" style="background:{WIRING.COLORS[kind]}"></i></td><td>{html.escape(WIRING.NODES[a][0])}</td>'
                    f'<td>{html.escape(WIRING.NODES[b][0])}</td><td>{html.escape(what)}</td><td>{html.escape(wire)}</td>'
                    f'<td>{rec["len_mm"]} mm</td><td>{html.escape(conn)}</td><td>{html.escape(fuse)}</td></tr>')
    return "\n".join(rows)

COLORS = {"shell": [22, 23, 26], "dark": [13, 13, 14], "frame": [41, 43, 48], "accent": [0, 127, 255],
          "actuator": [52, 52, 58], "electronics": [40, 110, 70], "battery": [90, 140, 50], "metal": [190, 192, 198],
          "wheel": [24, 24, 24]}


def bom_rows():
    rows, total, have = [], 0.0, 0.0
    for sec, item, qty, each, link, note, owned in BOM:
        line = qty * each
        total += line
        if owned:
            have += line
        rows.append(dict(section=sec, item=item, qty=qty, each=each, line=round(line, 2), link=link, note=note, have=owned))
    return rows, round(total, 2), round(have, 2)


def build_glb(scene, out):
    s = trimesh.Scene()
    for it in scene["items"]:
        m = trimesh.load_mesh(ROOT / "cad" / "viewer" / it["file"])
        rgb = COLORS.get(it["color"], [180, 180, 180])
        m.visual = trimesh.visual.ColorVisuals(m, face_colors=np.tile([*rgb, 255], (len(m.faces), 1)))
        s.add_geometry(m, node_name=it["name"], geom_name=it["name"])
    out.write_bytes(s.export(file_type="glb"))


def fill(template: str, name: str, body: str) -> str:
    a, b = f"<!--{{{{{name}}}}}-->", f"<!--{{{{/{name}}}}}-->"
    i, j = template.index(a), template.index(b)
    return template[: i + len(a)] + "\n" + body + "\n" + template[j:]


def money(v):
    return f"${v:,.0f}" if v >= 10 else f"${v:,.2f}"



def us_units(t: str) -> str:
    """Show the robot's numbers in US units: lb, in, ft, lb·ft, lbf, mph. Part names (M3, 12 mm rod, TR8) stay as sold."""
    import re as R

    def num(v, d=1):
        x = f"{v:,.{d}f}"
        return x.rstrip("0").rstrip(".") if "." in x else x

    def ftin(m):
        inch = m / 0.0254
        if inch < 24:
            return f"{num(inch)} in"
        ft, i = divmod(round(inch), 12)
        return f"{ft} ft {i} in" if i else f"{ft} ft"

    def rng(f, unit_out=None):
        def g(mo):
            a = mo.group(1).replace(",", "")
            b = mo.group(2)
            if b:
                return f"{f(float(a), bare=True)}–{f(float(b.replace(',', '')))}"
            return f(float(a))
        return g

    def kg(v, bare=False):
        return num(v * 2.20462, 1) + ("" if bare else " lb")

    def nm(v, bare=False):
        return num(v * 0.73756, 1) + ("" if bare else " lb·ft")

    def newton(v, bare=False):
        return num(v * 0.224809, 0 if v > 40 else 1) + ("" if bare else " lbf")

    def ms(v, bare=False):
        return num(v * 2.23694, 1) + ("" if bare else " mph")

    def mms(v, bare=False):
        return num(v / 25.4, 1) + ("" if bare else " in/s")

    def mss(v, bare=False):
        return num(v * 3.28084, 0) + ("" if bare else " ft/s²")

    def mm(v, bare=False):
        i = v / 25.4
        return (num(i, 2 if i < 1 else 1)) + ("" if bare else " in")

    def m(v, bare=False):
        return (num(v / 0.0254, 1) if bare and v < 0.6 else ftin(v) if not bare else ftin(v)) if not bare else ftin(v).replace(" in", "").replace(" ft", " ft") if False else ftin(v)

    N_ = r"(\d[\d,]*(?:\.\d+)?)(?:\s?[–-]\s?(\d[\d,]*(?:\.\d+)?))?"
    t = R.sub(N_ + r"\s?N·m\b", rng(nm), t)
    t = R.sub(N_ + r"\s?kg\b", rng(kg), t)
    t = R.sub(N_ + r"\s?m/s²", rng(mss), t)
    t = R.sub(N_ + r"\s?mm/s\b", rng(mms), t)
    t = R.sub(N_ + r"\s?m/s\b", rng(ms), t)
    t = R.sub(N_ + r"\s?N\b(?!·)", rng(newton), t)

    def mm_sub(mo):
        a, b = mo.group(1), mo.group(2)
        if not b and a in ("12", "5", "8", "22", "48"):  # rod, shaft, bearing and motor sizes are part names
            return mo.group(0)
        if b:
            return f"{mm(float(a.replace(',', '')), True)}–{mm(float(b.replace(',', '')))}"
        return mm(float(a.replace(",", "")))
    t = R.sub(N_ + r"\s?mm\b(?!/)", mm_sub, t)

    def m_sub(mo):
        a, b = mo.group(1), mo.group(2)
        if b:
            return f"{ftin(float(a))} – {ftin(float(b))}"
        return ftin(float(a.replace(",", "")))
    t = R.sub(N_ + r"\sm\b(?![/²·])", m_sub, t)
    return t

def main():
    dst = Path(sys.argv[1]).expanduser().resolve()
    dst.mkdir(parents=True, exist_ok=True)
    scene = json.loads((ROOT / "cad" / "scene.json").read_text())
    manifest = json.loads((ROOT / "cad" / "reports" / "manifest.json").read_text())
    checks = json.loads((ROOT / "sim" / "reports" / "check.json").read_text())
    rows, total, have = bom_rows()

    print("glb")
    build_glb(scene, dst / "bob_v3.glb")

    print("stl")
    (dst / "stl").mkdir(exist_ok=True)
    for f in (dst / "stl").glob("*.stl"):
        f.unlink()
    for p in manifest["parts"]:
        shutil.copy(ROOT / "cad" / "stl" / f"{p['name']}.stl", dst / "stl" / f"{p['name']}.stl")
    with zipfile.ZipFile(dst / "bob-v3-print-files.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in manifest["parts"]:
            z.write(ROOT / "cad" / "stl" / f"{p['name']}.stl", f"bob-v3/stl/{p['name']}.stl")
        for doc in ("PRINT.md", "BOM.md", "ASSEMBLY.md", "VERIFY.md"):
            if (ROOT / doc).exists():
                z.write(ROOT / doc, f"bob-v3/{doc}")
    print("sim zip")
    with zipfile.ZipFile(dst / "bob-v3-sim.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in ["bob_v3.xml", "bob_env.py", "expert.py", "train.py", "record_demos.py", "check.py", "interlock.py", "README.md"]:
            if (ROOT / "sim" / f).exists():
                z.write(ROOT / "sim" / f, f"bob-v3-sim/{f}")
        for f in sorted((ROOT / "sim" / "assets").glob("*.stl")):
            z.write(f, f"bob-v3-sim/assets/{f.name}")
        z.write(ROOT / "requirements-sim.txt", "bob-v3-sim/requirements.txt")
    shutil.copy(ROOT / "docs" / "sim_tasks.json", dst / "sim_tasks.json")
    print("img")
    (dst / "img").mkdir(exist_ok=True)
    for f in (ROOT / "docs" / "img").glob("*"):
        shutil.copy(f, dst / "img" / f.name)

    # reach-limit interlock for the viewer: the rule from sim/interlock.py and each hand's tool point
    # in the zero pose (the viewer's link matrices move zero-pose points)
    import mujoco
    sys.path.insert(0, str(ROOT / "sim"))
    import interlock as IL
    mm = mujoco.MjModel.from_xml_path(str(ROOT / "sim" / "bob_v3.xml"))
    md = mujoco.MjData(mm)
    mujoco.mj_kinematics(mm, md)
    b0 = md.xpos[mm.body("base").id]
    interlock = dict(lift_free_m=IL.LIFT_FREE_M, x_cap_low_mm=IL.X_CAP_LOW_M * 1000, x_cap_high_mm=IL.X_CAP_HIGH_M * 1000,
                     x_rear_mm=IL.X_REAR_M * 1000, z_low_mm=IL.Z_CAP_LOW_M * 1000, z_high_mm=IL.Z_CAP_HIGH_M * 1000,
                     tip_mm={s: [round(float(v) * 1000, 1) for v in md.site_xpos[mm.site(f"tcp_{s}").id] - b0] for s in "lr"})
    data = dict(interlock=interlock, scene=dict(joints=scene["joints"], poses=scene["poses"], links=scene["links"], dims=scene["dims"],
                           items=[{k: it.get(k) for k in ("name", "link", "group", "kind", "color", "material", "mass_g", "print", "note", "bom")}
                                  for it in scene["items"]]),
                parts=manifest["parts"], hardware=manifest["hardware"], stability=manifest["stability"],
                bom=dict(rows=rows, total=total, have=have), checks=checks,
                wiring=dict(nodes={k: dict(label=v[0], item=v[4]) for k, v in WIRING.NODES.items()},
                            wires=[dict(a=a, b=b, kind=k, what=w, gauge=g, conn=c, fuse=f,
                                        len_mm=rec["len_mm"], path=rec["path"])
                                   for (a, b, k, w, g, c, f), rec in zip(WIRING.WIRES, WIRING.wire_records())],
                            colors=WIRING.COLORS),
                mass_kg=round(manifest["robot_mass_g"] / 1000, 1), print_kg=round(manifest["print_mass_g"] / 1000, 2))
    # The site caches .glb and images for a year (vercel.json), so every URL carries a content hash.
    import hashlib

    def ver(path):
        return hashlib.sha1(path.read_bytes()).hexdigest()[:10]

    data["glb"] = f"bob_v3.glb?v={ver(dst / 'bob_v3.glb')}"
    (dst / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    vjs = dst / "viewer.js"
    if vjs.exists():
        import re as _re
        vtxt = vjs.read_text()
        vtxt2, n = _re.subn(r"data\.json(?:\?v=[0-9a-f]+)?", f"data.json?v={ver(dst / 'data.json')}", vtxt, count=1)
        if n:
            vjs.write_text(vtxt2)

    # ---- tables in index.html
    page = dst / "index.html"
    t = page.read_text()
    # BOM
    out, sec = [], None
    for r in rows:
        if r["section"] != sec:
            sec = r["section"]
            sub = sum(x["line"] for x in rows if x["section"] == sec)
            out.append(f'<tr class="grp"><td colspan="3">{html.escape(sec)}</td><td class="n">{money(sub)}</td></tr>')
        tag = ' <span class="have">have</span>' if r["have"] else ""
        note = f'<span class="d">{html.escape(r["note"])}</span>' if r["note"] else ""
        out.append(f'<tr><td><a href="{html.escape(r["link"])}" rel="noopener" target="_blank">{html.escape(r["item"])}</a>{tag}{note}</td>'
                   f'<td class="n">{r["qty"]}</td><td class="n">{money(r["each"])}</td><td class="n">{money(r["line"])}</td></tr>')
    out.append(f'<tr class="sum"><td colspan="3">Everything</td><td class="n">{money(total)}</td></tr>')
    t = fill(t, "BOM", "\n".join(out))
    # prints
    out = []
    grp_names = {"base": "Base", "mast": "Column", "torso": "Torso", "head": "Head", "arm": "Arms"}
    for g in ("base", "mast", "torso", "head", "arm"):
        ps = [p for p in manifest["parts"] if p["group"] == g]
        if not ps:
            continue
        grams = sum(p["grams"] * p["qty"] for p in ps)
        out.append(f'<tr class="grp"><td colspan="4">{grp_names[g]}</td><td class="n">{grams / 1000:.2f} kg</td></tr>')
        for p in ps:
            bed = " × ".join(f"{v:.0f}" for v in p["bed_mm"])
            col = {"shell": "white", "frame": "grey", "dark": "black", "accent": "TPU"}.get(p["color"], p["color"])
            out.append(f'<tr><td><a href="/bob-v3/stl/{p["name"]}.stl" download>{p["name"]}</a><span class="d">{html.escape(p["note"])}</span></td>'
                       f'<td class="n">{p["qty"]}</td><td>{col}</td><td class="n">{bed}</td><td class="n">{p["grams"] * p["qty"]:.0f} g</td></tr>')
    t = fill(t, "PRINTS", "\n".join(out))
    # checks
    names = {"stand": "Stands still at home", "torque": "Arm torque, 0.5 kg in the hand", "hold": "Holds 0.5 kg per hand at the furthest pose the reach limit allows",
             "lift": f"Lift 0 → {scene['dims']['lift_travel']:.0f} mm → 0 at 25 mm/s, hands tucked at the chest, 0.5 kg per hand",
             "tip": "Tip margin, worst poses the reach limit allows, 0.5 kg per hand", "brake": "Drives 0.6 m/s, stops at up to 6 m/s², torso up, 0.5 kg per hand", "push": "Shove at the head, torso up, worst allowed pose, 0.5 kg per hand",
             "slope": "Steepest ramp, worst pose", "reach": "Workspace sampling", "tasks": "Floor, counter and top shelf by IK",
             "pick": "Scripted pick off a 0.75 m table, reach limit on",
             "interlock": "Reach limit with a load: blocks reaching out; 25 N shove and 20° ramp at the worst allowed pose"}
    out = []
    for k, v in checks.items():
        detail = {
            "stand": lambda v: f"drift {v['drift_mm']} mm, tilt {v['tilt_deg']}°",
            "torque": lambda v: ", ".join(f"{r['joint'].replace('_', ' ')} {r['worst_Nm']} N·m ({100 * r['of_rated']:.0f}% rated)" for r in v["rows"][:5]),
            "hold": lambda v: f"worst error {v['worst_err_deg']}°, tilt {v.get('tilt_deg', 0)}°" + ("" if not v.get("saturated") else ", saturated"),
            "tip": lambda v: "; ".join(f"{n}: CoM {r['margin_mm']} mm inside, tilt {r['tilt_deg']}°" for n, r in v["poses"].items()),
            "lift": lambda v: (
                f"{v['time_s']} s up, {v.get('down_time_s', '?')} s down, holds within {v['hold_err_mm']} mm at {v['hold_force_N']} N, "
                + ("tubes track 1/3 and 2/3 of the travel (error under 0.01 in), " if v.get('stage_err_mm', 1) < 0.25 else f"tubes within {v.get('stage_err_mm', '?')} mm of 1/3 and 2/3, ")
                + ("no contact" if not v.get("contacts") else "touches " + ", ".join(v["contacts"]))
                if abs(v.get("travel_mm", -1) - scene["dims"]["lift_travel"]) < 5
                else "self-locking screw, holds with the power off"),
            "brake": lambda v: f"max tilt {v['max_tilt_deg']}° at {v['speed_mps']} m/s",
            "push": lambda v: f"tips at {v['push_forward_N']} N forward, {v['push_back_N']} N back",
            "slope": lambda v: f"{v['down_deg']}° nose down, {v['up_deg']}° nose up, {v['side_deg']}° sideways",
            "reach": lambda v: f"hand to {v['z_max_m']} m up, {v['side_reach_y_m']} m sideways, counter reach {v['counter_reach_x_m']} m",
            "tasks": lambda v: ", ".join(f"{n.split(',')[0]}: lift {x['lift_m']} m" for n, x in v["targets"].items() if x),
            "pick": lambda v: f"{100 * v['success_rate']:.0f}% of {v['episodes']} random placements",
            "interlock": lambda v: ("blocks reaching straight out at every lift height; "
                                    + "; ".join(f"lift {float(L):.3f} m: {r['push_forward_N']} N forward, {r['push_back_N']} N back, {r['down_deg']}° nose down"
                                                for L, r in v["stability_by_lift"].items())),
        }[k](v)
        out.append(f'<tr><td>{"✓" if v["ok"] else "✗"}</td><td>{names.get(k, k)}</td><td class="d2">{html.escape(detail)}</td></tr>')
    t = fill(t, "CHECKS", "\n".join(out))
    t = fill(t, "WIRING", wiring_svg())
    t = fill(t, "WIRES", wiring_table())
    t = t.replace("{{TOTAL}}", money(total)).replace("{{TOBUY}}", money(total - have)).replace("{{MASS}}", f"{data['mass_kg']}") \
         .replace("{{PRINTKG}}", f"{manifest['print_mass_g'] / 1000:.1f}").replace("{{NPRINTS}}", str(manifest["total_prints"])) \
         .replace("{{NUNIQUE}}", str(manifest["unique_prints"]))
    import re as _re

    def bust(m):
        f = dst / m.group(2)
        return f'{m.group(1)}/bob-v3/{m.group(2)}?v={ver(f)}"' if f.exists() else m.group(0)

    t = _re.sub(r'((?:src|href|poster)=")/bob-v3/(img/[^"?]+|bob-v3-[a-z-]+\.zip)(?:\?v=[0-9a-f]+)?"', bust, t)
    if (dst / "viewer.js").exists():
        t = _re.sub(r'(/bob-v3/viewer\.js)(?:\?v=[0-9a-f]+)?',
                    lambda m: f"{m.group(1)}?v={ver(dst / 'viewer.js')}", t, count=1)
    # numbers tagged data-k are refilled on every publish
    fills = {
        "mass": f"{data['mass_kg']} kg", "nprints": str(manifest["total_prints"]), "total": money(total),
        "printcount": f"{manifest['unique_prints']} files · {manifest['total_prints']} prints · {manifest['print_mass_g'] / 1000:.1f} kg",
        "bomcount": money(total),
        "printline": f"{manifest['total_prints']} prints from {manifest['unique_prints']} files, about {manifest['print_mass_g'] / 1000:.1f} kg of filament.",
    }
    for k, v in fills.items():
        t, n = _re.subn(r'(<[^>]*data-k="%s"[^>]*>)[^<]*(<)' % k, lambda m, v=v: m.group(1) + html.escape(v) + m.group(2), t)
        if not n:
            print("warning: no data-k", k)
    a, b = t.index("<body"), t.index('<section class="section" id="prints"')
    t = t[:a] + us_units(t[a:b]) + t[b:]
    page.write_text(t)
    print("done ->", dst)


if __name__ == "__main__":
    main()
