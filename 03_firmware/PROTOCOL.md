# Protokol serial laptop ↔ Mega (ax12_bridge v0.2)

Teks ASCII, satu perintah per baris (`\n`), 115200 baud di Serial1. Mudah di-debug dengan serial monitor
mana pun. Urutan nilai: ID1 base yaw, ID2 bahu, ID3 siku, ID4 wrist pitch, ID5 wrist roll, lalu **gripper**.

- AX-12A: posisi **raw** (0..1023, 512 = tengah, 1 unit ≈ 0.29°).
- Gripper servo PWM 25 kg: **pulsa mikrodetik** (default dibatasi 1000..2000). Tidak ada feedback posisi.

Konversi ke radian dilakukan di ROS 2 (`ax12_arm_driver/protocol.py`).

## Laptop → Mega

| Perintah | Arti | Balasan |
|---|---|---|
| `PING` | Cek koneksi | `OK PONG` |
| `S` | Cek keberadaan servo AX | `I 1 1 1 1 1` (1 = merespons) |
| `T 1` / `T 0` | Torque semua on/off. On: goal AX = posisi sekarang (tidak melompat), gripper diberi pulsa terakhir. Off: AX torque off, gripper tanpa pulsa | `OK T 1` |
| `X` | Darurat: torque off semua | `OK X` |
| `P a1 a2 a3 a4 a5 g` | Goal AX raw (di-clamp `LIMIT_MIN/MAX`) + pulsa gripper µs (di-clamp `GRIP_US_MIN/MAX`). Ditolak bila torque off | — / `E TORQUE_OFF` |
| `G g` | Gripper saja (µs) | — / `E TORQUE_OFF` |
| `V v1 … v5` | Moving speed AX (1..1023) | `OK V` |

Perubahan pulsa gripper dibatasi `GRIP_SLEW_US_PER_TICK` per 20 ms supaya tidak menghentak.

## Mega → laptop (otomatis)

| Baris | Frekuensi | Arti |
|---|---|---|
| `J <ms> a1 … a5 g` | 50 Hz | Posisi AX sekarang (raw, `-1` = tidak merespons) + pulsa gripper yang sedang dikirim (`-1` = gripper off) |
| `H <volt_dV> t1 … t5` | 1 Hz | Tegangan bus AX (0.1 V, mis. `118` = 11.8 V) dan suhu tiap AX (°C) |
| `E <kode> …` | saat error | `PARSE`, `UNKNOWN`, `OVERFLOW`, `TORQUE_OFF`, `LOWBATT <dV>` |
| `OK BOOT …` | saat reset | Mega baru menyala |

## Rencana pengembangan

- Sync Write untuk goal AX.
- Watchdog: bila laptop diam > N detik saat demo, kembali ke pose aman.
- Sensor arus gripper (INA219) untuk mendeteksi benda terjepit / stall.
- Kalau butuh lebih cepat: protokol biner + checksum, atau hardware interface `ros2_control`.
