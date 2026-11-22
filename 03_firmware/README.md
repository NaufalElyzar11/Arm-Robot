# 03_firmware — Arduino Mega + DYNAMIXEL Shield

| Sketch | Fungsi |
|---|---|
| `tools/ax12_scan/` | Cari semua servo di bus (ID & model) |
| `tools/ax12_set_id/` | Ganti ID satu servo (sambungkan satu servo saja) |
| `ax12_bridge/` | Firmware utama v0.2: 5× AX-12A (bus DYNAMIXEL) + gripper servo PWM 25 kg di D22. Protokol: `PROTOCOL.md` |

## Persiapan Arduino IDE

1. Library Manager → install **DynamixelShield** (otomatis menarik **Dynamixel2Arduino**). Library **Servo** sudah bawaan.
2. Board: **Arduino Mega or Mega 2560**.
3. Lepas jumper VIN di shield (lihat `02_hardware/README.md`).

## Alur upload

1. UART switch shield → **Upload**, colok USB Mega, upload.
2. UART switch → **DYNAMIXEL**.
3. Buka serial monitor di port **adapter USB-TTL** (Serial1), 115200, line ending *Newline*.

## Urutan pertama kali

1. Sambungkan satu servo → `ax12_set_id` dengan `NEW_ID = 1`. Ulangi untuk ID 2..5. Beri label.
2. Sambungkan semua → `ax12_scan`, pastikan ID 1..5 muncul.
3. Upload `ax12_bridge`. Di serial monitor: `S`, lalu `T 1`, lalu gerakan kecil mis.
   `P 512 512 512 512 512 1500` → `P 540 512 512 512 512 1500`. Akhiri dengan `T 0`.
4. Dengan torque off, gerakkan tiap sendi manual ke batas aman, catat nilai dari baris `J`,
   lalu isi `LIMIT_MIN` / `LIMIT_MAX` di `ax12_bridge.ino`.
5. Gripper (**sebelum tuas dipasang**): `T 1`, lalu `G 1500`, `G 1300`, `G 1700` … cari pulsa jari terbuka
   dan jari *hampir* bertemu setelah tuas dipasang. Isi `GRIP_US_MIN/MAX/SAFE` di firmware dan
   `gripper_*` di `04_ros2_ws/src/ax12_arm_bringup/config/arm.yaml` dengan angka yang sama.
