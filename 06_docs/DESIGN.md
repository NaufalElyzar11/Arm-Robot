# Dokumen Rancangan — Robot Arm AX-12A + Gripper Servo 25 kg

Versi 0.2 · 23 November 2026 · Status: desain mekanik & software dasar selesai, **belum dicetak/dirakit**

Dokumen ini adalah sumber utama "apa yang dibangun dan kenapa". Detail teknis per bagian ada di README
masing-masing folder.

---

## 1. Tujuan

| Tujuan | Ukuran keberhasilan |
|---|---|
| Showcase di pameran | Robot bisa berjalan ≥ 30 menit tanpa intervensi dalam mode demo, aman disentuh pengunjung |
| Konten (video/foto) | Tiap fase menghasilkan minimal 1 video pendek yang bisa dipublikasikan |
| Portofolio robotics engineer | Repo rapi + dokumen ini + demo digital twin yang bisa direproduksi orang lain |

Fokus pertama: **digital twin** — robot asli dan model 3D di laptop bergerak sinkron dua arah (lihat §7).

## 2. Ringkasan sistem

| Aspek | Nilai |
|---|---|
| Konfigurasi | 5-DOF (yaw, bahu, siku, wrist pitch, wrist roll) + gripper paralel |
| Aktuator lengan | 5× DYNAMIXEL AX-12A (ID 1–5), bus TTL 1 Mbps, Protocol 1.0 |
| Aktuator gripper | 1× servo standar 25 kg DS3225-class, PWM, tanpa feedback |
| Rangka | PLA cetak 3D, gabungan Thingiverse 166430 + base hybrid WidowX MK-II + gripper DS3225 baru |
| Tinggi sumbu bahu | 129 mm dari meja |
| Jarak bahu → siku → wrist pitch | 92.1 mm + 92.1 mm |
| Wrist pitch → muka horn wrist roll | 65.7 mm |
| Muka horn wrist roll → bawah plat gripper | 50.5 mm |
| Jangkauan teoretis (bahu → titik jepit, lurus) | ±335 mm |
| Massa di depan bahu (perkiraan) | ±340 g, gripper lengkap ±117 g |
| Controller | Arduino Mega 2560 + DYNAMIXEL Shield (komunikasi saja) |
| Daya | LiPo 3S 3300 mAh → bus AX 11.1 V langsung + buck 6 V untuk servo gripper |
| Otak | Laptop, WSL Ubuntu 24.04 + ROS 2 Jazzy |

```
Laptop (ROS 2) ──USB──> USB-TTL ──Serial1──> Arduino Mega ──Serial0 + shield──> AX-12A ID1..ID5
                                                   └── D22 (PWM) ──> servo gripper 25 kg (daya buck 6 V)
```

## 3. Keputusan desain

| # | Keputusan | Alasan | Konsekuensi / risiko |
|---|---|---|---|
| D1 | Rangka gabungan Thingiverse 166430 + base WidowX hybrid | Tidak ada desain tunggal yang pas; part 166430 memang untuk AX-12A | Sebagian part berupa mesh (bukan CAD parametrik) |
| D2 | **Hanya 5 AX-12A; gripper pakai servo 25 kg** | Jumlah AX-12A yang tersedia 5 | Lihat §4. Gripper tanpa feedback, butuh rail 6 V, perlu part 09/10/11b baru |
| D3 | Gripper: pertahankan mekanisme crawer asli (tuas + jari tidak berubah) | Mekanisme sudah terbukti; adapter 11b menjaga pin tuas di R8 seperti horn AX-12A | Gripper ±1 cm lebih panjang |
| D4 | Arduino Mega sebagai jembatan, laptop sebagai otak | Mega deterministik untuk bus servo; berat komputasi di laptop | Butuh adapter USB-TTL (USB Mega terpakai bus DYNAMIXEL) |
| D5 | Protokol serial teks sederhana | Mudah di-debug saat awal | Bisa diganti biner / `ros2_control` bila perlu lebih cepat |
| D6 | ROS 2 Jazzy di WSL, source tetap di F:\ | Satu sumber kebenaran, bisa diedit dari Windows | Port USB perlu `usbipd` |
| D7 | Shoulder tetap AX-12A (tanpa upgrade servo) | Hardware yang ada | **Batas torsi bahu** — lihat §5 |

## 4. Servo 25 kg untuk gripper — kelayakan

**Kesimpulan: layak**, dengan syarat di bawah.

