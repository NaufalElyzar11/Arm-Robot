"""Parametric prototype: real STEP/STL parts, shared URDF frames, validation data.

Units: CAD mm; URDF m. Horns and screws are purchased hardware. This is a
fit-test prototype, not a validated production design or hardware controller.
"""
from pathlib import Path
import csv
import json
import math
import shutil
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "design.json").read_text())
OUT = ROOT / "output"
PKG = ROOT / "ros2_ws" / "src" / "ax12_compact_description"
for folder in (OUT / "stl", OUT / "step", OUT / "coupons", PKG / "meshes", PKG / "urdf"):
    folder.mkdir(parents=True, exist_ok=True)


def box(x, y, z, center):
    return cq.Workplane("XY").box(x, y, z).val().translate(center)


def cylinder(radius, height, start, axis=(0, 1, 0)):
    return cq.Solid.makeCylinder(radius, height, cq.Vector(*start), cq.Vector(*axis))


def fuse(*shapes):
    shape = shapes[0]
    for other in shapes[1:]:
        shape = shape.fuse(other)
    return shape.clean()


def rx90(shape):
    return shape.rotate((0, 0, 0), (1, 0, 0), 90)


def body_mount():
    # ROBOTIS front mounting pattern: x +/-13.5, 8 mm vertical pitch;
    # first row 6.5 mm below output axis. Body face is y=-3 mm.
    shape = box(34, 3, 44, (0, -1.5, -12))
    shape = shape.cut(box(18, 8, 27, (0, -1.5, -16.5)))
    shape = shape.cut(cylinder(12.4, 10, (0, -7, 0)))
    for x in (-13.5, 13.5):
        for z in (-6.5, -14.5, -22.5, -30.5):
            shape = shape.cut(cylinder(1.15, 10, (x, -7, z)))
    return shape.clean()


def horn_blank():
    return cylinder(11, 3, (0, 0.5, 0))


def horn_holes(shape):
    # Official output horn: four tapped M2 holes on 16 mm PCD.
    for x, z, r in [(0, 0, 3.25), (8, 0, 1.15), (-8, 0, 1.15), (0, 8, 1.15), (0, -8, 1.15)]:
        shape = shape.cut(cylinder(r, 12, (x, -5, z)))
    return shape.clean()


def arm_link(length):
    # Horn-side rail stays in front of the parent servo body. Bridge meets
    # stationary mounting rails of the next servo, whose body is behind y=-3.
    bottom = length - 34
    shape = fuse(horn_blank(), box(12, 3, bottom+5, (0, 2, (bottom+5)/2)),
                 box(34, 6.5, 5, (0, 0.25, bottom+2.5)), body_mount().translate((0, 0, length)))
    return horn_holes(shape)


def ax_motor():
    body = box(32, 32, 50, (0, -19, -13.5))
    boss = cylinder(8, 5, (0, -40, 0))
    return fuse(body, boss)


def base():
    h = P["base_axis_height"]
    bottom = box(110, 94, 4, (0, 12, 2))
    top = box(54, 68, 3, (0, 12, h-1.5))
    top = top.cut(cylinder(12.4, 10, (0, 0, h-6), (0, 0, 1)))
    for x in (-13.5, 13.5):
        for y in (6.5, 14.5, 22.5, 30.5):
            top = top.cut(cylinder(1.15, 10, (x, y, h-6), (0, 0, 1)))
    supports = [box(6, 8, h-7, (x, y, (h+1)/2)) for x in (-24, 24) for y in (-14, 40)]
    shape = fuse(bottom, top, *supports)
    for x in (-45, 45):
        for y in (-25, 49):
            shape = shape.cut(cylinder(2.25, 10, (x, y, -2), (0, 0, 1)))
    return shape.clean()


def yaw_adapter():
    h = P["shoulder_height_above_base_axis"]
    disk = rx90(horn_holes(horn_blank()))
    return fuse(disk, box(18, 3, h-34-3.3+1, (0, -1.5, (3.3+h-33)/2)), body_mount().translate((0, 0, h)))


