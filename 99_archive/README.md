# 99_archive — Referensi & eksperimen lama (tidak dipakai)

| Folder | Isi | Kenapa disimpan |
|---|---|---|
| `reference_designs/widowx_mkii_robotic_arm/` | Desain WidowX MK-II | Referensi base & proporsi |
| `reference_designs/mx28_arm_mk2/`, `mx28_arm_mk2_stl/` | Model OBJ/STL lengan MX-28 (±270 MB OBJ) | Referensi visual |
| `reference_designs/pxpincher_ros_kinetic/` | Paket ROS1 PhantomX Pincher | Contoh driver/IK lengan AX-12 |
| `reference_designs/widowx_arm_description_ros1/` | URDF/xacro WidowX (ROS1) | Contoh struktur URDF & gripper |
| `old_experiments/compact_arm/` | Desain "compact arm" (5× AX-12A + MG90S) + paket ROS2 lama | Tidak dilanjutkan |
| `old_experiments/mesh_analysis/` | Pemisahan mesh MX-28 menjadi 82 komponen | Tidak dilanjutkan |
| `old_experiments/BUILD_CONSTRAINTS_lama.md` | Catatan kebutuhan awal (asumsi gripper MG90S, sudah usang) | Riwayat keputusan |
| `old_gripper_ax12a/` | `09_wrist_rotate`, `10_the_crawer_base` (STL+STEP) untuk gripper AX-12A | Diganti gripper servo 25 kg (v0.2) |
| `original_downloads/` | Zip/rar unduhan asli | Cadangan sumber. **`ARM.rar` (±246 MB) belum dicek isinya** |

Desain akhir (v0.2) memakai 5× AX-12A + servo 25 kg DS3225 untuk gripper. Folder `old_gripper_ax12a/`
terisi setelah `tidy_repo.ps1 -Apply` dijalankan ulang.
