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
    """Lay the wiring out on the grid in docs/wiring.py and route every wire with right angles."""
    pos = {k: (PAD + c * CW, PAD + 30 + r * RH) for k, (_, _, c, r, _) in WIRING.NODES.items()}
    cols = max(v[2] for v in WIRING.NODES.values()) + 1
    rows = max(v[3] for v in WIRING.NODES.values()) + 1
    W, H = PAD * 2 + (cols - 1) * CW + NW, PAD * 2 + 30 + rows * RH + 30
    lanes = {}
    paths = []
    for i, (a, b, kind, what, wire, conn, fuse) in enumerate(WIRING.WIRES):
        (xa, ya), (xb, yb) = pos[a], pos[b]
        ca, cb = WIRING.NODES[a][2], WIRING.NODES[b][2]
        key = (min(ca, cb), max(ca, cb))
        lane = lanes.get(key, 0)
        lanes[key] = lane + 1
        off = (lane % 7 - 3) * 5
        ya_, yb_ = ya + NH / 2 + (lane % 3 - 1) * 6, yb + NH / 2 + (lane % 3 - 1) * 6
        gap = (CW - NW) / 2
        if cb == ca + 1:  # neighbours: one elbow in the column gap
            mx = xa + NW + gap + off * 0.6
            pts = [(xa + NW, ya_), (mx, ya_), (mx, yb_), (xb, yb_)]
        elif cb > ca:  # run along the row gap above B so no box is crossed
            gy = yb - (RH - NH) / 2 + (lane % 3 - 1) * 4
            x1, x2 = xa + NW + gap + off * 0.6, xb - gap + off * 0.6
            pts = [(xa + NW, ya_), (x1, ya_), (x1, gy), (x2, gy), (x2, yb_), (xb, yb_)]
        elif cb < ca:
            gy = yb - (RH - NH) / 2 + (lane % 3 - 1) * 4
            x1, x2 = xa - gap + off * 0.6, xb + NW + gap + off * 0.6
            pts = [(xa, ya_), (x1, ya_), (x1, gy), (x2, gy), (x2, yb_), (xb + NW, yb_)]
        else:
            x = xa + NW + 8 + (lane % 4) * 4
            pts = [(xa + NW, ya_), (x, ya_), (x, yb_), (xa + NW, yb_)]
        d = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        col = WIRING.COLORS[kind]
        dash = ' stroke-dasharray="5 4"' if kind == "estop" else ""
        tip = html.escape(f"{WIRING.NODES[a][0]} → {WIRING.NODES[b][0]}: {what}. {wire} {conn} {fuse}".strip())
        paths.append(f'<polyline class="w" data-kind="{kind}" points="{d}" stroke="{col}"{dash}><title>{tip}</title></polyline>')
    nodes = []
    for k, (label, sub, c, r, item) in WIRING.NODES.items():
        x, y = pos[k]
        nodes.append(f'<g class="wn" data-node="{k}"><rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="8"/>'
                     f'<text class="t" x="{x + NW / 2}" y="{y + 20}">{html.escape(label)}</text>'
                     f'<text class="ts" x="{x + NW / 2}" y="{y + 36}">{html.escape(sub)}</text></g>')
    heads = ["Power in", "Distribution", "Conversion", "Compute, rails", "Buses", "Motors, sensors", "More devices"]
    hdr = "".join(f'<text class="hd" x="{PAD + i * CW + NW / 2}" y="{PAD + 4}">{h.upper()}</text>' for i, h in enumerate(heads[:cols]))
    lx = PAD
    legend = []
    for k, lab in WIRING.LABELS.items():
        legend.append(f'<g><line x1="{lx}" y1="{H - 14}" x2="{lx + 22}" y2="{H - 14}" stroke="{WIRING.COLORS[k]}" stroke-width="3"'
                      f'{" stroke-dasharray=\"5 4\"" if k == "estop" else ""}/><text class="lg" x="{lx + 28}" y="{H - 10}">{lab}</text></g>')
        lx += 28 + 8 * len(lab) + 26
    return (f'<svg class="wiresvg" viewBox="0 0 {W} {H}" role="img" aria-label="Bob v3 wiring: every power, bus and signal wire">'
            f'{hdr}<g class="ws">{"".join(paths)}</g><g>{"".join(nodes)}</g>{"".join(legend)}</svg>')


def wiring_table() -> str:
    rows = ["<tr><th></th><th>From</th><th>To</th><th>What</th><th>Wire</th><th>Connector</th><th>Fuse</th></tr>"]
    for a, b, kind, what, wire, conn, fuse in WIRING.WIRES:
        rows.append(f'<tr><td><i class="sw" style="background:{WIRING.COLORS[kind]}"></i></td><td>{html.escape(WIRING.NODES[a][0])}</td>'
                    f'<td>{html.escape(WIRING.NODES[b][0])}</td><td>{html.escape(what)}</td><td>{html.escape(wire)}</td>'
                    f'<td>{html.escape(conn)}</td><td>{html.escape(fuse)}</td></tr>')
    return "\n".join(rows)

