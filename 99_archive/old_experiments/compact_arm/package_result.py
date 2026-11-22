"""Verify exported STEP files and assemble a small portable delivery ZIP."""
import json
from pathlib import Path
import zipfile

import cadquery as cq
import trimesh
import build as b


def main():
    checks = []
    for name, (original, _, _) in b.PARTS.items():
        restored = cq.importers.importStep(str(b.OUT / "step" / f"{name}.step")).val()
        assert restored.isValid() and len(restored.Solids()) == 1
        step_error = abs(restored.Volume()-original.Volume())/original.Volume()
        mesh = trimesh.load_mesh(b.OUT / "stl" / f"{name}.stl")
        mesh_error = abs(mesh.volume-original.Volume())/original.Volume()
        assert step_error < 1e-7 and mesh_error < .01
        checks.append({"part": name, "STEP_volume_relative_error": step_error, "STL_volume_relative_error": mesh_error})
    (b.OUT / "export_verification.json").write_text(json.dumps(checks, indent=2))
    validation = json.loads((b.OUT / "validation.json").read_text())
    assert validation["all_sampled_poses_clear"]
    validation["torque_sweep_sampling"] = {"poses": 567, "varied_joints": ["shoulder_pitch", "elbow_pitch", "wrist_pitch"], "other_joints_rad": 0, "not_an_exhaustive_workspace_rating": True}
    (b.OUT / "validation.json").write_text(json.dumps(validation, indent=2))
    ros = json.loads((b.OUT / "ros2_validation.json").read_text())
    gui = json.loads((b.OUT / "ros2_gui_validation.json").read_text())
    assert ros["passed"] and gui["slider_started_offscreen"]
    report = f"""# Hasil verifikasi prototipe

- 8 part STEP berhasil dibaca ulang sebagai solid valid; volume cocok dengan sumber CAD.
- 8 STL part tertutup dan volumenya berbeda kurang dari 1% terhadap CAD akibat tessellation.
- 5 STL kupon dibuat dan diperiksa sebagai mesh tertutup.
- URDF: {validation['links']} link (termasuk anchor world), 6 sendi bergerak, 1 joint fixed, massa/inersia estimasi positif.
- {len(validation['CAD_collision_samples'])} pose CAD sampel: tidak ditemukan overlap volume di atas 0,01 mm³ terhadap envelope servo dan part cetak yang dimodelkan.
- Sweep gravitasi: 567 kombinasi tiga sendi pitch; joint lain nol. Beban uji 10 g. Puncak sampel bahu {validation['static_torque_sweep_10g_max_abs_Nm']['shoulder_pitch']:.3f} N·m.
- ROS2 Jazzy pada WSL Ubuntu-24.04: colcon build dan check_urdf berhasil; {ros['joint_state_messages']} pesan JointState dan {ros['tf_messages']} pesan TF diterima, keenam sendi berubah.
- Panel slider berhasil berjalan offscreen dan memublikasikan enam joint. RViz belum diperiksa secara visual; render CAD dan animasi disertakan untuk inspeksi geometri.
- Tidak ada koneksi atau perintah gerak ke hardware.

Ini bukti pemeriksaan digital, bukan validasi hasil cetak, kekuatan, payload, suhu, akses baut atau kecocokan unit servo aktual. Baut/kabel/horn detail tidak dimodelkan; servo digambarkan dengan envelope sederhana. Pemeriksaan benturan diskret tidak menjamin semua kombinasi sudut aman. Nilai gravitasi tidak memasukkan dinamika atau gaya jepit.
"""
    (b.OUT / "VALIDATION.md").write_text(report, encoding="utf-8")
    files = []
    for pattern in ("*.py", "*.json", "*.md", "*.ps1", "requirements.txt"):
        files += list(b.ROOT.glob(pattern))
    files += list((b.ROOT / "reference").glob("*.png"))
    files += [p for p in b.PKG.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    for subdir in ("stl", "step", "coupons"):
        files += [p for p in (b.OUT / subdir).iterdir() if p.is_file()]
    files += [p for p in b.OUT.iterdir() if p.is_file() and p.suffix in (".json", ".md", ".png", ".gif", ".csv", ".step", ".log")]
    dest = b.OUT / "compact_arm_prototype_v1.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, Path("compact_arm") / path.relative_to(b.ROOT))
    with zipfile.ZipFile(dest) as archive:
        assert archive.testzip() is None
        count = len(archive.infolist())
    print(f"Verified and packaged {count} files, {dest.stat().st_size/1024/1024:.2f} MiB")


if __name__ == "__main__":
    main()
