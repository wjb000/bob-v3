#!/usr/bin/env python3
"""Generate the MuJoCo model of Bob v3 from the CAD build.

    .venv/bin/python sim/build_mjcf.py

Reads cad/scene.json and cad/placed/*.stl (written by cad/export.py), writes
  sim/assets/*.stl     meshes in each link's frame, metres
  sim/bob_v3.xml       the robot (free-floating base), floor and lights
  sim/scene.xml        bob_v3.xml plus a kitchen counter, a shelf and objects

Everything the sim knows comes from the CAD: link masses are the printed
volumes at the print fill plus listed masses of bought parts; joint axes and
limits are the CAD joints; actuator limits are the datasheet torques.
"""

from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads((ROOT / "cad" / "scene.json").read_text())
PLACED = ROOT / "cad" / "placed"
ASSETS = ROOT / "sim" / "assets"
OUT = ROOT / "sim"

# Wiring, screws, inserts and paint are not in the CAD. Book them where they sit.
MISC_G = {"base": 1200.0, "lift": 400.0, "lift_upper": 60.0, "lift_mid": 100.0}

# Actuator models. Torques from the datasheets; armature is the reflected rotor
# inertia (an estimate); kp/kv are the gains used for position control.
ACT = {
    # Direct Feetech bus servos, Nori A3 grades. Stall is the force limit; rated is what sim/check.py uses.
    "sts3095": dict(force=9.32, rated=2.21, kp=80.0, kv=1.2, armature=0.012, damping=0.08, frictionloss=0.06, vel=3.25),
    "sts3250": dict(force=4.9, rated=1.57, kp=60.0, kv=0.8, armature=0.005, damping=0.05, frictionloss=0.04, vel=7.8),
    "sts3215": dict(force=2.94, rated=0.98, kp=40.0, kv=0.6, armature=0.004, damping=0.05, frictionloss=0.03, vel=4.8),
    # gripper: STS3215 through a 12 mm pitch-radius pinion, torque limit set to ~0.5 N·m -> ~40 N per finger
    "sts3215g": dict(force=40.0, rated=25.0, kp=2500.0, kv=60.0, armature=0.4, damping=5.0, frictionloss=0.8, vel=0.06),
    "nema": dict(force=380.0, rated=250.0, kp=60000.0, kv=9000.0, armature=0.0, damping=1000.0, frictionloss=15.0, vel=0.03),
    # DDSM115: 2.0 N·m locked, 0.96 rated, 200 rpm no-load, direct drive
    "hub": dict(force=2.0, rated=0.96, kv=1.5, armature=0.004, damping=0.01, frictionloss=0.02, vel=13.9),  # 133 rpm at 12 V
}
# Collision classes: bit 1 floor, 2 body shell, 4 arm, 8 objects
CLS = {
    "floor": (1, 1),
    "wheel": (1, 0),
    "body": (2, 1 | 4 | 8),
    "arm": (4, 1 | 2 | 4 | 8),
    "obj": (8, 15),
}
COLORS = {
    "shell": "0.085 0.09 0.10 1", "dark": "0.05 0.05 0.055 1", "frame": "0.16 0.17 0.19 1", "accent": "0.0 0.5 1.0 1",
    "actuator": "0.20 0.20 0.22 1", "electronics": "0.20 0.45 0.30 1", "battery": "0.35 0.55 0.20 1",
    "metal": "0.75 0.76 0.78 1", "wheel": "0.10 0.10 0.10 1",
    # looks of the modelled bought parts
    "anodised": "0.17 0.17 0.19 1", "alu": "0.78 0.79 0.81 1", "steel": "0.62 0.63 0.66 1", "chrome": "0.85 0.86 0.88 1",
    "brass": "0.80 0.62 0.28 1", "copper": "0.78 0.45 0.25 1", "black": "0.05 0.05 0.055 1", "white": "0.085 0.09 0.10 1",
    "grey": "0.40 0.40 0.42 1", "yellow": "0.95 0.75 0.10 1", "red": "0.82 0.10 0.10 1", "green": "0.15 0.55 0.25 1",
    "rubber": "0.07 0.07 0.07 1", "pcb": "0.10 0.40 0.20 1", "pcb_black": "0.06 0.07 0.07 1", "pcb_blue": "0.10 0.25 0.60 1",
    "glass": "0.05 0.06 0.08 1", "lens": "0.10 0.12 0.30 1", "smoke": "0.20 0.20 0.22 1", "eye": "0.25 0.85 1.0 1", "glow": "0.30 0.85 1.0 1",
}


