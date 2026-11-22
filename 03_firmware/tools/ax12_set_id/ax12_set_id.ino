/*
 * ax12_set_id.ino — Ganti ID satu AX-12A
 *
 * PENTING: sambungkan HANYA SATU servo ke bus saat menjalankan ini.
 * Ubah NEW_ID, upload, lihat hasil di Serial1 (adapter USB-TTL, 115200).
 * Ulangi untuk servo berikutnya dengan NEW_ID berbeda (1..5). Tempel label ID di tiap servo.
 * (Servo gripper 25 kg adalah servo PWM biasa, tidak punya ID.)
 */
#include <DynamixelShield.h>

#define HOST Serial1
const uint8_t  NEW_ID   = 2;        // <-- ubah per servo
const uint32_t DXL_BAUD = 1000000;

DynamixelShield dxl;

void setup() {
  HOST.begin(115200);
  while (!HOST) {}
  dxl.begin(DXL_BAUD);
  dxl.setPortProtocolVersion(1.0);

  int found_id = -1;
  uint8_t count = 0;
  for (uint16_t id = 0; id < 254; id++) {
    if (dxl.ping(id)) { found_id = id; count++; }
  }

  if (count == 0) { HOST.println(F("Tidak ada servo. Cek kabel, daya, switch DYNAMIXEL.")); return; }
  if (count > 1)  { HOST.println(F("Lebih dari satu servo terdeteksi! Sambungkan satu saja. Dibatalkan.")); return; }

  HOST.print(F("Servo ditemukan dengan ID ")); HOST.println(found_id);
  if (found_id == NEW_ID) { HOST.println(F("ID sudah sesuai, tidak ada perubahan.")); return; }

  dxl.torqueOff(found_id);
  if (dxl.setID(found_id, NEW_ID) && dxl.ping(NEW_ID)) {
    HOST.print(F("Berhasil: ID sekarang ")); HOST.println(NEW_ID);
  } else {
    HOST.println(F("Gagal mengganti ID."));
  }
}

void loop() {}
