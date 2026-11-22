/*
 * ax12_bridge.ino v0.2 — Bridge serial laptop <-> 5x DYNAMIXEL AX-12A + 1 servo PWM gripper (25 kg, DS3225)
 * Board : Arduino Mega 2560 + ROBOTIS DYNAMIXEL Shield
 * Lib   : DynamixelShield + Dynamixel2Arduino (Library Manager), Servo (bawaan Arduino)
 *
 * Bus DYNAMIXEL : Serial (D0/D1) + DIR D2 via shield, 1 Mbps, Protocol 1.0
 * Link laptop   : Serial1 (TX1=18, RX1=19) via adapter USB-TTL 5V, 115200 baud
 * Gripper       : sinyal PWM di GRIPPER_PIN (D22). Daya servo dari buck 6 V terpisah, GND bersama!
 *
 * Upload: UART switch shield ke "Upload" -> upload -> kembalikan ke "DYNAMIXEL".
 * Protokol teks: lihat ../PROTOCOL.md
 */
#include <DynamixelShield.h>
#include <Servo.h>

#define HOST Serial1
const uint32_t HOST_BAUD    = 115200;
const uint32_t DXL_BAUD     = 1000000;
const float    DXL_PROTOCOL = 1.0;

// ---------------- AX-12A (5 sendi): base yaw, bahu, siku, wrist pitch, wrist roll
const uint8_t NUM_AX = 5;
const uint8_t DXL_IDS[NUM_AX] = {1, 2, 3, 4, 5};
// Batas aman raw (0..1023, 512 = tengah, 1 unit = 0.29 derajat). AWAL KONSERVATIF (+/- ~90 derajat).
// WAJIB disesuaikan setelah dicek manual (torque off) pada robot yang sudah dirakit.
const uint16_t LIMIT_MIN[NUM_AX] = {205, 205, 205, 205, 205};
const uint16_t LIMIT_MAX[NUM_AX] = {818, 818, 818, 818, 818};
const uint16_t DEFAULT_SPEED     = 100;  // Moving Speed AX (1..1023). 0 = tanpa batas -> tidak dipakai

// ---------------- Gripper servo PWM 25 kg (tanpa feedback posisi)
const uint8_t  GRIPPER_PIN     = 22;    // header digital Mega yang tidak tertutup shield
// Pulsa dalam mikrodetik. DS3225: 500..2500 us = ~180 derajat. Batasi agar tuas PLA tidak patah.
// Isi setelah uji: GRIP_US_OPEN = jari terbuka penuh, GRIP_US_CLOSE = jari hampir bertemu (bukan menekan!).
const uint16_t GRIP_US_MIN     = 1000;  // batas keras bawah
const uint16_t GRIP_US_MAX     = 2000;  // batas keras atas
const uint16_t GRIP_US_SAFE    = 1500;  // posisi saat gripper diaktifkan pertama kali
const uint16_t GRIP_SLEW_US_PER_TICK = 20;  // pelan-pelan: maks perubahan pulsa per 20 ms (~ 1000 us/s)

// ---------------- Lain-lain
const uint16_t LOW_VOLT_DV       = 105;  // 10.5 V (3.5 V/sel LiPo 3S). Satuan 0.1 V
const uint8_t  LOW_VOLT_HITS_MAX = 3;
const uint16_t STATE_PERIOD_MS   = 20;   // 50 Hz baris "J"
const uint16_t HEALTH_PERIOD_MS  = 1000; // 1 Hz baris "H"

DynamixelShield dxl;
Servo gripper;
using namespace ControlTableItem;

bool     present_ok[NUM_AX];
int16_t  present_pos[NUM_AX];
uint16_t goal_pos[NUM_AX];
bool     torque_enabled = false;
uint16_t grip_goal_us = GRIP_US_SAFE;
uint16_t grip_cmd_us  = GRIP_US_SAFE;   // pulsa yang benar-benar dikirim (setelah slew)

char     line_buf[128];
uint8_t  line_len = 0;
uint32_t t_state = 0, t_health = 0;
uint8_t  low_volt_hits = 0;