def link_origins():
    org = {"base": np.zeros(3)}
    for j in SCENE["joints"]:
        org[j["child"]] = np.asarray(j["anchor"], float) / 1000.0
    return org


def collides(item):
    """Which items take part in contact, and as what."""
    n, link, kind = item["name"], item["link"], item["kind"]
    if kind != "print":
        return None
    if link == "base":
        return "body" if n.startswith(("base_shell_", "col_outer_")) else None
    if link == "lift_mid":
        return "body" if n.startswith("col_mid_") else None
    if link == "lift_upper":
        return "body" if n.startswith("col_upper_") else None
    if link == "lift":
        return "body" if (n.startswith("torso_") and not n.startswith("torso_back")) or n.startswith("col_inner_") else None
    if link.startswith("head"):
        return "body" if n.startswith(("head_shell", "visor")) else None
    if link.startswith(("l_", "r_")):
        return "arm"
    return None


def inertia_of(meshes):
    """[(mesh_in_link_frame, mass_kg)] -> mass, com, full inertia about com."""
    m_tot = sum(m for _, m in meshes)
    com = sum(m * (mesh.center_mass if mesh.is_watertight else mesh.bounds.mean(0)) for mesh, m in meshes) / m_tot
    I = np.zeros((3, 3))
    for mesh, m in meshes:
        if m <= 0:
            continue
        if mesh.is_watertight and mesh.volume > 1e-9:
            c = mesh.center_mass
            Ic = mesh.moment_inertia * (m / mesh.mass) if mesh.mass > 0 else np.zeros((3, 3))
        else:
            c = mesh.bounds.mean(0)
            e = mesh.extents
            Ic = np.diag([e[1] ** 2 + e[2] ** 2, e[0] ** 2 + e[2] ** 2, e[0] ** 2 + e[1] ** 2]) * m / 12.0
        d = c - com
        I += Ic + m * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    # keep it physical
    w, v = np.linalg.eigh(I)
    w = np.maximum(w, 1e-6)
    I = v @ np.diag(w) @ v.T
    return m_tot, com, I


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for f in ASSETS.glob("*.stl"):
        f.unlink()
    org = link_origins()
    children = {}
    for j in SCENE["joints"]:
        children.setdefault(j["parent"], []).append(j)
    by_link = {}
    meshes_for_inertia = {}
    for it in SCENE["items"]:
        mesh = trimesh.load_mesh(PLACED / it["file"])
        mesh.apply_scale(0.001)
        mesh.apply_translation(-org[it["link"]])
        # MuJoCo rejects very thin meshes for inertia; we give it explicit inertials instead.
        out = ASSETS / it["file"]
        mesh.export(out)
        by_link.setdefault(it["link"], []).append(it)
        meshes_for_inertia.setdefault(it["link"], []).append((mesh, it["mass_g"] / 1000.0))

    def add_misc(link):
        if link in MISC_G and meshes_for_inertia.get(link):
            box = trimesh.util.concatenate([m for m, _ in meshes_for_inertia[link]])
            meshes_for_inertia[link].append((trimesh.creation.box(extents=box.extents * 0.6,
                                                                   transform=trimesh.transformations.translation_matrix(box.bounds.mean(0))),
                                             MISC_G[link] / 1000.0))

    for link in list(meshes_for_inertia):
        add_misc(link)

    lines = []
    w = lines.append
    w('<mujoco model="bob_v3">')
    w("  <!-- Generated by sim/build_mjcf.py from cad/scene.json. Do not edit by hand. -->")
    w('  <compiler angle="radian" autolimits="true" meshdir="assets"/>')
    w('  <option timestep="0.002" integrator="implicitfast" cone="elliptic" impratio="10"/>')
    w('  <size memory="64M"/>')
    w("  <visual><global offwidth=\"1600\" offheight=\"1200\"/><quality shadowsize=\"4096\"/><headlight ambient=\"0.35 0.35 0.35\" diffuse=\"0.5 0.5 0.5\"/></visual>")
    w("  <default>")
    w('    <geom contype="0" conaffinity="0" group="1"/>')
    w('    <default class="col"><geom group="3" rgba="0.9 0.2 0.2 0.25"/></default>')
    w("  </default>")
    w("  <asset>")
    for c, rgba in COLORS.items():
        extra = ' emission="1.2"' if c in ("eye", "glow") else ' reflectance="0.15"' if c in ("alu", "chrome", "steel") else ""
        w(f'    <material name="m_{c}" rgba="{rgba}" specular="0.4" shininess="0.5"{extra}/>')
    w('    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.93 0.94 0.96" rgb2="0.62 0.66 0.72" width="512" height="512"/>')
    w('    <texture name="grid" type="2d" builtin="checker" rgb1="0.82 0.80 0.76" rgb2="0.76 0.74 0.70" width="512" height="512"/>')
    w('    <material name="floor" texture="grid" texrepeat="8 8" reflectance="0.05"/>')
    for it in SCENE["items"]:
        w(f'    <mesh name="{it["name"]}" file="{it["file"]}"/>')
    w("  </asset>")

    joints_by_child = {j["child"]: j for j in SCENE["joints"]}
    sensors, actuators, equalities = [], [], []

    def body(link, indent):
        pad = "  " * indent
        if link == "base":
            w(f'{pad}<body name="base" pos="0 0 0.002">')
            w(f'{pad}  <freejoint name="root"/>')
            w(f'{pad}  <site name="imu" pos="0.13 -0.04 0.14" size="0.01"/>')
        else:
            j = joints_by_child[link]
            pos = org[link] - org[j["parent"]]
            w(f'{pad}<body name="{link}" pos="{pos[0]:.5f} {pos[1]:.5f} {pos[2]:.5f}">')
            a = ACT.get(j["actuator"], dict(damping=0, armature=0, frictionloss=0, kp=0, kv=0, force=0, vel=0))
            if j["kind"] == "slide":
                lo, hi = j["range"]
                w(f'{pad}  <joint name="{j["name"]}" type="slide" axis="{" ".join(map(str, j["axis"]))}" range="{lo} {hi}" '
                  f'damping="{a["damping"]}" armature="{a.get("armature", 0)}" frictionloss="{a["frictionloss"]}"/>')
            elif j["name"].startswith("wheel"):
                w(f'{pad}  <joint name="{j["name"]}" type="hinge" axis="{" ".join(map(str, j["axis"]))}" damping="{a["damping"]}" '
                  f'armature="{a["armature"]}" frictionloss="{a["frictionloss"]}"/>')
            else:
                lo, hi = j["range"]
                w(f'{pad}  <joint name="{j["name"]}" type="hinge" axis="{" ".join(map(str, j["axis"]))}" range="{lo} {hi}" '
                  f'damping="{a["damping"]}" armature="{a["armature"]}" frictionloss="{a["frictionloss"]}"/>')
            sensors.append(f'    <jointpos name="q_{j["name"]}" joint="{j["name"]}"/>')
            if j.get("mimic"):
                coef = float(j.get("mimic_coef") or 1.0)
                equalities.append(f'    <joint joint1="{j["name"]}" joint2="{j["mimic"]}" polycoef="0 {coef} 0 0 0" solref="0.005 1"/>')
            elif j["name"].startswith("wheel"):
                actuators.append(f'    <velocity name="{j["name"]}" joint="{j["name"]}" kv="{a["kv"]}" ctrlrange="{-a["vel"]} {a["vel"]}" '
                                 f'forcerange="{-a["force"]} {a["force"]}"/>')
            else:
                lo, hi = j["range"]
                actuators.append(f'    <position name="{j["name"]}" joint="{j["name"]}" kp="{a["kp"]}" kv="{a["kv"]}" '
                                 f'ctrlrange="{lo} {hi}" forcerange="{-a["force"]} {a["force"]}"/>')
        m, com, I = inertia_of(meshes_for_inertia.get(link, []))
        w(f'{pad}  <inertial pos="{com[0]:.5f} {com[1]:.5f} {com[2]:.5f}" mass="{m:.4f}" '
          f'fullinertia="{I[0,0]:.6g} {I[1,1]:.6g} {I[2,2]:.6g} {I[0,1]:.6g} {I[0,2]:.6g} {I[1,2]:.6g}"/>')
        for it in by_link.get(link, []):
            col = collides(it)
            mat = f"m_{it['color']}" if it["color"] in COLORS else f"m_{it['kind']}"
            grp = 1 if it["kind"] == "print" else 2
            w(f'{pad}  <geom name="{it["name"]}" type="mesh" mesh="{it["name"]}" material="{mat}" group="{grp}" mass="0"/>')
            if col and it["name"].startswith("finger_"):
                # The rack and the blade are one print, but their convex hull would fill the grasp gap.
                # Collide with the blade only, as a box.
                mesh = meshes_for_inertia[link][[x["name"] for x in by_link[link]].index(it["name"])][0]
                v = mesh.vertices
                low = v[v[:, 2] < v[:, 2].min() + 0.050]
                lo, hi = low.min(0), low.max(0)
                c, e = (lo + hi) / 2, (hi - lo) / 2
                ct, ca = CLS[col]
                w(f'{pad}  <geom name="c_{it["name"]}" class="col" type="box" pos="{c[0]:.4f} {c[1]:.4f} {c[2]:.4f}" '
                  f'size="{e[0]:.4f} {e[1]:.4f} {e[2]:.4f}" contype="{ct}" conaffinity="{ca}" friction="0.8 0.01 0.001" mass="0"/>')
            elif col:
                ct, ca = CLS[col]
                fr = "1.5 0.02 0.002" if it["name"].startswith("finger_") else "0.8 0.01 0.001"
                w(f'{pad}  <geom name="c_{it["name"]}" class="col" type="mesh" mesh="{it["name"]}" contype="{ct}" conaffinity="{ca}" '
                  f'friction="{fr}" mass="0"/>')
        if link.startswith("wheel"):
            d = SCENE["dims"]
            ct, ca = CLS["wheel"]
            # A sphere of the tire radius rolls without the edge chatter a cylinder gets on a plane.
            w(f'{pad}  <geom name="tire_{link}" class="col" type="sphere" size="{d["wheel_od"] / 2000:.4f}" '
              f'contype="{ct}" conaffinity="{ca}" friction="1.0 0.005 0.0001" condim="3" mass="0"/>')
        if link == "base":
            d = SCENE["dims"]
            ct, ca = CLS["wheel"]
            r = d["caster_wheel"] / 2000
            for sx, nm in ((1, "front"), (-1, "rear")):
                x = (d["caster_x"] if sx > 0 else -d.get("caster_x_rear", d["caster_x"])) / 1000 - d["caster_trail"] / 1000
                w(f'{pad}  <geom name="caster_{nm}" class="col" type="sphere" size="{r:.4f}" pos="{x:.4f} 0 {r:.4f}" '
                  f'contype="{ct}" conaffinity="{ca}" condim="1" priority="1" friction="0 0 0" mass="0"/>')  # swivel casters: no drag
        if link == "head_tilt":
            cam = next(i for i in SCENE["items"] if i["name"] == "head_cam_glass")
            mesh = trimesh.load_mesh(PLACED / cam["file"])
            c = mesh.bounds.mean(0) / 1000 - org[link]
            front = mesh.bounds[1][0] / 1000 - org[link][0]
            w(f'{pad}  <camera name="head_cam" pos="{front:.4f} {c[1]:.4f} {c[2]:.4f}" xyaxes="0 -1 0 0 0 1" fovy="70"/>')
        if link in ("l_link6", "r_link6"):
            side = link[0]
            cam = next(i for i in SCENE["items"] if i["name"] == f"wrist_cam_{side}")
            mesh = trimesh.load_mesh(PLACED / cam["file"])
            c = mesh.bounds.mean(0) / 1000 - org[link]
            # looks down the fingers, tipped forward 20 degrees
            w(f'{pad}  <camera name="wrist_cam_{side}" pos="{c[0]:.4f} {c[1]:.4f} {c[2]:.4f}" xyaxes="0 {-1 if side == "l" else -1} 0 0.94 0 0.34" fovy="80"/>')
            tip = SCENE_TIP[side] - org[link]
            w(f'{pad}  <site name="tcp_{side}" pos="{tip[0]:.4f} {tip[1]:.4f} {tip[2]:.4f}" size="0.006" rgba="1 0.3 0 1"/>')
        for fl, padname in (("link7", "a"), ("link8", "b")):
            if link != f"{link[0]}_{fl}" or not link.startswith(("l_", "r_")):
                continue
            side = link[0]
            pad_it = next(i for i in SCENE["items"] if i["name"] == f"finger_{padname}_{side}")
            pm = trimesh.load_mesh(PLACED / pad_it["file"])
            pc = pm.bounds.mean(0) / 1000 - org[link]
            pe = pm.extents / 2000
            w(f'{pad}  <site name="touch_{padname}_{side}" type="box" pos="{pc[0]:.4f} {pc[1]:.4f} {pc[2]:.4f}" '
              f'size="{pe[0] + 0.001:.4f} {pe[1] + 0.003:.4f} {pe[2] + 0.001:.4f}" rgba="0 0 0 0"/>')
            sensors.append(f'    <touch name="touch_{padname}_{side}" site="touch_{padname}_{side}"/>')
        for j in children.get(link, []):
            body(j["child"], indent + 1)
        w(f"{pad}</body>")

    w("  <worldbody>")
    w('    <light name="sun" pos="1.5 -1.5 3" dir="-0.5 0.5 -1" directional="true" castshadow="true" diffuse="0.7 0.7 0.7"/>')
    ct, ca = CLS["floor"]
    w(f'    <geom name="floor" type="plane" size="0 0 0.05" material="floor" contype="{ct}" conaffinity="{ca}" group="0" friction="1 0.01 0.001"/>')
    body("base", 2)
    w("  </worldbody>")
    # Nested column stages slide inside each other; the torso is a child of lift.
    w("  <contact>")
    w('    <exclude body1="base" body2="lift"/>')
    w('    <exclude body1="base" body2="lift_mid"/>')
    w('    <exclude body1="base" body2="lift_upper"/>')
    w('    <exclude body1="lift_mid" body2="lift_upper"/>')
    w('    <exclude body1="lift_upper" body2="lift"/>')
    w('    <exclude body1="lift_mid" body2="lift"/>')
    w('    <exclude body1="lift" body2="head_tilt"/>')
    for s in ("l", "r"):
        w(f'    <exclude body1="lift" body2="{s}_link2"/>')
        w(f'    <exclude body1="{s}_link5" body2="{s}_link7"/>')
        w(f'    <exclude body1="{s}_link5" body2="{s}_link8"/>')
        w(f'    <exclude body1="{s}_link7" body2="{s}_link8"/>')
    w("  </contact>")
    w("  <equality>")
    lines.extend(equalities)
    w("  </equality>")
    w("  <actuator>")
    lines.extend(actuators)
    w("  </actuator>")
    w("  <sensor>")
    lines.extend(sensors)
    w('    <accelerometer name="imu_acc" site="imu"/>')
    w('    <gyro name="imu_gyro" site="imu"/>')
    w("  </sensor>")
    w("</mujoco>")
    xml = "\n".join(lines) + "\n"
    (OUT / "bob_v3.xml").write_text(xml)
    xml = xml.replace("</mujoco>", keyframes() + "</mujoco>")
    (OUT / "bob_v3.xml").write_text(xml)
    print(f"wrote sim/bob_v3.xml with {len(SCENE['items'])} meshes, {len(actuators)} actuators, {len(SCENE['poses'])} keyframes")