def wrist_adapter():
    length = P["wrist_roll_axis_distance"]
    # Route bridge outside the wrist-roll motor envelope (minimum y=-11.5).
    shape = fuse(horn_blank(), box(12, 3, 24, (0, 2, 12)),
                 box(12, 21.5, 3, (0, -7.25, 22.5)),
                 box(12, 3, length-24+1, (0, -16.5, (24+length+1)/2)),
                 box(20, 16, 3, (0, -10, length-1.5)),
                 rx90(body_mount()).translate((0, 0, length)))
    # Restore clearance around roll horn after joining bridge.
    shape = shape.cut(cylinder(12.4, 8, (0, 0, length-4), (0, 0, 1)))
    return horn_holes(shape)


MG_HOLES = [(-8.35, -20), (-8.35, -9), (19.15, -20), (19.15, -9)]


def mg_cradle(z_shift=0):
    # Adjustable strap mounting avoids relying on variant-specific tab holes.
    z = P["mg90s_axis_height"] + z_shift
    floor = box(31.5, 25, 3, (5.4, -15.5, z-8))
    walls = [box(4, 25, 13.5, (x, -15.5, z-0.5)) for x in (-8.35, 19.15)]
    back = box(31.5, 2.5, 13.5, (5.4, -26.75, z-0.5))
    s = fuse(floor, back, *walls)
    s = s.cut(box(8, 5, 6, (5.4, -26.75, z-2)))  # Cable exit relief.
    for x, y in MG_HOLES:
        s = s.cut(cylinder(1.15, 22, (x, y, z-11), (0, 0, 1)))
    return s.clean()


def mg_cap():
    z = P["mg90s_axis_height"]
    s = box(31.5, 25, 2.4, (5.4, -15.5, z+7.45))
    for x, y in MG_HOLES:
        s = s.cut(cylinder(1.15, 8, (x, y, z+4), (0, 0, 1)))
    return s.clean()


def hand():
    disk = rx90(horn_holes(horn_blank()))
    floor_z = P["mg90s_axis_height"]-9.5
    supports = [box(4, 8, floor_z-3, (x, -7, (floor_z+3)/2)) for x in (-4, 4)]
    bridge = box(43.5, 6, 3, (11.4, 0, floor_z-1))
    fixed_jaw = box(4, 8, 45, (31, 0, floor_z+22.5))
    # Flat pad surface at x=27; stick on a thin rubber/foam gripping pad.
    pad = box(2, 8, 26, (28, 0, floor_z+32))
    return fuse(disk, *supports, mg_cradle(), bridge, fixed_jaw, pad)


def finger():
    shape = fuse(cylinder(8, 3, (0, 0.7, 0)), box(6, 3, P["finger_length"], (0, 2.2, P["finger_length"]/2)))
    shape = shape.cut(cylinder(2.6, 10, (0, -3, 0)))
    # Slots fasten to supplied plastic horn, not directly to a printed spline.
    for z in (-5.5, 5.5):
        hole = fuse(cylinder(0.9, 10, (0, -3, z-1.1)), cylinder(0.9, 10, (0, -3, z+1.1)), box(1.8, 10, 2.2, (0, 2, z)))
        shape = shape.cut(hole)
    return shape.clean()


def mg_motor():
    return box(22.8, 22, 12.2, (5.4, -14, P["mg90s_axis_height"]))


PARTS = {
    "base_stand": (base(), "base_link", 1),
    "yaw_shoulder_adapter": (yaw_adapter(), "yaw_link", 1),
    "upper_link": (arm_link(P["upper_axis_distance"]), "upper_link", 1),
    "forearm_link": (arm_link(P["forearm_axis_distance"]), "forearm_link", 1),
    "wrist_adapter": (wrist_adapter(), "wrist_link", 1),
    "gripper_body": (hand(), "hand_link", 1),
    "gripper_cap": (mg_cap(), "hand_link", 1),
    "moving_finger": (finger(), "finger_link", 1),
}

H = P["base_axis_height"]
SH = P["shoulder_height_above_base_axis"]
U = P["upper_axis_distance"]
F = P["forearm_axis_distance"]
W = P["wrist_roll_axis_distance"]

