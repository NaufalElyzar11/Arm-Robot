/*
 * ax12_scan.ino — Cari semua DYNAMIXEL di bus (Protocol 1.0)
 * Output ke Serial1 (adapter USB-TTL, 115200). Buka serial monitor di port adapter.
 */
#include <DynamixelShield.h>

#define HOST Serial1
const uint32_t BAUDS[] = {1000000, 57600};  // 1 Mbps = default AX-12A

DynamixelShield dxl;

void setup() {
  HOST.begin(115200);
  while (!HOST) {}
  dxl.setPortProtocolVersion(1.0);

  HOST.println(F("== Scan DYNAMIXEL (Protocol 1.0) =="));
  uint8_t total = 0;
  for (uint8_t b = 0; b < sizeof(BAUDS) / sizeof(BAUDS[0]); b++) {
    dxl.begin(BAUDS[b]);
    HOST.print(F("Baud ")); HOST.print(BAUDS[b]); HOST.println(F(" ..."));
    for (uint16_t id = 0; id < 254; id++) {
      if (dxl.ping(id)) {
        HOST.print(F("  ditemukan ID ")); HOST.print(id);
        HOST.print(F("  model ")); HOST.println(dxl.getModelNumber(id));
        total++;
      }
    }
  }
  HOST.print(F("Selesai. Total: ")); HOST.println(total);
}

void loop() {}