def keyframes() -> str:
    """One keyframe per CAD pose: qpos and matching position targets."""
    import mujoco

    m = mujoco.MjModel.from_xml_path(str(OUT / "bob_v3.xml"))
    out = ["  <keyframe>"]
    for name, pose in SCENE["poses"].items():
        q = m.qpos0.copy()
        q[2] = 0.002
        ctrl = np.zeros(m.nu)
        for i in range(m.nu):
            jn = m.joint(m.actuator_trnid[i, 0]).name
            v = pose.get(jn, 0.0)
            q[m.jnt_qposadr[m.actuator_trnid[i, 0]]] = v
            ctrl[i] = 0.0 if jn.startswith("wheel") else v
        # Mimic joints (column tubes, second finger) start where their equality puts them,
        # so a keyframe does not open with the tubes snapping into place.
        for j in SCENE["joints"]:
            if j.get("mimic"):
                q[m.jnt_qposadr[m.joint(j["name"]).id]] = pose.get(j["mimic"], 0.0) * float(j.get("mimic_coef") or 1.0)
        out.append(f'    <key name="{name}" qpos="{" ".join(f"{v:.6g}" for v in q)}" ctrl="{" ".join(f"{v:.6g}" for v in ctrl)}"/>')
    out.append("  </keyframe>")
    return "\n".join(out) + "\n"


def _tip_points():
    """Fingertip midpoint (tool centre) at the zero pose, metres, from the pad meshes."""
    out = {}
    for side in ("l", "r"):
        a = trimesh.load_mesh(PLACED / f"finger_a_{side}.stl").bounds / 1000
        b = trimesh.load_mesh(PLACED / f"finger_b_{side}.stl").bounds / 1000
        lo = np.minimum(a[0], b[0])
        hi = np.maximum(a[1], b[1])
        c = (lo + hi) / 2
        c[2] = lo[2] + 0.018  # 18 mm up from the fingertips, middle of the pads
        out[side] = c
    return out


SCENE_TIP = _tip_points()

if __name__ == "__main__":
    main()
