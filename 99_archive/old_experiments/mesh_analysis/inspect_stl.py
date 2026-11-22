"""Inspect disconnected STL shells without changing or repairing source geometry."""
from pathlib import Path
import csv
import json
import struct

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "MX-28_Arm-mk2.stl"
OUT = Path(__file__).resolve().parent
DTYPE = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])


def main():
    with SOURCE.open("rb") as f:
        header = f.read(80)
        count = struct.unpack("<I", f.read(4))[0]
        data = np.fromfile(f, dtype=DTYPE, count=count)
    assert SOURCE.stat().st_size == 84 + 50 * count
    xyz = data["vertices"].astype(np.float64)
    assert np.isfinite(xyz).all()
    vertices, inverse = np.unique(xyz.reshape(-1, 3), axis=0, return_inverse=True)
    faces = inverse.reshape(-1, 3)
    edges = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    graph = coo_matrix((np.ones(len(edges), dtype=np.uint8), (edges[:, 0], edges[:, 1])), shape=(len(vertices), len(vertices))).tocsr()
    n_components, labels = connected_components(graph, directed=False)
    face_labels = labels[faces[:, 0]]
    assert (labels[faces] == face_labels[:, None]).all()
    sizes = np.bincount(face_labels, minlength=n_components)
    order = np.argsort(-sizes, kind="stable")
    rank = np.empty(n_components, dtype=int)
    rank[order] = np.arange(1, n_components + 1)
    face_ids = rank[face_labels]
    rows = []
    for component_id in range(1, n_components + 1):
        mask = face_ids == component_id
        local_faces = faces[mask]
        points = xyz[mask]
        bounds = np.array([points.min(axis=(0, 1)), points.max(axis=(0, 1))])
        local_edges = np.sort(np.concatenate([local_faces[:, [0, 1]], local_faces[:, [1, 2]], local_faces[:, [2, 0]]]), axis=1)
        _, edge_counts = np.unique(local_edges, axis=0, return_counts=True)
        normal_lengths = np.linalg.norm(np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0]), axis=1)
        row = {"component_id": component_id, "triangles": int(mask.sum()), "edge_closed": bool((edge_counts == 2).all()), "boundary_edges": int((edge_counts == 1).sum()), "nonmanifold_edges": int((edge_counts > 2).sum()), "zero_area_triangles": int((normal_lengths == 0).sum())}
        for i, axis in enumerate("xyz"):
            row[f"min_{axis}"] = float(bounds[0, i])
            row[f"max_{axis}"] = float(bounds[1, i])
            row[f"size_{axis}"] = float(bounds[1, i] - bounds[0, i])
        rows.append(row)
    with (OUT / "components.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    summary = {"source": SOURCE.name, "triangles": count, "unique_vertices": len(vertices), "components_exact_vertex_connectivity": n_components, "bounds": [vertices.min(axis=0).tolist(), vertices.max(axis=0).tolist()], "size": np.ptp(vertices, axis=0).tolist(), "units": "unspecified in STL", "edge_closed_components": sum(r["edge_closed"] for r in rows), "zero_area_triangles": sum(r["zero_area_triangles"] for r in rows), "note": "Disconnected shells are not automatically mechanical parts or articulated links. Edge closure alone does not guarantee printability."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    np.save(OUT / "face_component_ids.npy", face_ids)
    print(json.dumps(summary, indent=2))
    print("Largest components:")
    for row in rows[:30]:
        print(row)


if __name__ == "__main__":
    main()
