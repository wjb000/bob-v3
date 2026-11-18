#!/usr/bin/env python3
"""Build Bob v3, check it, and write every file the build, the viewer and the sim need.

    .venv/bin/python cad/export.py            # full build
    .venv/bin/python cad/export.py --fast     # skip STEP files

Outputs
  cad/stl/<part>.stl        print orientation, on the origin, one per unique part
  cad/step/<part>.step      same, for editing in any CAD tool
  cad/step/bob_v3.step      whole robot at the home pose
  cad/placed/*.stl          every part and bought envelope in the robot frame, zero pose
  cad/scene.json            links, joints, poses, items -> viewer and sim
  cad/reports/manifest.json print list, masses, hardware tally, check results

Exit code 1 if any check fails.
"""

from __future__ import annotations

import json
import math
import sys
import time
from itertools import combinations
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN
from OCP.gp import gp_Pnt

import params as P
import robot
import base
from lib import HARDWARE

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / "cad"
STL, STEP, PLACED, REPORTS = CAD / "stl", CAD / "step", CAD / "placed", CAD / "reports"
VIEW = CAD / "viewer"  # coarse meshes for the web viewer
TOL, ANG = 0.15, 0.25
FAST = "--fast" in sys.argv


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- orientation

def _rotated(solid, rot):
    out = solid
    for ax, ang in zip(((1, 0, 0), (0, 1, 0), (0, 0, 1)), rot):
        if abs(ang) > 1e-6:
            out = out.rotate((0, 0, 0), ax, ang)
    bb = out.BoundingBox()
    return out.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))


def _bed_area(solid) -> float:
    bb = solid.BoundingBox()
    area = 0.0
    for f in solid.Faces():
        if f.geomType() != "PLANE":
            continue
        n = f.normalAt()
        if n.z < -0.999 and abs(f.Center().z - bb.zmin) < 0.05:
            area += f.Area()
    return area


def _support_cm2(solid) -> float:
    """Downward faces steeper than 45 degrees that are not on the bed, in cm^2: what a slicer would support."""
    import trimesh

    v, f = solid.tessellate(0.3, 0.5)
    t = trimesh.Trimesh(np.array([(p.x, p.y, p.z) for p in v]), np.array(f), process=False)
    n, c, a = t.face_normals, t.triangles_center, t.area_faces
    over = (n[:, 2] < -0.71) & (c[:, 2] > 0.6)
    return round(float(a[over].sum()) / 100.0, 1)


def _fits(solid) -> bool:
    bb = solid.BoundingBox()
    return bb.xlen <= P.BED + 0.01 and bb.ylen <= P.BED + 0.01 and bb.zlen <= P.BED_Z + 0.01


def orient(part):
    """Use the part's override if it has one, else the flat face with the most contact that fits."""
    if part.rot is not None:
        o = _rotated(part.solid, part.rot)
        if not _fits(o):
            for rz in (45.0, 30.0, 60.0):
                o2 = _rotated(part.solid, (part.rot[0], part.rot[1], rz))
                if _fits(o2):
                    return o2, (part.rot[0], part.rot[1], rz)
        return o, part.rot
    best = None
    for rot in ((0, 0, 0), (180, 0, 0), (90, 0, 0), (-90, 0, 0), (0, 90, 0), (0, -90, 0)):
        o = _rotated(part.solid, rot)
        if not _fits(o):
            rot = (rot[0], rot[1], 45)
            o = _rotated(part.solid, rot)
            if not _fits(o):
                continue
        score = _bed_area(o) - 0.02 * o.BoundingBox().zlen
        if best is None or score > best[0]:
            best = (score, o, rot)
    if best is None:
        return _rotated(part.solid, (0, 0, 0)), (0, 0, 0)
    return best[1], best[2]


# ---------------------------------------------------------------- geometry checks