uint16_t clampAx(uint8_t i, long v) {
  if (v < LIMIT_MIN[i]) return LIMIT_MIN[i];
  if (v > LIMIT_MAX[i]) return LIMIT_MAX[i];
  return (uint16_t)v;
}

uint16_t clampGrip(long us) {
  if (us < GRIP_US_MIN) return GRIP_US_MIN;
  if (us > GRIP_US_MAX) return GRIP_US_MAX;
  return (uint16_t)us;
}

void readPositions() {
  for (uint8_t i = 0; i < NUM_AX; i++) {
    int32_t v = dxl.readControlTableItem(PRESENT_POSITION, DXL_IDS[i]);
    if (dxl.getLastLibErrCode() != 0) {
      present_ok[i] = false;
      present_pos[i] = -1;
    } else {
      present_ok[i] = true;
      present_pos[i] = (int16_t)v;
    }
  }
}

void sendState() {
  HOST.print(F("J "));
  HOST.print(millis());
  for (uint8_t i = 0; i < NUM_AX; i++) { HOST.print(' '); HOST.print(present_pos[i]); }
  HOST.print(' ');
  HOST.print(torque_enabled ? (int)grip_cmd_us : -1);  // gripper: pulsa yang dikirim (bukan posisi terukur)
  HOST.print('\n');
}

void setTorqueAll(bool on) {
  if (on) {
    readPositions();  // goal = posisi sekarang -> tidak ada lonjakan
    for (uint8_t i = 0; i < NUM_AX; i++) {
      if (!present_ok[i]) continue;
      goal_pos[i] = clampAx(i, present_pos[i]);
      dxl.writeControlTableItem(MOVING_SPEED, DXL_IDS[i], DEFAULT_SPEED);
      dxl.writeControlTableItem(GOAL_POSITION, DXL_IDS[i], goal_pos[i]);
    }
    for (uint8_t i = 0; i < NUM_AX; i++) if (present_ok[i]) dxl.torqueOn(DXL_IDS[i]);
    // Servo PWM tidak bisa dibaca posisinya: saat attach ia langsung menuju pulsa yang diberikan.
    grip_cmd_us = grip_goal_us = clampGrip(grip_goal_us);
    gripper.writeMicroseconds(grip_cmd_us);
    if (!gripper.attached()) gripper.attach(GRIPPER_PIN, 500, 2500);
  } else {
    for (uint8_t i = 0; i < NUM_AX; i++) dxl.torqueOff(DXL_IDS[i]);
    gripper.detach();  // tanpa pulsa -> servo lemas (tidak menahan)
  }
  torque_enabled = on;
}

void stepGripper() {
  if (!torque_enabled) return;
  if (grip_cmd_us < grip_goal_us) grip_cmd_us = min((uint16_t)(grip_cmd_us + GRIP_SLEW_US_PER_TICK), grip_goal_us);
  else if (grip_cmd_us > grip_goal_us) grip_cmd_us = max((uint16_t)(grip_cmd_us - GRIP_SLEW_US_PER_TICK), grip_goal_us);
  gripper.writeMicroseconds(grip_cmd_us);
}

void sendHealth() {
  int32_t volt_dv = -1;
  for (uint8_t i = 0; i < NUM_AX && volt_dv < 0; i++) {
    int32_t v = dxl.readControlTableItem(PRESENT_VOLTAGE, DXL_IDS[i]);
    if (dxl.getLastLibErrCode() == 0) volt_dv = v;
  }
  HOST.print(F("H "));
  HOST.print(volt_dv);
  for (uint8_t i = 0; i < NUM_AX; i++) {
    int32_t t = dxl.readControlTableItem(PRESENT_TEMPERATURE, DXL_IDS[i]);
    HOST.print(' ');
    HOST.print(dxl.getLastLibErrCode() == 0 ? t : -1);
  }
  HOST.print('\n');

  // Proteksi tegangan rendah LiPo (cadangan, bukan pengganti alarm hardware)
  if (volt_dv > 0 && volt_dv < LOW_VOLT_DV) {
    if (++low_volt_hits >= LOW_VOLT_HITS_MAX && torque_enabled) {
      setTorqueAll(false);
      HOST.print(F("E LOWBATT "));
      HOST.println(volt_dv);
    }
  } else {
    low_volt_hits = 0;
  }
}

