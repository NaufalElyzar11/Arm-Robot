# 05_apps — Aplikasi di atas robot

Satu subfolder per aplikasi (paket ROS 2 baru dibuat di `04_ros2_ws/src/`, folder ini untuk notebook,
dataset, model, skrip eksperimen).

Rencana (urut dari yang paling cepat jadi):

| Folder | Ide | Skill yang ditunjukkan |
|---|---|---|
| `digital_twin/` | **Fokus berikutnya.** Robot asli ↔ model 3D sinkron dua arah, teach & replay, sim Gazebo (rencana di `06_docs/DESIGN.md` §7) | ROS 2, URDF, ros2_control, simulasi |
| `hand_teleop/` | Pengunjung menggerakkan lengan dengan tangan di depan webcam (MediaPipe Hands → target TCP → IK) | CV real-time, IK, HRI |
| `vision_pick_place/` | Kamera di atas meja + ArUco, deteksi kubus warna, ambil & sortir ke wadah | Kalibrasi kamera/hand-eye, persepsi, perencanaan gerak |
| `tictactoe/` | Main tic-tac-toe melawan pengunjung: kamera baca papan, robot menaruh bidak | Integrasi penuh: persepsi + AI game + manipulasi |
| `drawing/` | Robot menggambar sketsa wajah/garis dari foto (edge detection → path) | Trajectory, kalibrasi bidang |
| `imitation_learning/` | Rekam demonstrasi via teleop, latih policy (mis. ACT/diffusion) | Robot learning (tahap lanjut) |

Batasan realistis: AX-12A (1.5 N·m stall) + rangka PLA + jangkauan pendek → benda ringan (kubus cetak 3D
kecil, puluhan gram), gerak pelan-sedang, 5-DOF (orientasi ujung terbatas).
