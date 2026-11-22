# Build log

## 2026-11-23
- Repositori dirapikan: desain final di `01_design/`, referensi di `99_archive/`.
- Scaffold firmware (`03_firmware`) dan workspace ROS 2 (`04_ros2_ws`) dibuat.
- Hanya 5 AX-12A tersedia → gripper diganti servo 25 kg DS3225: part baru `09_gripper_cradle_ds3225`,
  `10_gripper_base_ds3225`, `11b_horn_adapter_25t`; firmware v0.2 (PWM di D22); URDF memakai dimensi CAD.
- Bug `tidy_repo.ps1` v1 merusak `build_hybrid_base.py` & `render_preview.py` (huruf A → X); sudah dipulihkan
  dari salinan asli dan script diperbaiki.
- Dokumen rancangan `06_docs/DESIGN.md` dibuat. Fokus berikutnya: digital twin.
