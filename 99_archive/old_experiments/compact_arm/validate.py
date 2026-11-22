"""Check topology, CAD intersections, URDF tree, and static gravity torque."""
import json
import math
import itertools
from pathlib import Path
import xml.etree.ElementTree as ET

import cadquery as cq
import numpy as np
from scipy.spatial.transform import Rotation
from urdf_parser_py.urdf import URDF

import build as b


def transforms(angles):
    frames = {"base_link": np.eye(4)}
    axes = {}
    for name, parent, child, xyz, axis, *_ in b.JOINTS:
        local = np.eye(4)
        local[:3, 3] = xyz
        joint = frames[parent] @ local
        axes[name] = (joint[:3, 3], joint[:3, :3] @ np.array(axis))
        local[:3, :3] = Rotation.from_rotvec(np.array(axis)*angles.get(name, 0)).as_matrix()
        frames[child] = frames[parent] @ local
    return frames, axes


def place(shape, frame):
    rv = Rotation.from_matrix(frame[:3, :3]).as_rotvec()
    angle = np.linalg.norm(rv)
    if angle > 1e-10:
        shape = shape.rotate((0, 0, 0), tuple(rv/angle), math.degrees(angle))
    return shape.translate(tuple(frame[:3, 3]))


def items_at(angles):
    frames, _ = transforms(angles)
    items = [(name, link, place(shape, frames[link])) for name, (shape, link, _) in b.PARTS.items()]
    items += [(f"{link}_motor", link, place(shape, frames[link])) for link, (shape, _) in b.MOTORS.items()]
    return items


def collisions(angles):
    items = items_at(angles)
    results = []
    for (na, la, a), (nb, lb, other) in itertools.combinations(items, 2):
        aa, bb = a.BoundingBox(), other.BoundingBox()
        if any(min(getattr(aa, d+"max"), getattr(bb, d+"max"))-max(getattr(aa, d+"min"), getattr(bb, d+"min")) < 0.001 for d in "xyz"):
            continue
        common = a.intersect(other)
        volume = sum(s.Volume() for s in common.Solids())
        if volume > 0.01:
            results.append({"a": na, "b": nb, "overlap_mm3": round(volume, 4), "same_link": la == lb})
    return results


def static_torques(angles, payload_kg=0.0):
    properties = json.loads((b.OUT / "mass_properties.json").read_text())
    frames, axes = transforms(angles)
    order = ["base_link"] + [j[2] for j in b.JOINTS]
    points = {}
    for link, props in properties.items():
        com_mm = np.array(props["com_m"])*1000
        points[link] = (frames[link][:3, :3] @ com_mm + frames[link][:3, 3], props["mass_kg"])
    # Conservative test-object center close to fixed jaw; no grasp force claim.
    payload_pos = frames["hand_link"] @ np.array([20, 0, 58, 1])
    values = {}
    for name, _, child, *_ in b.JOINTS:
        origin, axis = axes[name]
        torque = np.zeros(3)
        for link in order[order.index(child):]:
            pos, mass = points[link]
            torque += np.cross((pos-origin)*.001, [0, 0, -mass*9.81])
        if name != "gripper":
            torque += np.cross((payload_pos[:3]-origin)*.001, [0, 0, -payload_kg*9.81])
        values[name] = float(np.dot(torque, axis))
    return values


def main():
    path = b.PKG / "urdf" / "ax12_compact.urdf"
    robot = URDF.from_xml_file(str(path))
    assert robot.get_root() == "world"
    assert len(robot.joints) == 7 and len(robot.links) == 8
    assert sum(j.type == "revolute" for j in robot.joints) == 6
    assert set(robot.link_map) == {"world"} | {j.child for j in robot.joints}
    assert len(robot.get_chain("base_link", "finger_link", links=False)) == 6
    for link in robot.links:
        if link.name == "world":
            continue
        tensor = link.inertial.inertia.to_matrix()
        eig = np.linalg.eigvalsh(tensor)
        assert np.all(eig > 0) and eig[0]+eig[1] >= eig[2]-1e-10
        assert link.inertial.mass > 0
    for mesh in ET.parse(path).findall(".//mesh"):
        relative = mesh.attrib["filename"].split("package://ax12_compact_description/")[1]
        assert (b.PKG / relative).exists()
    samples = [("zero", {}), ("gripper_closed", {"gripper": 0.70}),
               ("working_pose", {"shoulder_pitch": 0.3, "elbow_pitch": -0.6, "wrist_pitch": 0.3, "gripper": 0.35})]
    for name, _, _, _, _, lo, hi, _ in b.JOINTS:
        samples += [(name+"_min", {name: lo}), (name+"_max", {name: hi})]
    # Include combinations, because single-axis endpoint checks miss collisions.
    for i, (sh, el, wr) in enumerate(itertools.product((-.65, 0, .65), (-.85, 0, .85), (-.7, 0, .7))):
        samples.append((f"combined_{i:02d}", {"shoulder_pitch": sh, "elbow_pitch": el, "wrist_pitch": wr, "wrist_roll": (-1, 0, 1)[i%3], "gripper": (0, .35, .7)[i%3]}))
    for i, phase in enumerate(np.linspace(0, 2*math.pi, 25)[:-1]):
        v = math.sin(phase)
        samples.append((f"demo_{i:02d}", {"base_yaw": .5*v, "shoulder_pitch": .3*v, "elbow_pitch": -.6*v, "wrist_pitch": .3*v, "wrist_roll": .6*v, "gripper": .35*(1-math.cos(phase))}))
    results = []
    for label, pose in samples:
        errors = collisions(pose)
        print(label, "collisions", errors, flush=True)
        results.append({"pose": label, "angles_rad": pose, "overlaps": errors,
                        "gravity_torque_empty_Nm": static_torques(pose),
                        "gravity_torque_10g_Nm": static_torques(pose, b.P["initial_test_object_mass_kg"])})
    # Torque sweep is not collision certification; it quantifies load at combinations.
    peaks = {j[0]: 0.0 for j in b.JOINTS}
    for sh, el, wr in itertools.product(np.linspace(-.65, .65, 9), np.linspace(-.85, .85, 9), np.linspace(-.7, .7, 7)):
        values = static_torques({"shoulder_pitch": sh, "elbow_pitch": el, "wrist_pitch": wr}, .01)
        for key, value in values.items():
            peaks[key] = max(peaks[key], abs(value))
    summary = {"urdf_parsed": True, "links": 8, "movable_joints": 6, "fixed_joints": 1, "positive_inertias": True,
               "CAD_collision_samples": results, "all_sampled_poses_clear": not any(r["overlaps"] for r in results),
               "static_torque_sweep_10g_max_abs_Nm": peaks,
               "limits": "Servo envelope approximations; mesh/hardware fit and full swept collision space not certified. Solid PLA mass; uniform motor inertia; no cables/fasteners/friction/dynamics."}
    (b.OUT / "validation.json").write_text(json.dumps(summary, indent=2))
    print("Gravity peaks", peaks)
    assert summary["all_sampled_poses_clear"], "CAD overlaps found; inspect output/validation.json"


if __name__ == "__main__":
    main()