def placed_at(solid, T):
    if np.allclose(T, np.eye(4)):
        return solid
    from OCP.gp import gp_Trsf
    U, _, Vt = np.linalg.svd(T[:3, :3])
    R = U @ Vt  # re-orthogonalise
    t = gp_Trsf()
    t.SetValues(*(float(v) for v in (R[0, 0], R[0, 1], R[0, 2], T[0, 3], R[1, 0], R[1, 1], R[1, 2], T[1, 3],
                                     R[2, 0], R[2, 1], R[2, 2], T[2, 3])))
    return solid.moved(cq.Location(t))


def _bb(s):
    b = s.BoundingBox()
    return (b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax)


def _bb_hit(a, b, pad=0.05):
    return all(a[i] <= b[i + 3] + pad and b[i] <= a[i + 3] + pad for i in range(3))


def overlaps(items, min_vol=30.0):
    """items: [(name, link, solid)] -> [(a, b, mm3)] for real interpenetration."""
    boxes = [_bb(s) for _, _, s in items]
    out = []
    for i, j in combinations(range(len(items)), 2):
        if not _bb_hit(boxes[i], boxes[j]):
            continue
        a, b = items[i], items[j]
        try:
            v = a[2].intersect(b[2]).Volume()
        except Exception:  # noqa: BLE001
            v = 0.0
        if v > min_vol:
            out.append((a[0], b[0], round(v, 1)))
    return out


def _inside(solid, x, y, z) -> bool:
    c = BRepClass3d_SolidClassifier(solid.wrapped, gp_Pnt(float(x), float(y), float(z)), 1e-4)
    return c.State() == TopAbs_IN


def hole_mates(points, z, solids):
    """Every pan insert needs a part above it with a clearance hole on the same axis."""
    bad = []
    for name, pts in points.items():
        for x, y in pts:
            ok = False
            for s in solids:
                b = s.BoundingBox()
                if not (b.xmin - 1 <= x <= b.xmax + 1 and b.ymin - 1 <= y <= b.ymax + 1 and b.zmin - 1 <= z <= b.zmax + 1):
                    continue
                if _inside(s, x, y, z):
                    continue
                if any(_inside(s, x + dx, y + dy, z) for dx, dy in ((4, 0), (-4, 0), (0, 4), (0, -4))):
                    ok = True
                    break
            if not ok:
                bad.append(f"pan insert {name} at ({x:.0f},{y:.0f}) has no mating hole")
    return bad


# ---------------------------------------------------------------- main