void sendPresence() {
  HOST.print(F("I"));
  for (uint8_t i = 0; i < NUM_AX; i++) {
    HOST.print(' ');
    HOST.print(dxl.ping(DXL_IDS[i]) ? 1 : 0);
  }
  HOST.print('\n');
}

bool parseInts(long *out, uint8_t n) {
  for (uint8_t i = 0; i < n; i++) {
    char *tok = strtok(NULL, " ");
    if (tok == NULL) return false;
    char *end;
    out[i] = strtol(tok, &end, 10);
    if (*end != '\0') return false;
  }
  return true;
}

void handleLine(char *line) {
  char *cmd = strtok(line, " ");
  if (cmd == NULL) return;

  if (strcmp(cmd, "PING") == 0) {
    HOST.println(F("OK PONG"));
  } else if (strcmp(cmd, "S") == 0) {
    sendPresence();
  } else if (strcmp(cmd, "T") == 0) {
    long v[1];
    if (!parseInts(v, 1)) { HOST.println(F("E PARSE")); return; }
    setTorqueAll(v[0] != 0);
    HOST.print(F("OK T ")); HOST.println(torque_enabled ? 1 : 0);
  } else if (strcmp(cmd, "X") == 0) {
    setTorqueAll(false);
    HOST.println(F("OK X"));
  } else if (strcmp(cmd, "P") == 0) {       // P ax1 ax2 ax3 ax4 ax5 grip_us
    long v[NUM_AX + 1];
    if (!parseInts(v, NUM_AX + 1)) { HOST.println(F("E PARSE")); return; }
    if (!torque_enabled) { HOST.println(F("E TORQUE_OFF")); return; }
    for (uint8_t i = 0; i < NUM_AX; i++) {
      goal_pos[i] = clampAx(i, v[i]);
      dxl.writeControlTableItem(GOAL_POSITION, DXL_IDS[i], goal_pos[i]);
    }
    grip_goal_us = clampGrip(v[NUM_AX]);
  } else if (strcmp(cmd, "G") == 0) {       // G grip_us  (gripper saja)
    long v[1];
    if (!parseInts(v, 1)) { HOST.println(F("E PARSE")); return; }
    if (!torque_enabled) { HOST.println(F("E TORQUE_OFF")); return; }
    grip_goal_us = clampGrip(v[0]);
  } else if (strcmp(cmd, "V") == 0) {       // V v1..v5 (moving speed AX)
    long v[NUM_AX];
    if (!parseInts(v, NUM_AX)) { HOST.println(F("E PARSE")); return; }
    for (uint8_t i = 0; i < NUM_AX; i++) {
      long s = v[i];
      if (s < 1) s = 1;
      if (s > 1023) s = 1023;
      dxl.writeControlTableItem(MOVING_SPEED, DXL_IDS[i], (uint16_t)s);
    }
    HOST.println(F("OK V"));
  } else {
    HOST.println(F("E UNKNOWN"));
  }
}

void pollHost() {
  while (HOST.available()) {
    char c = HOST.read();
    if (c == '\r') continue;
    if (c == '\n') {
      line_buf[line_len] = '\0';
      handleLine(line_buf);
      line_len = 0;
    } else if (line_len < sizeof(line_buf) - 1) {
      line_buf[line_len++] = c;
    } else {
      line_len = 0;
      HOST.println(F("E OVERFLOW"));
    }
  }
}

void setup() {
  HOST.begin(HOST_BAUD);
  dxl.begin(DXL_BAUD);
  dxl.setPortProtocolVersion(DXL_PROTOCOL);

  setTorqueAll(false);  // mulai aman: AX torque off, gripper tanpa pulsa
  HOST.println(F("OK BOOT ax12_bridge v0.2 (5xAX12A + PWM gripper)"));
  sendPresence();
}

void loop() {
  pollHost();
  uint32_t now = millis();
  if (now - t_state >= STATE_PERIOD_MS) {
    t_state = now;
    stepGripper();
    readPositions();
    sendState();
  }
  if (now - t_health >= HEALTH_PERIOD_MS) {
    t_health = now;
    sendHealth();
  }
}
