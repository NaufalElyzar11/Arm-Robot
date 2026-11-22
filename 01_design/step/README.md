# STEP — Model CAD (Lengan 5× AX-12A + Gripper Servo 25 kg DS3225)

## Rakitan

- `00_FULL_ROBOT_ARM_ASSEMBLY.step` — rakitan utuh: part cetak + 5× AX-12A + servo DS3225 + horn disc.
- `00_FULL_ROBOT_ARM_PRINTED_PARTS_ONLY.step` — part cetak saja dalam posisi terakit.
- Part kembar disimpan sebagai *instance* (geometri ditulis sekali); koordinat dibulatkan ke 1 nm.
- Board kontroler belum dimasukkan (posisi Arduino Mega + shield belum diputuskan).

## Part satuan

| File | Fungsi |
|---|---|
| `01_base_legs_widowx_hybrid.step` | Base Bawah Oktagonal Lebar WidowX (190x190x80 mm) |
| `02_base_turn_table_bot_widowx.step` | Deck Atas Turntable Model Oktagonal WidowX (112x112x7 mm) |
| `02b_base_turn_table_bot_original.step` | Deck Atas Turntable Kotak Asli (60x78.25x7 mm - Cadangan) |
| `03_base_widowx_outer_pillars.step` | 4 Tiang Luar Oktagonal WidowX (Tinggi 75 mm) |
| `04_base_turn_table_spacer.step` | Spacer Horn Servo Base (Ø22x2.5 mm) |
| `05_base_turn_table.step` | Meja Putar Base + Dudukan Servo Bahu (Ø56x20.7 mm) |
| `06_f4_n_f3_arm_link.step` | Lengan Utama Bahu-Siku & Siku-Pergelangan (Cetak 2x) |
| `07_servo_hinge_flange.step` | Flange Engsel Belakang Servo Bahu/Siku/Wrist (Cetak 3x) |
| `08_wrist.step` | Bracket Pergelangan Tangan Pitch-ke-Roll (48.2x54.7x43 mm) |
| `09_gripper_cradle_ds3225.step` | Dudukan Servo 25kg: dibaut ke horn wrist roll, menyangga kuping servo |
| `10_gripper_base_ds3225.step` | Plat Gripper + kaki ke kuping servo 25kg (modifikasi the_crawer_base) |
| `11_the_crawer_lever.step` | Tuas Penghubung Horn Gripper (Cetak 2x - Kiri & Kanan, tidak berubah) |
| `11b_horn_adapter_25t.step` | Adapter horn disc aluminium 25T -> pin tuas R8 (pengganti horn AX-12A) |
| `12_the_crawer_finger.step` | Jari Penjepit Gripper (Cetak 2x - Kiri & Kanan) |
| `13_dynamixel_ax12a_reference.step` | Referensi AX-12A (dipakai 5x, bukan untuk dicetak) |
| `14_servo_ds3225_reference.step` | Referensi servo 25 kg DS3225 + horn disc 25T (bukan untuk dicetak) |

Part `09`, `10`, `11b`, `14` dibuat langsung sebagai B-Rep oleh `cad_scripts/build_gripper_ds3225.py`
(parametrik, bisa diedit). Part lain berasal dari mesh STL asli sehingga permukaannya berupa banyak segitiga.
