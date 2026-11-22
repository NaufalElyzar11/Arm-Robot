# PCB distribusi daya

Simpan file KiCad / Gerber di folder ini.

## Kebutuhan minimum

- Input: XT60 dari LiPo 3S → saklar → sekring 10 A.
- Proteksi polaritas terbalik (P-MOSFET ideal diode atau minimal dioda Schottky berkapasitas besar).
- Kapasitor bulk 1000–2200 µF / 25 V dekat konektor servo.
- 2–3 konektor AX (3-pin): V+, GND, DATA. DATA diteruskan dari shield, V+ dari PCB.
- Titik ukur tegangan + LED indikator.
- **Buck 6.0 V ≥ 5 A** untuk servo gripper 25 kg (DS3225: 4.8–6.8 V, stall ±2.3–2.9 A) + konektor servo
  3-pin standar (sinyal diteruskan dari Mega D22).
- Opsional: buck 12 V ≥10 A bila tidak ingin bus AX menerima 12.6 V saat LiPo penuh.
- Opsional: pembagi tegangan ke pin analog Mega (mis. A0) untuk monitor baterai langsung.
- GND PCB disambung ke GND shield/Mega (common ground).
