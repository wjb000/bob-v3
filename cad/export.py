#!/usr/bin/env python3
"""Export print STLs, print STEPs, placed STLs, and one assembly STEP.

    /tmp/cq312/bin/python cad/export.py

Print meshes are rotated onto the bed and dropped to the origin.
Placed meshes stay in the robot frame so the viewer can stack them.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import cadquery as cq
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN
from OCP.gp import gp_Pnt

import model
import params as P

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / "cad" / "stl"
PLACED = STL / "placed"
STEP = ROOT / "cad" / "step"
REPORTS = ROOT / "cad" / "reports"
DENSITY = 1.27  # g/cm^3, PETG
TOL = 0.12
ANG = 0.2


def _hex_ok() -> None:
    solid = model.hex_z(0, 0, 0, 2, 5.5)
    bb = solid.BoundingBox()
    flats = min(bb.xlen, bb.ylen)
    if abs(flats - 5.5) > 0.2:
        raise SystemExit(f"hex across flats is {flats:.2f}, expected 5.5")


def _orient(solid, rot):
    rx, ry, rz = rot
    out = solid
    if abs(rx) > 1e-6:
        out = out.rotate((0, 0, 0), (1, 0, 0), rx)
    if abs(ry) > 1e-6:
        out = out.rotate((0, 0, 0), (0, 1, 0), ry)
    if abs(rz) > 1e-6:
        out = out.rotate((0, 0, 0), (0, 0, 1), rz)
    bb = out.BoundingBox()
    out = out.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))
    return out


def _inside(solid, x, y, z) -> bool:
    cls = BRepClass3d_SolidClassifier(solid.wrapped, gp_Pnt(float(x), float(y), float(z)), 1e-4)
    return cls.State() == TopAbs_IN


def _hole_open(solid, x, y, z) -> bool:
    bb = solid.BoundingBox()
    if not (bb.xmin - 1 <= x <= bb.xmax + 1 and bb.ymin - 1 <= y <= bb.ymax + 1 and bb.zmin - 1 <= z <= bb.zmax + 1):
        return False
    if _inside(solid, x, y, z):
        return False
    for dx, dy in ((6, 0), (-6, 0), (0, 6), (0, -6)):
        if _inside(solid, x + dx, y + dy, z):
            return True
    return False


def _in_window(x, y) -> bool:
    wx, wy, ww, wd = model.motor_window()
    return abs(x - wx) < ww / 2 + 1 and abs(y - wy) < wd / 2 + 1


def _overlap(a, b) -> float:
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if ba.xmax < bb.xmin - 0.1 or bb.xmax < ba.xmin - 0.1:
        return 0.0
    if ba.ymax < bb.ymin - 0.1 or bb.ymax < ba.ymin - 0.1:
        return 0.0
    if ba.zmax < bb.zmin - 0.1 or bb.zmax < ba.zmin - 0.1:
        return 0.0
    common = a.intersect(b)
    if common is None:
        return 0.0
    try:
        return float(common.Volume())
    except Exception:
        return 0.0


def main() -> int:
    _hex_ok()
    print("building", flush=True)
    prints, assy = model.build()
    errors = []

    plate = next(p.solid for p in prints if p.name == "arm_plate")
    zmax = plate.BoundingBox().zmax
    if abs(zmax - P.PLATE_TOP_LO) > 0.2:
        errors.append(f"arm plate top {zmax:.2f} != {P.PLATE_TOP_LO:.2f}")
    shoulder_lo = zmax + P.SHOULDER_ABOVE_PLATE
    if abs(shoulder_lo - P.SHOULDER_LO) > 0.2:
        errors.append(f"shoulder {shoulder_lo:.2f} != {P.SHOULDER_LO:.2f}")

    for folder in (STL, PLACED, STEP, REPORTS):
        folder.mkdir(parents=True, exist_ok=True)

    rows = []
    total_g = 0.0
    for part in prints:
        print(f"export {part.name}", flush=True)
        try:
            nsolids = len(part.solid.Solids())
            if nsolids != 1:
                errors.append(f"{part.name} is {nsolids} solids")
            vol = float(part.solid.Volume())
            if vol < 10:
                errors.append(f"{part.name} volume {vol:.1f} mm^3")
            oriented = _orient(part.solid, part.rot)
            bb = oriented.BoundingBox()
            size = (bb.xlen, bb.ylen, bb.zlen)
            if size[0] > P.BED + 0.5 or size[1] > P.BED + 0.5:
                errors.append(f"{part.name} bed {size[0]:.1f} x {size[1]:.1f} mm")
            if size[2] > 200:
                errors.append(f"{part.name} too tall {size[2]:.1f} mm")
            cq.exporters.export(oriented, str(STL / f"{part.name}.stl"), tolerance=TOL, angularTolerance=ANG)
            cq.exporters.export(oriented, str(STEP / f"{part.name}.step"))
            mass = vol / 1000.0 * DENSITY
            total_g += mass * part.qty
            rows.append({
                "name": part.name,
                "qty": part.qty,
                "note": part.note,
                "rot_deg": list(part.rot),
                "bed_mm": [round(v, 1) for v in size],
                "volume_mm3": round(vol, 1),
                "mass_g": round(mass, 1),
                "mass_qty_g": round(mass * part.qty, 1),
            })
        except Exception as exc:  # noqa: BLE001 — keep going so one bad part does not hide the next
            errors.append(f"{part.name} export failed: {exc}")
            traceback.print_exc()

    print("placed stl", flush=True)
    for name, solid in assy:
        try:
            cq.exporters.export(solid, str(PLACED / f"{name}.stl"), tolerance=TOL, angularTolerance=ANG)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"placed {name} failed: {exc}")

    print("mates", flush=True)
    tiles = [s for n, s in assy if n.startswith("deck_")]
    splices = [s for n, s in assy if n.startswith("splice_")]
    others = [s for n, s in assy if not n.startswith("deck_") and not n.startswith("splice_")]
    for x, y, kind in model.deck_holes():
        if _in_window(x, y):
            continue
        z_deck = P.DECK_TOP - 1.0
        if not any(_hole_open(t, x, y, z_deck) for t in tiles):
            errors.append(f"deck hole closed at {x:.1f},{y:.1f} ({kind})")
            continue
        if kind == "splice":
            z = P.DECK_TOP - P.SKIN - 3.0
            if not any(_hole_open(s, x, y, z) for s in splices):
                errors.append(f"splice misses deck hole {x:.1f},{y:.1f}")
        else:
            zs = (
                P.DECK_TOP + 2.0,
                P.DECK_TOP - P.SKIN - 2.0,
                P.DECK_TOP - P.SKIN - P.BOSS_EXTRA - 3.0,
            )
            if not any(_hole_open(s, x, y, z) for s in others for z in zs):
                errors.append(f"no part mates deck hole {x:.1f},{y:.1f}")

    print("clearance", flush=True)
    by = {n: s for n, s in assy}
    carriage = by["carriage"]
    for name, solid in assy:
        if name.startswith("tower_") or name in ("arm_plate", "strap_left", "strap_right"):
            hit = _overlap(carriage, solid) if name.startswith("tower_") else 0.0
            if name.startswith("tower_") and hit > 50:
                errors.append(f"carriage hits {name} by {hit:.0f} mm^3")
        if name.startswith("tower_"):
            for other in ("arm_plate", "strap_left", "strap_right"):
                hit = _overlap(by[other], solid)
                if hit > 50:
                    errors.append(f"{other} hits {name} by {hit:.0f} mm^3")
    for deck_name, deck in assy:
        if not deck_name.startswith("deck_"):
            continue
        for other in ("caster_nose", "caster_tail", "pod_left", "pod_right", "elec_tray", "cam_shoe"):
            hit = _overlap(by[other], deck)
            if hit > 50:
                errors.append(f"{other} hits {deck_name} by {hit:.0f} mm^3")
    for roller, caster in (("roller_nose", "caster_nose"), ("roller_tail", "caster_tail")):
        hit = _overlap(by[roller], by[caster])
        if hit > 50:
            errors.append(f"{roller} hits {caster} by {hit:.0f} mm^3")

    print("assembly step", flush=True)
    try:
        assembly = cq.Assembly(name="bob_v3")
        for name, solid in assy:
            assembly.add(solid, name=name)
        assembly.save(str(STEP / "bob_v3.step"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"assembly step failed: {exc}")
        traceback.print_exc()

    manifest = {
        "units": "mm",
        "density_g_cm3": DENSITY,
        "rod_len_mm": P.ROD_LEN,
        "shoulder_lo_mm": round(P.SHOULDER_LO, 1),
        "shoulder_hi_mm": round(P.SHOULDER_HI, 1),
        "travel_mm": round(P.TRAVEL, 1),
        "plate_top_lo_mm": round(P.PLATE_TOP_LO, 1),
        "total_print_mass_g": round(total_g, 1),
        "placed_stl": [f"{name}.stl" for name, _ in assy],
        "parts": rows,
        "errors": errors,
    }
    (REPORTS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"mass {total_g:.0f} g  parts {len(rows)}  errors {len(errors)}")
    for err in errors:
        print("ERROR", err)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
