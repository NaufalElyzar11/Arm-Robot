# 02_hardware — Elektrik, wiring, daya

## Komponen utama

| Komponen | Peran |
|---|---|
| 5× DYNAMIXEL AX-12A (ID 1–5) | Base yaw, bahu, siku, wrist pitch, wrist roll (TTL half-duplex, Protocol 1.0, 1 Mbps) |
| 1× servo 25 kg DS3225-class (PWM) | Gripper. 4.8–6.8 V, sinyal pulsa 500–2500 µs, **tanpa feedback posisi** |
| Horn aluminium bulat 25T (Ø20, 4× M3 PCD 14) | Dipasang di servo gripper, lalu adapter `11b` dibaut di atasnya |
| Arduino Mega 2560 | Controller real-time: bus DYNAMIXEL + sinyal PWM gripper, terima perintah dari laptop |
| DYNAMIXEL Shield (ROBOTIS) | Hanya untuk **komunikasi** (buffer half-duplex, pin DIR = D2) |
| Adapter USB-TTL 5V (CP2102/CH340/FTDI) | Link laptop ↔ Mega lewat **Serial1** |
| Buck converter 6.0 V ≥ 5 A | Daya khusus servo gripper dari LiPo 3S |
| LiPo 3S 3300 mAh | Sumber daya utama |
| PCB distribusi daya (custom) | Sekring, saklar, kapasitor, konektor servo, buck 6 V |
| Laptop (WSL Ubuntu 24.04 + ROS 2 Jazzy) | Otak: perencanaan gerak, vision, digital twin |

## ⚠️ Kenapa laptop tidak lewat USB Mega

DYNAMIXEL Shield memakai Serial hardware pin 0/1 — pin yang sama dengan USB Mega. Selama UART switch
shield di posisi **DYNAMIXEL**, USB tidak bisa dipakai untuk komunikasi (hanya untuk upload dengan switch
di posisi **Upload**). Karena Mega punya UART tambahan, link ke laptop dipindah ke **Serial1**:

| Adapter USB-TTL | Arduino Mega |
|---|---|
| TX | RX1 (pin 19) |
| RX | TX1 (pin 18) |
| GND | GND |
| 5V/VCC | **jangan disambung** (Mega diberi daya dari USB-nya sendiri) |

Alur kerja: switch **Upload** → upload sketch lewat USB Mega → switch **DYNAMIXEL** → komunikasi lewat adapter.

## Servo gripper 25 kg (DS3225-class)

| Kabel servo | Sambung ke |
|---|---|
| Oranye/kuning (sinyal) | Mega **D22** (header digital panjang, tidak tertutup shield) |
| Merah (+) | Output **buck 6.0 V** di PCB daya |
| Cokelat/hitam (−) | GND PCB daya (**harus** satu ground dengan Mega) |

- **Jangan** sambungkan servo ini ke bus 11–12.6 V AX-12A, dan jangan ambil daya dari pin 5V Arduino.
  Rentang tegangan DS3225 4.8–6.8 V, arus stall ±2.3–2.9 A → buck 6 V minimal 5 A memberi ruang aman.
- Tidak ada feedback: firmware hanya tahu pulsa yang dikirim. Saat torque dinyalakan, servo langsung
  menuju pulsa terakhir (default `GRIP_US_SAFE`), jadi jangan ada jari/benda di jalur gripper saat itu.
- Tenaga 25 kg·cm jauh melebihi kebutuhan menjepit benda ringan dan bisa mematahkan tuas PLA.
  Batasi `GRIP_US_MIN/MAX` di firmware hanya sampai jari **hampir** bertemu; jangan perintahkan menekan terus
  (servo stall = panas + arus tinggi). Pertimbangkan bantalan karet di ujung jari.

## Daya

- AX-12A: input 9–12 V (rekomendasi 11.1 V), arus stall 1.5 A per servo.
- LiPo 3S: 11.1 V nominal, **12.6 V saat penuh** → sedikit di atas batas atas 12 V AX-12A.
  Pertimbangkan tidak mengisi penuh untuk sesi pameran (~4.1 V/sel), atau buck 11–12 V ≥ 10 A untuk bus AX.
- Batas bawah: hentikan di ~3.5 V/sel (10.5 V). Firmware mematikan torque bila tegangan bus < 10.5 V, tapi
  **tetap pasang alarm LiPo / low-voltage cutoff hardware**.
- Worst case: 5 AX stall ≈ 7.5 A + gripper ≈ 3 A (di sisi 6 V, ±1.7 A di sisi baterai). Sekring utama
  ±10 A slow-blow, kabel utama min. 18 AWG.

### ⚠️ Jumper VIN pada DYNAMIXEL Shield

Jumper VIN shield menyambungkan daya DYNAMIXEL dengan jack DC Arduino. Karena daya servo datang dari PCB
terpisah, **lepas jumper VIN**. Kabel dari shield ke bus servo cukup membawa **DATA + GND**. Ground shield,
Mega, PCB daya, buck 6 V, dan semua servo **harus bersatu** (common ground).

## Topologi

```
LiPo 3S ─ XT60 ─ saklar ─ sekring 10A ─┬─ bus 11.1V ─┬─ ID1 ─ ID2 ─ ID3 ─ ID4 ─ ID5   (kabel 3-pin AX)
                                       │             │
                                       │   Shield DXL port (DATA + GND saja)
                                       │
                                       └─ buck 6.0V ── servo gripper (+/−) ;  sinyal ← Mega D22
Mega ─ Serial1 ─ USB-TTL ─ laptop                       GND semua disatukan
```

## Konfigurasi servo

| ID / pin | Sendi | Catatan |
|---|---|---|
| AX ID 1 | Base yaw | |
| AX ID 2 | Bahu | Paling berat bebannya — pantau suhu |
| AX ID 3 | Siku | |
| AX ID 4 | Wrist pitch | |
| AX ID 5 | Wrist roll | Horn-nya memikul cradle + servo gripper (±90 g) |
| D22 (PWM) | Gripper DS3225 | 1000–2000 µs default, kalibrasi buka/tutup |

Semua AX-12A keluar pabrik dengan ID 1 → set ID **satu per satu** (hanya satu servo tersambung)
memakai `03_firmware/tools/ax12_set_id`.

## Checklist sebelum menyalakan torque pertama kali

- [ ] Polaritas konektor baterai & PCB benar; output buck terukur 6.0 V **sebelum** servo gripper dicolok.
- [ ] Jumper VIN shield dilepas, common ground tersambung (termasuk GND buck).
- [ ] ID 1–5 unik, terverifikasi dengan `ax12_scan`.
- [ ] Servo diuji **tanpa terpasang di rangka** dulu: gerak kecil di sekitar 512 / 1500 µs.
- [ ] Horn gripper dipasang setelah servo dipusatkan, rentang `GRIP_US_*` dicoba tanpa tuas dulu.
- [ ] Batas sudut aman tiap sendi diisi di firmware setelah dicek manual dengan torque off.
- [ ] Ada cara mematikan darurat (saklar daya mudah dijangkau).
