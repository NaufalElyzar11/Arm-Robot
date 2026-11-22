# STL — Part Siap Cetak (Lengan 5× AX-12A + Gripper Servo 25 kg DS3225)

Semua file diletakkan di bed (`Z = 0`) dalam **orientasi cetak**. Semua watertight kecuali `06_f4_n_f3_arm_link` (mesh asli; slicer biasanya bisa memperbaikinya otomatis — cek dulu).
Jumlah cetak untuk 1 robot ada di akhir nama file (`_x1`, `_x2`, `_x3`).

## File preview

- `00_FULL_ROBOT_ARM_PREVIEW.stl` — rakitan utuh termasuk 5 servo AX-12A + servo DS3225 (untuk viewer/slicer).
- `00_FULL_ROBOT_ARM_PRINTED_PARTS_PREVIEW.stl` — semua part cetak dalam posisi terakit.
- `PREVIEW_FULL_ROBOT_ARM.png`, `KATALOG_SEMUA_PART_STL.png` — render.

## Part

| Kode | File | Jumlah | Ukuran (mm) | Keterangan |
|---|---|---|---|---|
| 01 | `01_base_legs_widowx_hybrid_x1.stl` | **1x** | 190.0 x 190.0 x 80.0 | Base Bawah Oktagonal Lebar WidowX (190x190x80 mm) |
| 02 | `02_base_turn_table_bot_widowx_x1.stl` | **1x** | 112.0 x 112.0 x 7.0 | Deck Atas Turntable Model Oktagonal WidowX (112x112x7 mm) |
| 02b | `02b_base_turn_table_bot_original_x1_opsional.stl` | Opsional (1x) | 60.0 x 78.25 x 7.0 | Deck Atas Turntable Kotak Asli (60x78.25x7 mm - Cadangan) |
| 03 | `03_base_widowx_outer_pillars_x1set.stl` | **1 set (4 tiang)** | 98.0 x 46.0 x 75.0 | 4 Tiang Luar Oktagonal WidowX (Tinggi 75 mm) |
| 04 | `04_base_turn_table_spacer_x1.stl` | **1x** | 22.0 x 21.78 x 2.5 | Spacer Horn Servo Base (Ø22x2.5 mm) |
| 05 | `05_base_turn_table_x1.stl` | **1x** | 56.0 x 55.59 x 20.7 | Meja Putar Base + Dudukan Servo Bahu (Ø56x20.7 mm) |
| 06 | `06_f4_n_f3_arm_link_x2.stl` | **2x** | 48.0 x 91.63 x 28.61 | Lengan Utama Bahu-Siku & Siku-Pergelangan (Cetak 2x) |
| 07 | `07_servo_hinge_flange_x3.stl` | **3x** | 6.5 x 20.0 x 19.94 | Flange Engsel Belakang Servo Bahu/Siku/Wrist (Cetak 3x) |
| 08 | `08_wrist_x1.stl` | **1x** | 48.22 x 54.71 x 42.96 | Bracket Pergelangan Tangan Pitch-ke-Roll (48.2x54.7x43 mm) |
| 09 | `09_gripper_cradle_ds3225_x1.stl` | **1x** | 24.0 x 57.0 x 34.0 | Dudukan Servo 25kg: dibaut ke horn wrist roll, menyangga kuping servo |
| 10 | `10_gripper_base_ds3225_x1.stl` | **1x** | 104.4 x 59.5 x 18.0 | Plat Gripper + kaki ke kuping servo 25kg (modifikasi the_crawer_base) |
| 11 | `11_the_crawer_lever_x2.stl` | **2x** | 33.13 x 10.38 x 5.5 | Tuas Penghubung Horn Gripper (Cetak 2x - Kiri & Kanan, tidak berubah) |
| 11b | `11b_horn_adapter_25t_x1.stl` | **1x** | 24.0 x 24.0 x 3.0 | Adapter horn disc aluminium 25T -> pin tuas R8 (pengganti horn AX-12A) |
| 12 | `12_the_crawer_finger_x2.stl` | **2x** | 62.9 x 31.2 x 40.82 | Jari Penjepit Gripper (Cetak 2x - Kiri & Kanan) |

## Catatan cetak (PLA, nozzle 0.4)

- `09_gripper_cradle_ds3225`: dasar di bed, dinding ke atas. Kantong mur horizontal → bridging pendek, tanpa support.
- `10_gripper_base_ds3225`: sudah dibalik (muka atas plat di bed, kaki ke atas). Tanpa support.
- `11b_horn_adapter_25t`: muka countersink menghadap ke atas. Cetak 100% infill (part kecil, menerima torsi).
- Part gripper menerima torsi servo 25 kg: minimal 4 perimeter, infill ≥ 40%.
- Desain lama gripper AX-12A (`09_wrist_rotate`, `10_the_crawer_base`) dipindah ke `99_archive/old_gripper_ax12a/` oleh `tidy_repo.ps1`.
