"""Render actual exported geometry and a kinematic motion preview."""
import json
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import build as b
from validate import transforms


def draw(ax, triangles, color):
    normal = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    light = np.array([0.4, -0.5, 0.77])
    shade = .4+.6*np.abs(normal@light)
    colors = shade[:, None]*np.array(color)[None, :]
    ax.add_collection3d(Poly3DCollection(triangles, facecolors=colors, edgecolors="none", rasterized=True))


def setup(ax, points, elev=18, azim=-55):
    lo, hi = points.min(axis=0), points.max(axis=0)
    mid = (lo+hi)/2
    span = (hi-lo).max()*.56
    ax.set(xlim=(mid[0]-span, mid[0]+span), ylim=(mid[1]-span, mid[1]+span), zlim=(mid[2]-span, mid[2]+span))
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev, azim)
    ax.set_axis_off()


def main():
    assets = [(name, link, (0.08, .6, .74)) for name, (_, link, _) in b.PARTS.items()]
    assets += [(f"{link}_servo_envelope", link, (.26, .29, .34)) for link in b.MOTORS]
    meshes = {name: trimesh.load_mesh(b.PKG / "meshes" / f"{name}.stl") for name, _, _ in assets}
    fig = plt.figure(figsize=(14, 9), facecolor="#f4f6f8")
    for idx, (label, pose) in enumerate([
        ("ZERO POSE", {}),
        ("ARTICULATED POSE", {"base_yaw": -.2, "shoulder_pitch": .45, "elbow_pitch": -.75, "wrist_pitch": .5, "wrist_roll": -.25, "gripper": .4}),
    ], 1):
        ax = fig.add_subplot(1, 2, idx, projection="3d", facecolor="#f4f6f8")
        frames, _ = transforms(pose)
        points = []
        for name, link, color in assets:
            vertices = meshes[name].vertices @ frames[link][:3, :3].T + frames[link][:3, 3]
            draw(ax, vertices[meshes[name].faces], color)
            points.append(vertices)
        setup(ax, np.vstack(points), 16, -55)
        ax.set_title(label, fontsize=12, pad=-5)
    fig.suptitle("AX-12A compact arm | 5 arm joints + MG90S gripper", fontsize=19, y=.95)
    fig.text(.5, .08, "Teal: printable prototype parts   /   Grey: approximate purchased servo envelopes", ha="center", fontsize=11)
    fig.text(.5, .045, "Fit-test prototype. Hardware holes, clearances and strength still require physical verification.", ha="center", fontsize=10, color="#5c6570")
    fig.subplots_adjust(left=.01, right=.99, bottom=.12, top=.88, wspace=0)
    fig.savefig(b.OUT / "assembly_preview.png", dpi=150)
    plt.close(fig)
    fig = plt.figure(figsize=(15, 10), facecolor="white")
    for idx, (name, (shape, _, _)) in enumerate(b.PARTS.items(), 1):
        ax = fig.add_subplot(2, 4, idx, projection="3d")
        mesh = trimesh.load_mesh(b.OUT / "stl" / f"{name}.stl")
        draw(ax, mesh.triangles, (0.08, .6, .74))
        setup(ax, mesh.vertices, 24, -55)
        ax.set_title(name.replace("_", " "), fontsize=10)
    fig.suptitle("8 printable parts | tile scales differ", fontsize=18)
    fig.subplots_adjust(left=.01, right=.99, bottom=.01, top=.91, wspace=.05, hspace=.1)
    fig.savefig(b.OUT / "parts_preview.png", dpi=150)
    plt.close(fig)
    print("Rendered assembly and parts previews.")


if __name__ == "__main__":
    main()