# Origins refer to actual motor axes; CAD geometry stays local to these frames.
JOINTS = [
    ("base_yaw", "base_link", "yaw_link", (0, 0, H), (0, 0, 1), -1.57, 1.57, 0.30),
    ("shoulder_pitch", "yaw_link", "upper_link", (0, 0, SH), (0, 1, 0), -0.65, 0.65, 0.30),
    ("elbow_pitch", "upper_link", "forearm_link", (0, 0, U), (0, 1, 0), -0.85, 0.85, 0.30),
    ("wrist_pitch", "forearm_link", "wrist_link", (0, 0, F), (0, 1, 0), -0.70, 0.70, 0.30),
    ("wrist_roll", "wrist_link", "hand_link", (0, 0, W), (0, 0, 1), -1.0, 1.0, 0.30),
    ("gripper", "hand_link", "finger_link", (0, 0, P["mg90s_axis_height"]), (0, 1, 0), 0.0, 0.70, 0.035),
]

MOTORS = {
    "base_link": (rx90(ax_motor()).translate((0, 0, H)), P["ax12_mass_kg"]),
    "yaw_link": (ax_motor().translate((0, 0, SH)), P["ax12_mass_kg"]),
    "upper_link": (ax_motor().translate((0, 0, U)), P["ax12_mass_kg"]),
    "forearm_link": (ax_motor().translate((0, 0, F)), P["ax12_mass_kg"]),
    "wrist_link": (rx90(ax_motor()).translate((0, 0, W)), P["ax12_mass_kg"]),
    "hand_link": (mg_motor(), P["mg90s_mass_kg"]),
}


def export_shape(shape, path):
    if path.suffix == ".stl":
        cq.exporters.export(shape, str(path), tolerance=0.05, angularTolerance=0.1)
    else:
        cq.exporters.export(shape, str(path))


def mesh_of(shape):
    vs, fs = shape.tessellate(0.05, 0.1)
    mesh = trimesh.Trimesh(vertices=[v.toTuple() for v in vs], faces=fs, process=True)
    return mesh


def aggregate_mass(elements):
    mass = sum(m for _, m in elements)
    centers = [np.array(s.Center().toTuple())*0.001 for s, _ in elements]
    com = sum(c*m for c, (_, m) in zip(centers, elements))/mass
    inertia = np.zeros((3, 3))
    for (shape, m), c in zip(elements, centers):
        mesh = mesh_of(shape)
        intrinsic = mesh.moment_inertia * (m / mesh.volume) * 1e-6
        r = c-com
        inertia += intrinsic + m*(np.eye(3)*np.dot(r, r)-np.outer(r, r))
    return mass, com, inertia