COLORS = {"shell": [235, 235, 230], "dark": [34, 34, 37], "frame": [140, 146, 156], "accent": [0, 127, 255],
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
        for f in ["bob_v3.xml", "bob_env.py", "expert.py", "train.py", "record_demos.py", "check.py", "README.md"]:
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

    data = dict(scene=dict(joints=scene["joints"], poses=scene["poses"], links=scene["links"], dims=scene["dims"],
                           items=[{k: it.get(k) for k in ("name", "link", "group", "kind", "color", "material", "mass_g", "print", "note", "bom")}
                                  for it in scene["items"]]),
                parts=manifest["parts"], hardware=manifest["hardware"], stability=manifest["stability"],
                bom=dict(rows=rows, total=total, have=have), checks=checks,
                wiring=dict(nodes={k: dict(label=v[0], item=v[4]) for k, v in WIRING.NODES.items()},
                            wires=[dict(a=a, b=b, kind=k, what=w) for a, b, k, w, *_ in WIRING.WIRES], colors=WIRING.COLORS),
                mass_kg=round(manifest["robot_mass_g"] / 1000, 1), print_kg=round(manifest["print_mass_g"] / 1000, 2))
    # The site caches .glb and images for a year (vercel.json), so every URL carries a content hash.
    import hashlib

    def ver(path):
        return hashlib.sha1(path.read_bytes()).hexdigest()[:10]

    data["glb"] = f"bob_v3.glb?v={ver(dst / 'bob_v3.glb')}"
    (dst / "data.json").write_text(json.dumps(data, separators=(",", ":")))

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
    out.append(f'<tr class="sum2"><td colspan="3">To buy, if you already have the Bob v2 hubs, pack, charger and drivers</td><td class="n">{money(total - have)}</td></tr>')
    t = fill(t, "BOM", "\n".join(out))
    # prints
    out = []
    grp_names = {"base": "Base", "mast": "Mast and lift", "torso": "Torso", "head": "Head", "arm": "Arms"}
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
    names = {"stand": "Stands still at home", "torque": "Arm torque, 0.5 kg in the hand", "hold": "Holds both arms straight out with 0.5 kg",
             "lift": "Lift 0 → 650 mm at 25 mm/s", "brake": "Drives 0.6 m/s, stops at up to 6 m/s²", "push": "Shove at the head, torso up, arms out",
             "slope": "Steepest ramp, worst pose", "reach": "Workspace sampling", "tasks": "Floor, counter and top shelf by IK",
             "pick": "Scripted pick off a 0.75 m table"}
    out = []
    for k, v in checks.items():
        detail = {
            "stand": lambda v: f"drift {v['drift_mm']} mm, tilt {v['tilt_deg']}°",
            "torque": lambda v: ", ".join(f"{r['joint'].replace('_', ' ')} {r['worst_Nm']} N·m ({100 * r['of_rated']:.0f}% rated)" for r in v["rows"][:5]),
            "hold": lambda v: f"worst error {v['worst_err_deg']}°, nothing saturated",
            "lift": lambda v: f"{v['time_s']} s, holds within {v['hold_err_mm']} mm at {v['hold_force_N']} N",
            "brake": lambda v: f"max tilt {v['max_tilt_deg']}° at {v['speed_mps']} m/s",
            "push": lambda v: f"tips at {v['push_forward_N']} N forward, {v['push_back_N']} N back",
            "slope": lambda v: f"{v['down_deg']}° nose down, {v['up_deg']}° nose up, {v['side_deg']}° sideways",
            "reach": lambda v: f"hand to {v['z_max_m']} m up, {v['side_reach_y_m']} m sideways, counter reach {v['counter_reach_x_m']} m",
            "tasks": lambda v: ", ".join(f"{n.split(',')[0]}: lift {x['lift_m']} m" for n, x in v["targets"].items() if x),
            "pick": lambda v: f"{100 * v['success_rate']:.0f}% of {v['episodes']} random placements",
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

    t = _re.sub(r'((?:src|href)=")/bob-v3/(img/[^"?]+|bob-v3-[a-z-]+\.zip)(?:\?v=[0-9a-f]+)?"', bust, t)
    # numbers tagged data-k are refilled on every publish
    fills = {
        "mass": f"{data['mass_kg']} kg", "nprints": str(manifest["total_prints"]), "total": money(total),
        "printcount": f"{manifest['unique_prints']} files · {manifest['total_prints']} prints · {manifest['print_mass_g'] / 1000:.1f} kg",
        "bomcount": f"{money(total)} · {money(total - have)} to buy (you already have the battery and charger)",
        "printline": f"{manifest['total_prints']} prints from {manifest['unique_prints']} files, about {manifest['print_mass_g'] / 1000:.1f} kg of filament.",
    }
    for k, v in fills.items():
        t, n = _re.subn(r'(<[^>]*data-k="%s"[^>]*>)[^<]*(<)' % k, lambda m, v=v: m.group(1) + html.escape(v) + m.group(2), t)
        if not n:
            print("warning: no data-k", k)
    page.write_text(t)
    print("done ->", dst)


if __name__ == "__main__":
    main()