| Aspek | Penilaian |
|---|---|
| Ukuran & berat | DS3225 40×20×40.5 mm, 60–67 g — hampir sama dengan AX-12A (54.6 g) |
| Tegangan | 4.8–6.8 V → **tidak boleh** di bus 11–12.6 V. Pakai buck 6 V ≥ 5 A (stall ±2.3–2.9 A) |
| Kontrol | PWM 500–2500 µs dari Mega D22 (library `Servo`). Tidak ada ID, tidak ada telemetri |
| Feedback | Tidak ada. Twin menampilkan *perintah* gripper, bukan posisi terukur |
| Gaya | 25 kg·cm pada crank R8 mm secara teori bisa mendorong ratusan newton ke tuas PLA → **wajib dibatasi** di firmware (`GRIP_US_MIN/MAX`), jangan diperintah menekan terus |
| Mekanik | Part baru: `09_gripper_cradle_ds3225`, `10_gripper_base_ds3225`, `11b_horn_adapter_25t` + horn aluminium bulat 25T Ø20 (beli terpisah) |
| Dampak lengan | Gripper +20–25 g dan ±1 cm lebih jauh → torsi bahu naik ±8% dibanding versi AX-12A |

Dimensi servo yang dipakai adalah dimensi umum DS3225; **ukur unit Anda** sebelum mencetak
(tabel parameter di `01_design/README.md`).

## 5. Analisis beban statis (perkiraan)

Lengan lurus horizontal, PLA infill efektif 60%, massa servo dari datasheet, termasuk ±15 g baut/kabel.
Perkiraan kasar untuk menentukan arah, bukan jaminan kinerja.

| Sendi | Torsi gravitasi tanpa beban | Pedoman ROBOTIS (≤ 1/5 stall = 0.3 N·m) |
|---|---|---|
| Bahu (ID2) | **±0.69 N·m** | ❌ 2.3× di atas pedoman (46% stall) |
| Siku (ID3) | ±0.39 N·m | ⚠️ di atas pedoman |
| Wrist pitch (ID4) | ±0.16 N·m | ✅ |

Arti praktis:

- Jangan menahan lengan lurus horizontal lama-lama; servo bahu akan panas/overload. Ini sifat AX-12A di bahu
  (WidowX asli memakai MX-64 di bahu), bukan akibat servo 25 kg.
- **Area kerja aman**: siku ditekuk, target dalam radius horizontal ±150–200 mm dari base, ketinggian
  meja. Pose "home" dan pose idle demo dibuat dekat vertikal.
- Benda yang dijepit: ringan (kubus cetak 3D, tutup botol, ±10–30 g) dan dekat base.
- Perbaikan murah bila perlu: **pegas/karet penyeimbang** di bahu (dari base ke upper arm), atau mengganti
  servo bahu dengan yang lebih kuat di masa depan.
- Validasi di hardware: pantau suhu ID2/ID3 di `/diagnostics` selama demo 30 menit.

## 6. Arsitektur software

| Lapisan | Komponen | Lokasi |
|---|---|---|
| Firmware | `ax12_bridge` v0.2: baca/tulis 5 AX-12A, PWM gripper ber-slew, telemetri tegangan & suhu, proteksi LiPo | `03_firmware/` |
| Protokol | Teks ASCII 115200 baud (`P`, `G`, `T`, `X`, `J`, `H`, …) | `03_firmware/PROTOCOL.md` |
| Driver ROS 2 | `ax12_driver`: konversi raw/µs ↔ rad, `/joint_states`, `~/command`, `~/set_torque`, `~/estop`, `/diagnostics`, mode `fake_hardware` | `04_ros2_ws/src/ax12_arm_driver` |
| Model | URDF/xacro dengan panjang dari CAD, gripper prismatic mimic | `04_ros2_ws/src/ax12_arm_description` |
| Bringup | `arm.launch.py` (real/fake), `demo.launch.py` (loop pose) | `04_ros2_ws/src/ax12_arm_bringup` |
| Aplikasi | Digital twin (fase berikut), lalu vision/teleop | `05_apps/` |

Keamanan software:

- Torque mati saat boot; saat dinyalakan, goal AX = posisi sekarang (tidak melompat).
- Batas sudut per sendi di firmware (`LIMIT_MIN/MAX`) dan batas pulsa gripper (`GRIP_US_MIN/MAX`).
- Torque dimatikan otomatis bila tegangan bus < 10.5 V tiga kali berturut-turut.
- Node berhenti ≠ torque mati (supaya lengan tidak jatuh); `~/estop` mematikan semua torque.

## 7. Rencana: Digital Twin (fokus berikutnya)

Definisi "selesai": robot asli dan model 3D bergerak sinkron **dua arah**, didokumentasikan dalam video
split-screen.