def sub(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def vec(v):
    return " ".join(f"{n:.9g}" for n in v)


def main():
    manifest = []
    assets = {}
    properties = {}
    for name, (shape, link, qty) in PARTS.items():
        assert shape.isValid(), name
        assert len(shape.Solids()) == 1, (name, len(shape.Solids()))
        export_shape(shape, OUT / "step" / f"{name}.step")
        # Manufacturing STL is translated to bed; link-local STL stays unchanged.
        bb = shape.BoundingBox()
        oriented = rx90(shape) if name in ("upper_link", "forearm_link", "moving_finger", "yaw_shoulder_adapter") else shape
        bed_bb = oriented.BoundingBox()
        on_bed = oriented.translate((-(bed_bb.xmin+bed_bb.xmax)/2, -(bed_bb.ymin+bed_bb.ymax)/2, -bed_bb.zmin))
        export_shape(on_bed, OUT / "stl" / f"{name}.stl")
        export_shape(shape, PKG / "meshes" / f"{name}.stl")
        mesh = trimesh.load_mesh(OUT / "stl" / f"{name}.stl")
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, name
        assert len(mesh.split()) == 1, name
        assets.setdefault(link, []).append((name, shape, "printed"))
        manifest.append({"part": name, "quantity": qty, "link": link, "solid_PLA_mass_g": shape.Volume()*P["pla_density_kg_per_mm3"]*1000, "x_mm": bb.xlen, "y_mm": bb.ylen, "z_mm": bb.zlen, "watertight": True})
    for link, (shape, _) in MOTORS.items():
        name = f"{link}_servo_envelope"
        export_shape(shape, PKG / "meshes" / f"{name}.stl")
        assets.setdefault(link, []).append((name, shape, "motor"))
    coupons = {"ax12_body_mount": body_mount(), "ax12_horn_pattern": horn_holes(horn_blank()), "mg90s_cradle": mg_cradle(), "mg90s_cap": mg_cap(), "mg90s_horn_slots": finger()}
    for name, shape in coupons.items():
        assert shape.isValid() and len(shape.Solids()) == 1
        # Front mounting/horn plates laid flat; cradle and cap already horizontal.
        if name in ("ax12_body_mount", "ax12_horn_pattern", "mg90s_horn_slots"):
            shape = rx90(shape)
        bb = shape.BoundingBox()
        shape = shape.translate((-(bb.xmin+bb.xmax)/2, -(bb.ymin+bb.ymax)/2, -bb.zmin))
        export_shape(shape, OUT / "coupons" / f"{name}.stl")
        m = trimesh.load_mesh(OUT / "coupons" / f"{name}.stl")
        assert m.is_watertight and len(m.split()) == 1
    robot = ET.Element("robot", name=P["name"])
    robot.append(ET.Comment("Prototype geometry. Mass/inertia estimated from solid PLA and uniform motor envelopes; not calibrated hardware."))
    sub(robot, "link", name="world")  # Massless root avoids KDL root-inertia loss.
    for name, rgba in [("frame", "0.08 0.48 0.62 1"), ("servo", "0.16 0.18 0.21 1")]:
        sub(sub(robot, "material", name=name), "color", rgba=rgba)
    for link, items in assets.items():
        node = sub(robot, "link", name=link)
        elements = []
        for name, shape, kind in items:
            mass = shape.Volume()*P["pla_density_kg_per_mm3"] if kind == "printed" else MOTORS[link][1]
            elements.append((shape, mass))
            for tag in ("visual", "collision"):
                visual = sub(node, tag, name=name)
                geometry = sub(visual, "geometry")
                sub(geometry, "mesh", filename=f"package://ax12_compact_description/meshes/{name}.stl", scale="0.001 0.001 0.001")
                if tag == "visual":
                    sub(visual, "material", name="frame" if kind == "printed" else "servo")
        mass, com, inertia = aggregate_mass(elements)
        properties[link] = {"mass_kg": mass, "com_m": com.tolist(), "inertia_kg_m2": inertia.tolist()}
        node = sub(node, "inertial")
        sub(node, "origin", xyz=vec(com), rpy="0 0 0")
        sub(node, "mass", value=f"{mass:.9g}")
        sub(node, "inertia", ixx=inertia[0, 0], ixy=inertia[0, 1], ixz=inertia[0, 2], iyy=inertia[1, 1], iyz=inertia[1, 2], izz=inertia[2, 2])
    for name, parent, child, origin, axis, low, high, effort in JOINTS:
        node = sub(robot, "joint", name=name, type="revolute")
        sub(node, "parent", link=parent)
        sub(node, "child", link=child)
        sub(node, "origin", xyz=vec(np.array(origin)*0.001), rpy="0 0 0")
        sub(node, "axis", xyz=vec(axis))
        sub(node, "limit", lower=low, upper=high, effort=effort, velocity=0.35)
    anchor = sub(robot, "joint", name="world_to_base", type="fixed")
    sub(anchor, "parent", link="world")
    sub(anchor, "child", link="base_link")
    sub(anchor, "origin", xyz="0 0 0", rpy="0 0 0")
    ET.indent(robot, space="  ")
    ET.ElementTree(robot).write(PKG / "urdf" / "ax12_compact.urdf", encoding="utf-8", xml_declaration=True)
    # STEP assembly in the vertical zero pose, with individually named solids.
    origins = {"base_link": np.zeros(3)}
    for _, parent, child, xyz, *_ in JOINTS:
        origins[child] = origins[parent] + np.array(xyz)
    asm = cq.Assembly(name=P["name"])
    for link, items in assets.items():
        for name, shape, kind in items:
            color = cq.Color(0.08, 0.48, 0.62) if kind == "printed" else cq.Color(0.16, 0.18, 0.21)
            asm.add(shape, name=name, loc=cq.Location(cq.Vector(*origins[link])), color=color)
    asm.export(str(OUT / "assembly.step"))
    with (OUT / "parts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest[0])
        writer.writeheader()
        writer.writerows(manifest)
    (OUT / "mass_properties.json").write_text(json.dumps(properties, indent=2))
    print(json.dumps({"printed_parts": len(PARTS), "coupons": len(coupons), "all_part_meshes_closed": True, "total_solid_PLA_g": sum(x["solid_PLA_mass_g"] for x in manifest), "urdf": str(PKG / "urdf" / "ax12_compact.urdf")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
