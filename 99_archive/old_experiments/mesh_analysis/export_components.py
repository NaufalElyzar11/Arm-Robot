"""Lossless shell extraction and inspection previews; no guessed robot joints."""
import json
import struct

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from inspect_stl import SOURCE, OUT, DTYPE


def draw(ax, triangles, colors, bounds, elevation=22, azimuth=15):
    normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-20)
    light = np.array([0.3, -0.5, 0.8])
    brightness = 0.42 + 0.58 * np.abs(normals @ light)
    colors = np.asarray(colors)[:, :3] * brightness[:, None]
    ax.add_collection3d(Poly3DCollection(triangles, facecolors=colors, edgecolors="none", rasterized=True))
    center = bounds.mean(axis=0)
    span = max(np.ptp(bounds, axis=0)) * 0.55
    ax.set(xlim=(center[0]-span, center[0]+span), ylim=(center[1]-span, center[1]+span), zlim=(center[2]-span, center[2]+span))
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_axis_off()


def main():
    data = np.fromfile(SOURCE, dtype=DTYPE, offset=84)
    ids = np.load(OUT / "face_component_ids.npy")
    assert len(data) == len(ids)
    dest = OUT / "separated_stl"
    dest.mkdir(exist_ok=True)
    object_count = int(ids.max())
    triangle_count = 0
    with (OUT / "robot_separated.obj").open("w", encoding="ascii", newline="\n") as obj:
        obj.write("# Disconnected shells; original assembly coordinates; STL units unspecified.\n")
        vertex_offset = 1
        for component_id in range(1, object_count + 1):
            part = data[ids == component_id]
            path = dest / f"component_{component_id:03d}.stl"
            with path.open("wb") as f:
                f.write(f"Extracted component {component_id:03d}; original coordinates".encode("ascii").ljust(80, b" "))
                f.write(struct.pack("<I", len(part)))
                part.tofile(f)
            restored = np.fromfile(path, dtype=DTYPE, offset=84)
            assert restored.tobytes() == part.tobytes()
            triangle_count += len(restored)
            vertices, inverse = np.unique(part["vertices"].reshape(-1, 3), axis=0, return_inverse=True)
            obj.write(f"o component_{component_id:03d}\n")
            np.savetxt(obj, vertices, fmt="v %.9g %.9g %.9g")
            np.savetxt(obj, inverse.reshape(-1, 3) + vertex_offset, fmt="f %d %d %d")
            vertex_offset += len(vertices)
    assert triangle_count == len(data)
    with (OUT / "robot_separated.obj").open() as f:
        obj_lines = {"o": 0, "v": 0, "f": 0}
        for line in f:
            key = line.split(" ", 1)[0]
            if key in obj_lines:
                obj_lines[key] += 1
    assert obj_lines["o"] == object_count and obj_lines["f"] == len(data)
    print(f"Verified {object_count} STL files: all {triangle_count} original triangles preserved exactly.", flush=True)
    print(f"OBJ verified: {obj_lines}", flush=True)
    triangles = data["vertices"].astype(np.float64)
    palette = plt.get_cmap("tab20")
    colors = palette((ids - 1) % 20)
    bounds = np.array([triangles.min(axis=(0, 1)), triangles.max(axis=(0, 1))])
    fig = plt.figure(figsize=(12, 8), facecolor="#f6f8fb")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#f6f8fb")
    draw(ax, triangles, colors, bounds)
    fig.suptitle("MX-28 Arm mk2 | 82 disconnected mesh groups", fontsize=18, y=0.95)
    fig.text(0.5, 0.06, "Original geometry and assembly positions preserved. Colors repeat; groups are not yet robot links.", ha="center", fontsize=10)
    fig.savefig(OUT / "assembly_preview.png", dpi=140)
    plt.close(fig)
    for start in range(1, object_count + 1, 28):
        end = min(start + 27, object_count)
        fig = plt.figure(figsize=(16, 16), facecolor="white")
        fig.suptitle(f"Extracted mesh groups {start:03d}-{end:03d} | each tile scaled independently", fontsize=18, y=0.99)
        for slot, component_id in enumerate(range(start, end + 1), 1):
            local = triangles[ids == component_id]
            local_bounds = np.array([local.min(axis=(0, 1)), local.max(axis=(0, 1))])
            ax = fig.add_subplot(7, 4, slot, projection="3d")
            draw(ax, local, np.tile(palette((component_id-1) % 20), (len(local), 1)), local_bounds)
            ax.set_title(f"{component_id:03d} | {len(local):,} triangles", fontsize=10, pad=-8)
        fig.subplots_adjust(left=0.01, right=0.99, top=0.96, bottom=0.01, wspace=0, hspace=0.03)
        fig.savefig(OUT / f"components_{start:03d}_{end:03d}.png", dpi=120)
        plt.close(fig)
        print(f"Rendered contact sheet {start:03d}-{end:03d}", flush=True)
    (OUT / "export_validation.json").write_text(json.dumps({"stl_files": object_count, "source_triangles": len(data), "exported_triangles": triangle_count, "binary_triangle_records_preserved_exactly": True, "obj_counts": obj_lines}, indent=2))


if __name__ == "__main__":
    main()