| Fase | Isi | Kriteria selesai | Output konten |
|---|---|---|---|
| **DT-0 Model** | URDF dari CAD (sudah), lalu mesh per link dari STEP | Model di RViz menyerupai robot asli; ukuran link diverifikasi dengan penggaris setelah rakit | Screenshot model |
| **DT-1 Real → Twin** | Driver real + `robot_state_publisher` + RViz. Torque off, gerakkan lengan dengan tangan | Selisih sudut real vs twin < 2° di semua sendi AX; latensi visual < 100 ms | Video "gerakkan tangan, twin mengikuti" |
| **DT-2 Twin → Real** | Slider / interactive marker di RViz → `~/command` → robot | Robot mencapai target dalam batas aman tanpa hentakan | Video kontrol dari laptop |
| **DT-3 Teach & replay** | Torque off → rekam `/joint_states` (rosbag) → putar ulang dengan torque on | Replay mengikuti rekaman dengan galat < 3° | Video "ajari lalu ulangi" — sangat cocok untuk pameran |
| **DT-4 Simulasi fisika** | Gazebo (pasangan resmi Jazzy: Harmonic) + `ros2_control`, launch argumen `sim:=true` | Satu launch file menjalankan sim atau real; plot galat sim vs real | Video side-by-side sim vs real |
| **DT-5 Dashboard pameran** | Foxglove/rqt: model 3D, tegangan, suhu, status torque; tombol demo | Operator bisa menjalankan & menghentikan demo tanpa terminal | Foto booth pameran |

Catatan gripper: karena servo 25 kg tanpa feedback, twin menampilkan sudut *perintah* gripper. Bila nanti
butuh status "benda terjepit", tambahkan sensor arus (INA219) di jalur 6 V.

Urutan setelah DT: teleop tangan (MediaPipe) → vision pick & place → game tic-tac-toe (lihat `05_apps/README.md`).

## 8. Roadmap keseluruhan

- [ ] **Fase 0 — Persiapan hardware**: ukur servo 25 kg & horn, cetak uji `09/10/11b`, PCB daya + buck 6 V.
- [ ] **Fase 1 — Rakit & uji per servo**: ID 1–5, uji gerak kecil, kalibrasi batas & nol (`06_docs/calibration.md`).
- [ ] **Fase 2 — Digital twin DT-0 … DT-3** (target utama).
- [ ] **Fase 3 — Simulasi & dashboard DT-4, DT-5.**
- [ ] **Fase 4 — Persepsi**: kamera, kalibrasi hand-eye, pick & place.
- [ ] **Fase 5 — Showcase**: mode demo 30 menit, video, write-up portofolio.

## 9. Risiko & mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Torsi bahu AX-12A kurang (§5) | Servo panas, lengan turun | Area kerja dekat, pose idle vertikal, pegas penyeimbang, pantau suhu |
| Dimensi servo 25 kg berbeda dari asumsi | Part gripper tidak pas | Ukur dulu, parameter di `build_gripper_ds3225.py`, shim ring M3 |
| Servo 25 kg mematahkan tuas PLA | Gripper rusak | Batas pulsa firmware, slew rate, bantalan karet, cetak 4 perimeter |
| LiPo 3S penuh (12.6 V) > 12 V AX-12A | Umur servo | Jangan isi penuh untuk demo / buck 12 V |
| LiPo terkuras di pameran | Sel rusak | Alarm LiPo + cut-off firmware 10.5 V, baterai cadangan |
| Kabel USB-serial lepas saat demo | Robot diam / menahan pose | Driver auto-reconnect; tambahkan watchdog firmware (rencana) |
| Pengunjung menyentuh robot | Cedera ringan / kerusakan | Kecepatan rendah di mode demo, tombol/saklar darurat terjangkau |

## 10. Referensi di repo

- Mekanik & perakitan: `01_design/README.md`, `01_design/stl/README.md`
- Elektrik & daya: `02_hardware/README.md`, `02_hardware/bom.csv`
- Firmware & protokol: `03_firmware/README.md`, `03_firmware/PROTOCOL.md`
- ROS 2: `04_ros2_ws/README.md`
- Kalibrasi: `06_docs/calibration.md`

## Riwayat versi

| Versi | Tanggal | Perubahan |
|---|---|---|
| 0.1 | 2026-11-23 | Repo dirapikan, scaffold firmware & ROS 2 (6× AX-12A) |
| 0.2 | 2026-11-23 | Gripper diganti servo 25 kg DS3225 (part 09/10/11b baru), firmware v0.2, URDF dari CAD, dokumen rancangan |
