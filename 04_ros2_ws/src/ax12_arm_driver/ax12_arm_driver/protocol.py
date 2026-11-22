"""Konversi satuan dan parser protokol teks ax12_bridge v0.2 (tanpa dependensi ROS, mudah dites).

Robot: 5x AX-12A (raw 0..1023) + 1 servo PWM gripper (pulsa mikrodetik, tanpa feedback).
Baris J: "J <ms> ax1..ax5 grip_us"  (grip_us = -1 bila gripper tidak aktif)
Baris H: "H <volt_dV> t1..t5"
Baris I: "I p1..p5"
"""
import math
from dataclasses import dataclass, field
from typing import List, Optional

AX_RAW_MIN = 0
AX_RAW_MAX = 1023
RAD_PER_UNIT = math.radians(300.0 / 1023.0)  # 1 unit ~ 0.29 derajat
N_AX = 5


def us_to_rad(us: float, zero_us: float, direction: int, deg_per_2000us: float = 180.0) -> float:
    """Pulsa servo PWM -> sudut horn (rad). DS3225 standar: 500..2500 us = 180 derajat."""
    return direction * (us - zero_us) * math.radians(deg_per_2000us) / 2000.0


def rad_to_us(rad: float, zero_us: float, direction: int, deg_per_2000us: float = 180.0,
              us_min: int = 500, us_max: int = 2500) -> int:
    us = int(round(zero_us + direction * rad * 2000.0 / math.radians(deg_per_2000us)))
    return max(us_min, min(us_max, us))


def raw_to_rad(raw: int, zero_raw: int, direction: int) -> float:
    return direction * (raw - zero_raw) * RAD_PER_UNIT


def rad_to_raw(rad: float, zero_raw: int, direction: int) -> int:
    raw = int(round(zero_raw + direction * rad / RAD_PER_UNIT))
    return max(AX_RAW_MIN, min(AX_RAW_MAX, raw))


@dataclass
class Message:
    kind: str                       # 'J', 'H', 'I', 'E', 'OK', atau 'UNKNOWN'
    values: List[int] = field(default_factory=list)
    text: str = ''
    stamp_ms: Optional[int] = None


def parse_line(line: str, n_ax: int = N_AX) -> Message:
    """Ubah satu baris dari firmware menjadi Message. Tidak pernah melempar exception."""
    line = line.strip()
    if not line:
        return Message('UNKNOWN', text=line)
    parts = line.split()
    head = parts[0]
    try:
        if head == 'J' and len(parts) == 2 + n_ax + 1:
            return Message('J', [int(p) for p in parts[2:]], stamp_ms=int(parts[1]))
        if head == 'H' and len(parts) == 2 + n_ax:
            return Message('H', [int(p) for p in parts[1:]])
        if head == 'I' and len(parts) == 1 + n_ax:
            return Message('I', [int(p) for p in parts[1:]])
    except ValueError:
        return Message('UNKNOWN', text=line)
    if head == 'E':
        return Message('E', text=' '.join(parts[1:]))
    if head == 'OK':
        return Message('OK', text=' '.join(parts[1:]))
    return Message('UNKNOWN', text=line)


def format_goal(ax_raw: List[int], grip_us: int) -> str:
    return 'P ' + ' '.join(str(int(v)) for v in ax_raw) + f' {int(grip_us)}\n'