def main() -> int:
    t0 = time.time()
    errors, warnings = [], []
    for d in (STL, STEP, PLACED, REPORTS, VIEW):
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.st*"):
            f.unlink()

    log("building parts")
    parts = robot.parts()
    buys = robot.bought()
    tabs = robot.joiners()
    joints = robot.joints()
    log(f"  {len(parts)} parts, {len(buys)} bought, {len(tabs)} joiner tabs  ({time.time() - t0:.0f}s)")

    # ---- print files
    rows = []
    tab_solid = base.joiner_tab()

    class _Tab:
        name, qty, note, material, color, walls, infill, rot, link, group = (
            "joiner_tab", len(tabs), "Joins shell and pan tiles from inside. M3x10 into heat-set inserts.", "PETG", "frame", 4, 40,
            None, "base", "base")
        solid = tab_solid

    print_list = [(p.name, p.solid, p) for p in parts] + [("joiner_tab", tab_solid, _Tab)]
    total_g = 0.0
    for name, solid, p in print_list:
        n = len(solid.Solids())
        if n != 1:
            errors.append(f"{name} is {n} solids")
        oriented, rot = orient(p)
        bb = oriented.BoundingBox()
        size = (bb.xlen, bb.ylen, bb.zlen)
        if not _fits(oriented):
            errors.append(f"{name} does not fit the bed: {size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f}")
        vol = solid.Volume()
        g = vol / 1000 * P.DENSITY * P.FILL
        qty = getattr(p, "qty", 1)
        total_g += g * qty
        cq.exporters.export(oriented, str(STL / f"{name}.stl"), tolerance=TOL, angularTolerance=ANG)
        if not FAST:
            cq.exporters.export(oriented, str(STEP / f"{name}.step"))
        sup = _support_cm2(oriented)
        rows.append(dict(name=name, qty=qty, group=p.group, link=p.link, material=p.material, color=p.color, support_cm2=sup,
                         walls=p.walls, infill=p.infill, note=p.note, rot_deg=[round(r, 1) for r in rot],
                         bed_mm=[round(v, 1) for v in size], volume_cm3=round(vol / 1000, 1), grams=round(g, 1)))
    log(f"  print files written ({time.time() - t0:.0f}s)")

    # ---- placed meshes for the viewer and sim
    items, solids = [], []
    for p in parts:
        items.append(dict(name=p.name, file=f"{p.name}.stl", link=p.link, group=p.group, kind="print",
                          color=p.color, material=p.material, mass_g=round(p.solid.Volume() / 1000 * P.DENSITY * P.FILL, 1),
                          print=p.name, note=p.note))
        solids.append(p.solid)
        cq.exporters.export(p.solid, str(PLACED / f"{p.name}.stl"), tolerance=TOL, angularTolerance=ANG)
        cq.exporters.export(p.solid, str(VIEW / f"{p.name}.stl"), tolerance=0.35, angularTolerance=0.5)
    for i, (link, s) in enumerate(tabs):
        name = f"joiner_{i:02d}"
        grp = {"base": "base", "lift": "torso"}.get(link, "head")
        items.append(dict(name=name, file=f"{name}.stl", link=link, group=grp, kind="print", color="frame", material="PETG",
                          mass_g=round(s.Volume() / 1000 * P.DENSITY * 0.8, 1), print="joiner_tab", note="Joiner tab"))
        solids.append(s)
        cq.exporters.export(s, str(PLACED / f"{name}.stl"), tolerance=0.3, angularTolerance=0.5)
        cq.exporters.export(s, str(VIEW / f"{name}.stl"), tolerance=0.5, angularTolerance=0.6)
    for b in buys:
        items.append(dict(name=b.name, file=f"{b.name}.stl", link=b.link, group=b.group, kind=b.kind, color=b.kind,
                          material="bought", mass_g=b.mass_g, bom=b.bom))
        solids.append(b.solid)
        cq.exporters.export(b.solid, str(PLACED / f"{b.name}.stl"), tolerance=0.3, angularTolerance=0.4)
        cq.exporters.export(b.solid, str(VIEW / f"{b.name}.stl"), tolerance=0.5, angularTolerance=0.6)
    log(f"  placed meshes written ({time.time() - t0:.0f}s)")

    # ---- mass properties per link (printed at FILL, bought at listed mass)
    links = {}
    for it, s in zip(items, solids):
        L = links.setdefault(it["link"], dict(mass_g=0.0, com=np.zeros(3)))
        c = cq.Shape.centerOfMass(s)
        L["mass_g"] += it["mass_g"]
        L["com"] += it["mass_g"] * np.array([c.x, c.y, c.z])
    for L in links.values():
        L["com"] = [round(v, 1) for v in (L["com"] / max(L["mass_g"], 1e-9))]
        L["mass_g"] = round(L["mass_g"], 1)
    total_mass = sum(L["mass_g"] for L in links.values())

    # ---- checks
    log("checks: pan inserts")
    pan_solids = [p.solid for p in parts if not p.name.startswith("base_pan_")]
    errors += hole_mates(dict(base.PAN_PTS), P.PAN_TOP + 2.0, pan_solids)

    log("checks: interference at the home and zero poses")
    report_overlap = {}
    for pose_name in ("home", "zero"):
        T = robot.link_transforms(robot.POSES[pose_name], joints)
        pool = [(it["name"], it["link"], placed_at(s, T[it["link"]])) for it, s in zip(items, solids)]
        # The pinion turns with the fingers on the real gripper; here it is frozen, so its mesh with the racks is expected.
        hits = [h for h in overlaps(pool) if not (h[0].startswith("pinion_") and h[1].startswith("finger_"))]
        report_overlap[pose_name] = hits
        for a, b, v in hits:
            errors.append(f"{pose_name}: {a} intersects {b} by {v} mm3")
        log(f"  {pose_name}: {len(hits)} hits ({time.time() - t0:.0f}s)")

    # ---- tip stability per pose (static, rigid, wheels plus casters)
    stability = {}
    for pose_name, pose in robot.POSES.items():
        T = robot.link_transforms(pose, joints)
        m, mc = 0.0, np.zeros(3)
        for name, L in links.items():
            c = T[name] @ np.array([*L["com"], 1.0])
            m += L["mass_g"]
            mc += L["mass_g"] * c[:3]
        com = mc / m
        front = P.CASTER_X - P.CASTER_TRAIL
        rear = -P.CASTER_X + P.CASTER_TRAIL
        margin_f, margin_b = front - com[0], com[0] - rear
        margin_s = P.WHEEL_Y - abs(com[1])
        stability[pose_name] = dict(com_mm=[round(v, 1) for v in com], margin_front_mm=round(margin_f, 1),
                                    margin_rear_mm=round(margin_b, 1), margin_side_mm=round(margin_s, 1),
                                    tip_deg_front=round(math.degrees(math.atan2(margin_f, com[2])), 1),
                                    tip_deg_rear=round(math.degrees(math.atan2(margin_b, com[2])), 1))
        if min(margin_f, margin_b, margin_s) < 40:
            errors.append(f"{pose_name}: CoM within 40 mm of the support polygon")

    if not FAST:
        log("assembly step")
        T = robot.link_transforms(robot.HOME, joints)
        asm = cq.Assembly(name="bob_v3")
        colors = {"shell": (0.93, 0.93, 0.91), "dark": (0.12, 0.12, 0.13), "frame": (0.55, 0.57, 0.6), "accent": (0.0, 0.5, 1.0)}
        for p in parts:
            asm.add(placed_at(p.solid, T[p.link]), name=p.name, color=cq.Color(*colors.get(p.color, (0.7, 0.7, 0.7))))
        for b in buys:
            asm.add(placed_at(b.solid, T[b.link]), name=b.name, color=cq.Color(0.2, 0.2, 0.2))
        asm.save(str(STEP / "bob_v3.step"))

    scene = dict(
        units="mm", frame="x forward, y left, z up, origin on the floor between the wheels",
        links=links, total_mass_g=round(total_mass, 1),
        joints=[dict(name=j.name, kind=j.kind, parent=j.parent, child=j.child, anchor=list(j.anchor), axis=list(j.axis),
                     range=list(j.range), actuator=j.actuator, mimic=j.mimic) for j in joints],
        poses=robot.POSES, items=items,
        dims=dict(shoulder_z0=P.SHOULDER_Z0, lift_travel=P.LIFT_TRAVEL, base=[P.BASE_L, P.BASE_W, P.BASE_TOP],
                  wheel_od=P.WHEEL_OD, wheel_w=P.WHEEL_W, wheel_y=P.WHEEL_Y, caster_x=P.CASTER_X, caster_trail=P.CASTER_TRAIL,
                  caster_wheel=P.CASTER_WHEEL, mast_top=P.MAST_TOP + P.CAP_H),
    )
    (CAD / "scene.json").write_text(json.dumps(scene, indent=1) + "\n")

    manifest = dict(
        units="mm", bed_mm=[P.BED, P.BED, P.BED_Z], density_g_cm3=P.DENSITY, fill=P.FILL,
        unique_prints=len(rows), total_prints=sum(r["qty"] for r in rows),
        print_mass_g=round(total_g, 0), robot_mass_g=round(total_mass, 0),
        parts=rows, hardware=dict(sorted(HARDWARE.items())), stability=stability, overlaps=report_overlap,
        errors=errors, warnings=warnings, seconds=round(time.time() - t0, 1),
    )
    (REPORTS / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    log(f"{len(rows)} unique prints, {manifest['total_prints']} total, {total_g / 1000:.2f} kg PETG, robot {total_mass / 1000:.1f} kg")
    for k, v in stability.items():
        log(f"  {k:8s} CoM {v['com_mm']}  front {v['margin_front_mm']} rear {v['margin_rear_mm']} side {v['margin_side_mm']}")
    for e in errors:
        log("ERROR", e)
    log(f"done in {time.time() - t0:.0f}s, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
