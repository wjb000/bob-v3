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


def _wd_fmt_a(a):
    return f"{a:.2f}" if a < 1 else f"{a:.1f}"


def wiring_svg() -> str:
    """Draw docs/wiring.py as a schematic: power on the left (pack, fuses, switch, contactor, regulators, the return bar),
    control and buses in the middle, devices and sensors on the right. Each wire runs on its own right-angle lane.
    Rails are coloured by voltage, every fuse is drawn with its rating, the e-stop loop is dashed, and power wires
    carry volts, design current and gauge."""
    import re as _re
    NW_, NH_, RH_, TOP = 164, 44, 62, 78
    COLX = [20, 274, 588, 842, 1076, 1320, 1548]  # wide gaps where the power branches and returns run
    N, E = WIRING.NODES, WIRING.elec()
    rows = max(v[3] for k, v in N.items() if k != "gnd") + 1
    bar_y = TOP + rows * RH_ + 8
    BAR_H = 34
    W = COLX[-1] + NW_ + 20
    LEG_Y = bar_y + BAR_H + 44
    H = LEG_Y + 76
    xy = {k: (COLX[c], TOP + r * RH_) for k, (_, _, c, r, _) in N.items() if k != "gnd"}
    rects = {k: (x, y, x + NW_, y + NH_) for k, (x, y) in xy.items()}
    bar = (COLX[0], bar_y, COLX[2] + NW_, bar_y + BAR_H)

    def gx(g):  # centre of the gap right of column g
        return (COLX[g] + NW_ + COLX[g + 1]) / 2 if g + 1 < len(COLX) else COLX[g] + NW_ + 10

    def ry(r):  # centre of the gap above row r
        return TOP + r * RH_ - (RH_ - NH_) / 2

    def col(k):
        return N[k][2]

    # which side of each node every wire end uses
    ends, side = [], {}
    for i, (a, b, kind, *_ ) in enumerate(WIRING.WIRES):
        if kind == "gnd":
            x = b if a == "gnd" else a
            sd = "r" if col(x) == 0 else "l"
            ends.append(((x, sd), None))
            side.setdefault((x, sd), []).append((bar_y, i, 0))
            continue
        ca, cb = col(a), col(b)
        e = ((a, "r"), (b, "r")) if ca == cb else ((a, "r"), (b, "l")) if ca < cb else ((a, "l"), (b, "r"))
        ends.append(e)
        side.setdefault(e[0], []).append((xy[b][1], i, 0))
        side.setdefault(e[1], []).append((xy[a][1], i, 1))
    port = {}
    for (k, sd), lst in side.items():
        lst.sort()
        for j, (_, i, e) in enumerate(lst):
            port[(i, e)] = (xy[k][0] + (NW_ if sd == "r" else 0), xy[k][1] + NH_ * (j + 1) / (len(lst) + 1))
    gapn, rown = {}, {}

    def lane(store, key, base, step=6):
        k = store.get(key, 0)
        store[key] = k + 1
        return base + ((k + 1) // 2) * step * (1 if k % 2 else -1)

    def clear(x1, x2, y, skip):
        lo, hi = sorted((x1, x2))
        return not any(k not in skip and r[0] - 4 < hi and r[2] + 4 > lo and r[1] - 3 < y < r[3] + 3 for k, r in rects.items())

    def fuse_at(pts):
        """Where the fuse symbol sits: on the run into the load if it is long enough, else the run out of the source."""
        segs = list(zip(pts, pts[1:]))
        last, first = segs[-1], segs[0]
        if abs(last[1][0] - last[0][0]) >= 30:
            s, near = (last[1], last[0]), True
        elif abs(first[1][0] - first[0][0]) >= 40:
            s, near = first, False
        else:
            s, near = max(segs, key=lambda q: abs(q[1][0] - q[0][0]) + abs(q[1][1] - q[0][1])), False
        (x0, y0), (x1, y1) = s
        L = abs(x1 - x0) + abs(y1 - y0)
        d = min(22.0, L / 2) if near else L / 2
        ux, uy = ((x1 > x0) - (x1 < x0)), ((y1 > y0) - (y1 < y0))
        return x0 + ux * d, y0 + uy * d, ux != 0

    paths = []
    for i, (a, b, kind, what, wire, conn, fuse) in enumerate(WIRING.WIRES):
        col_ = WIRING.COLORS[kind]
        rec = WIRING.wire_records()[i]
        e = E.get((a, b))
        if kind == "gnd":
            x = b if a == "gnd" else a
            xa, ya = port[(i, 0)]
            g = col(x) if col(x) == 0 else col(x) - 1
            cx = lane(gapn, g, gx(g))
            pts = [(xa, ya), (cx, ya), (cx, bar_y)]
        else:
            (xa, ya), (xb, yb) = port[(i, 0)], port[(i, 1)]
            ca, cb = col(a), col(b)
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
        pts = [p for j, p in enumerate(pts) if j in (0, len(pts) - 1) or not (
            (pts[j - 1][0] == p[0] == pts[j + 1][0]) or (pts[j - 1][1] == p[1] == pts[j + 1][1]))]  # drop straight-through bends
        dd = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        dash = ' stroke-dasharray="5 4"' if kind == "estop" else ""
        length = f" {rec['len_mm']} mm." if rec["len_mm"] else ""
        el = ""
        if e:
            el = f" {e['volts']:g} V"
            if e["amps"] > 0:
                el += f", {_wd_fmt_a(e['amps'])} A design"
                if e["peak"] > e["amps"] * 1.2:
                    el += f", {_wd_fmt_a(e['peak'])} A peak"
            el += "."
        tip = html.escape(f"{N[a][0]} → {N[b][0]}: {what}.{el} {wire} {conn}{' fuse ' + fuse if fuse else ''}.{length}"
                          .replace(" .", ".").replace("..", "."))
        extra = []
        if kind.startswith("power") and e and wire:
            seg = max(zip(pts, pts[1:]), key=lambda s2: abs(s2[1][0] - s2[0][0]))
            room = abs(seg[1][0] - seg[0][0]) - 8
            for lab in (f"{e['volts']:g} V · {_wd_fmt_a(e['amps'])} A · {wire}", f"{_wd_fmt_a(e['amps'])} A · {wire}"):
                if room > 5.6 * len(lab):
                    extra.append(f'<text class="wl" x="{(seg[0][0] + seg[1][0]) / 2:.0f}" y="{seg[0][1] + 12:.0f}" fill="{col_}" '
                                 f'text-anchor="middle">{html.escape(lab)}</text>')
                    break
        m = _re.match(r"(\d+(?:\.\d+)?) A", fuse or "")
        if m:
            fx, fy, horiz = fuse_at(pts)
            w_, h_ = (18, 8) if horiz else (8, 18)
            extra.append(f'<rect x="{fx - w_ / 2:.0f}" y="{fy - h_ / 2:.0f}" width="{w_}" height="{h_}" rx="2" fill="#121417" stroke="{col_}" stroke-width="1.5"/>'
                         + (f'<line x1="{fx - 9:.0f}" y1="{fy:.0f}" x2="{fx + 9:.0f}" y2="{fy:.0f}" stroke="{col_}" stroke-width="1"/>' if horiz else
                            f'<line x1="{fx:.0f}" y1="{fy - 9:.0f}" x2="{fx:.0f}" y2="{fy + 9:.0f}" stroke="{col_}" stroke-width="1"/>'))
            tx, ty, anc = (fx, fy - 7, "middle") if horiz else (fx + 8, fy + 3, "start")
            extra.append(f'<text class="wl" x="{tx:.0f}" y="{ty:.0f}" fill="{col_}" text-anchor="{anc}">{m.group(1)} A</text>')
        if kind == "estop":
            (xp, _), (xb, yb) = pts[-2], pts[-1]
            tag = "coil" if b == "cont" else "NC" if b == "estop" else ""
            if tag:
                tx, anc = (xb - 4, "end") if xp < xb else (xb + 4, "start")
                extra.append(f'<text class="wl" x="{tx:.0f}" y="{yb + 12:.0f}" fill="{col_}" text-anchor="{anc}">{tag}</text>')
        dots = f'<circle cx="{pts[0][0]:.0f}" cy="{pts[0][1]:.0f}" r="2.5" fill="{col_}"/>'
        dots += (f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="3" fill="{col_}"/>' if kind == "gnd" else
                 f'<circle cx="{pts[-1][0]:.0f}" cy="{pts[-1][1]:.0f}" r="2.5" fill="{col_}"/>')
        paths.append(f'<g class="wg" data-kind="{kind}" data-a="{a}" data-b="{b}"><polyline class="w" points="{dd}" stroke="{col_}"{dash}>'
                     f'<title>{tip}</title></polyline>{"".join(extra)}{dots}</g>')
    nodes = []
    feed = {}
    for a, b, kind, *_ in WIRING.WIRES:
        if kind != "gnd":
            feed.setdefault(b, kind)
            feed.setdefault(a, kind)
    for k, (label, sub, c, r, item) in N.items():
        if k == "gnd":
            x0, y0, x1, y1 = bar
            nodes.append(f'<g class="wn" data-node="{k}" tabindex="0"><rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{BAR_H}" rx="8"/>'
                         f'<rect class="acc" x="{x0}" y="{y0 + 6}" width="3" height="{BAR_H - 12}" rx="1.5" fill="{WIRING.COLORS["gnd"]}"/>'
                         f'<text class="t" x="{(x0 + x1) / 2:.0f}" y="{y0 + 15}">{html.escape(label)}</text>'
                         f'<text class="ts" x="{(x0 + x1) / 2:.0f}" y="{y0 + 28}">{html.escape(sub)} · the negative half of every power pair</text></g>')
            continue
        x, y = xy[k]
        acc = WIRING.COLORS[feed.get(k, "usb")]
        nodes.append(f'<g class="wn" data-node="{k}" tabindex="0"><rect x="{x}" y="{y}" width="{NW_}" height="{NH_}" rx="8"/>'
                     f'<rect class="acc" x="{x}" y="{y + 8}" width="3" height="{NH_ - 16}" rx="1.5" fill="{acc}"/>'
                     f'<text class="t" x="{x + NW_ / 2}" y="{y + 19}">{html.escape(label)}</text>'
                     f'<text class="ts" x="{x + NW_ / 2}" y="{y + 34}">{html.escape(sub)}</text></g>')
    zones, hdr = [], []
    for c0, c1, name in ((0, 2, "Power"), (3, 4, "Control and buses"), (5, 6, "Devices and sensors")):
        x0, x1 = COLX[c0] - 12, COLX[c1] + NW_ + 12
        y1 = (bar[3] if c0 == 0 else TOP + rows * RH_) + 12
        zones.append(f'<rect class="zone" x="{x0}" y="{TOP - 26}" width="{x1 - x0}" height="{y1 - TOP + 26}" rx="12"/>')
        hdr.append(f'<text class="hd" x="{(x0 + x1) / 2:.0f}" y="{TOP - 34}">{name.upper()}</text>')
    zones.append(f'<text class="zt" x="{COLX[0]}" y="{TOP - 10}">PACK · FUSES · SWITCH · CONTACTOR</text>'
                 f'<text class="zt" x="{COLX[2]}" y="{TOP - 10}">REGULATORS</text>')
    legend = []
    groups = (("POWER", ["power36", "power18", "power12", "power5", "gnd", "estop"]), ("BUSES AND SIGNALS", ["usb", "ttl", "signal", "motor"]))
    for gi, (gname, kinds) in enumerate(groups):
        ly = LEG_Y + gi * 26
        legend.append(f'<text class="zt" x="{COLX[0]}" y="{ly + 4}">{gname}</text>')
        lx = COLX[0] + 150
        for k in kinds:
            lab = WIRING.LABELS[k]
            legend.append(f'<g class="lgi" data-kind="{k}" tabindex="0"><line x1="{lx}" y1="{ly}" x2="{lx + 22}" y2="{ly}" stroke="{WIRING.COLORS[k]}" stroke-width="3"'
                          + (' stroke-dasharray="5 4"' if k == "estop" else "") + f'/><text class="lg" x="{lx + 28}" y="{ly + 4}">{html.escape(lab)}</text></g>')
            lx += 28 + 7 * len(lab) + 26
        if gi == 0:
            legend.append(f'<g><rect x="{lx}" y="{ly - 4}" width="18" height="8" rx="2" fill="#121417" stroke="#d0d4d8" stroke-width="1.5"/>'
                          f'<line x1="{lx}" y1="{ly}" x2="{lx + 18}" y2="{ly}" stroke="#d0d4d8" stroke-width="1"/>'
                          f'<text class="lg" x="{lx + 26}" y="{ly + 4}">Fuse and rating. Every 36 V fuse is rated 58 V DC.</text></g>')
    legend.append(f'<text class="lg" x="{COLX[0]}" y="{LEG_Y + 56}">Power wires show volts · design current · gauge. '
                  f'Design current is worked back from the parts\' ratings at a 30 V pack, where the arm converters stop.</text>')
    return (f'<svg class="wiresvg" viewBox="0 0 {W} {H}" role="img" aria-label="Bob v3 wiring schematic: power, control and buses, devices">'
            f'{"".join(zones)}{"".join(hdr)}<g class="ws">{"".join(paths)}</g><g>{"".join(nodes)}</g>{"".join(legend)}</svg>')


def wiring_table() -> str:
    E = WIRING.elec()
    rows = ["<tr><th></th><th>From</th><th>To</th><th>What</th><th>Volts</th><th>Current</th><th>Wire</th><th>Length</th>"
            "<th>Connector</th><th>Fuse</th></tr>"]
    for (a, b, kind, what, wire, conn, fuse), rec in zip(WIRING.WIRES, WIRING.wire_records()):
        e = E.get((a, b))
        volts = f"{e['volts']:g} V" if e else ""
        if not e:
            amps = ""
        elif e["amps"] <= 0:
            amps = "data"
        elif e["peak"] > e["amps"] * 1.2:
            amps = f"{_wd_fmt_a(e['amps'])} A, {_wd_fmt_a(e['peak'])} A peak"
        else:
            amps = f"{_wd_fmt_a(e['amps'])} A"
        rows.append(f'<tr><td><i class="sw" style="background:{WIRING.COLORS[kind]}"></i></td><td>{html.escape(WIRING.NODES[a][0])}</td>'
                    f'<td>{html.escape(WIRING.NODES[b][0])}</td><td>{html.escape(what)}</td><td>{volts}</td><td>{amps}</td>'
                    f'<td>{html.escape(wire)}</td><td>{rec["len_mm"]} mm</td><td>{html.escape(conn)}</td><td>{html.escape(fuse)}</td></tr>')
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
        for f in ["bob_v3.xml", "bob_env.py", "expert.py", "train.py", "record_demos.py", "check.py", "interlock.py", "cables.py", "harness.json", "README.md"]:
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
    ELEC = WIRING.elec()  # volts, design amps, peak amps per wire, for the viewer

    def harness_wires():
        """wiring.py rows plus the 3D route from sim/harness.json (docs/harness.py, format in docs/harness_format.md)."""
        sys.path.insert(0, str(ROOT / "docs"))
        import harness as HN
        routes = {w["id"]: w for w in json.loads((ROOT / "sim" / "harness.json").read_text())["wires"]}
        out, seen = [], set()
        for (a, b, k, w, g, c, f), rec in zip(WIRING.WIRES, WIRING.wire_records()):
            r = routes[f"{a}-{b}"]
            row = dict(id=r["id"], **{"from": a}, to=b, a=a, b=b, kind=k, what=w, gauge=g, awg=HN.awg(g), conn=c, fuse=f,
                       len_mm=rec["len_mm"], route_mm=r["route_mm"], **ELEC.get((a, b), {}))
            if r["bundle"]:
                row["bundle"] = r["bundle"]
            if not r["bundle"] or r["bundle"] not in seen:  # a bundle's radius sits on its first wire
                row["radius_mm"] = round(r["radius_mm"], 1)
            seen.add(r["bundle"])
            row["path"] = r["path"]
            out.append(row)
        return out
    data = dict(interlock=interlock, scene=dict(joints=scene["joints"], poses=scene["poses"], links=scene["links"], dims=scene["dims"],
                           items=[{k: it.get(k) for k in ("name", "link", "group", "kind", "color", "material", "mass_g", "print", "note", "bom")}
                                  for it in scene["items"]]),
                parts=manifest["parts"], hardware=manifest["hardware"], stability=manifest["stability"],
                bom=dict(rows=rows, total=total, have=have), checks=checks,
                wiring=dict(nodes={k: dict(label=v[0], item=v[4]) for k, v in WIRING.NODES.items()},
                            wires=harness_wires(),
                            colors=WIRING.COLORS),
                # the sim mass: every listed part plus the wiring, screws and small hardware build_mjcf adds per link
                mass_kg=round(float(mm.body_mass.sum()), 2), parts_kg=round(manifest["robot_mass_g"] / 1000, 2),
                print_kg=round(manifest["print_mass_g"] / 1000, 2))
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
             "interlock": "Reach limit with a load: blocks reaching out; 25 N shove and 20° ramp at the worst allowed pose",
             "cables": "3D cable routes: radius + 1 mm clear of servos and shells, slack across every joint and the lift"}
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
            "slope": lambda v: (f"{v['down_deg']}° nose down, {v['up_deg']}° nose up, "
                                + (f"{v['side_left_deg']}° left side down, {v['side_right_deg']}° right side down"
                                   if "side_left_deg" in v else f"{v['side_deg']}° sideways")),
            "reach": lambda v: f"hand to {v['z_max_m']} m up, {v['side_reach_y_m']} m sideways, counter reach {v['counter_reach_x_m']} m",
            "tasks": lambda v: ", ".join(f"{n.split(',')[0]}: lift {x['lift_m']} m" for n, x in v["targets"].items() if x),
            "pick": lambda v: f"{100 * v['success_rate']:.0f}% of {v['episodes']} random placements",
            "interlock": lambda v: ("blocks reaching straight out at every lift height; "
                                    + "; ".join(f"lift {float(L):.3f} m: {r['push_forward_N']} N forward, {r['push_back_N']} N back, {r['down_deg']}° nose down"
                                                for L, r in v["stability_by_lift"].items())),
            "cables": lambda v: (f"{v['wires']} wires, closest {v['worst_clear_mm']} mm, least slack {v['worst_slack_mm']} mm"
                                 + (f", {v['hits']} contacts: " + ", ".join(v["parts_in_the_way"]) if v["hits"] else "")),
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
