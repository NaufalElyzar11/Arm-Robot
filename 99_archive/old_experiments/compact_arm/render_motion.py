"""Animated visualization of the sampled demo trajectory; no physics solver."""
import math
import io
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

import build as b
from validate import transforms
from render_preview import draw


def main():
    assets = [(n, link, (.08, .6, .74)) for n, (_, link, _) in b.PARTS.items()]
    assets += [(f"{link}_servo_envelope", link, (.26, .29, .34)) for link in b.MOTORS]
    meshes = {n: trimesh.load_mesh(b.PKG / "meshes" / f"{n}.stl") for n, _, _ in assets}
    images = []
    for i in range(24):
        phase = 2*math.pi*i/24
        v = math.sin(phase)
        pose = dict(zip([j[0] for j in b.JOINTS], [.5*v, .3*v, -.6*v, .3*v, .6*v, .35*(1-math.cos(phase))]))
        frames, _ = transforms(pose)
        fig = plt.figure(figsize=(5.2, 6.2), facecolor="#f4f6f8")
        ax = fig.add_subplot(111, projection="3d", facecolor="#f4f6f8")
        for name, link, color in assets:
            verts = meshes[name].vertices @ frames[link][:3, :3].T + frames[link][:3, 3]
            draw(ax, verts[meshes[name].faces], color)
        ax.set(xlim=(-105, 105), ylim=(-90, 120), zlim=(0, 365))
        ax.set_box_aspect((210, 210, 365))
        ax.set_axis_off()
        ax.view_init(16, -55)
        fig.suptitle("5 AX-12A + MG90S", fontsize=15, y=.96)
        fig.text(.5, .055, "Kinematic prototype / no hardware commands", ha="center", fontsize=9)
        fig.subplots_adjust(left=0, right=1, top=.92, bottom=.08)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=95)
        plt.close(fig)
        buffer.seek(0)
        images.append(Image.open(buffer).convert("RGB"))
    images[0].save(b.OUT / "motion_preview.gif", save_all=True, append_images=images[1:], duration=180, loop=0, optimize=False)
    print("Motion GIF created.")


if __name__ == "__main__":
    main()
