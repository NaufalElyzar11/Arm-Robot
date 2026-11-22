import math

from ax12_arm_driver.protocol import (RAD_PER_UNIT, format_goal, parse_line,
                                      rad_to_raw, rad_to_us, raw_to_rad, us_to_rad)


def test_roundtrip_center_is_zero():
    assert raw_to_rad(512, 512, 1) == 0.0
    assert rad_to_raw(0.0, 512, 1) == 512


def test_direction_and_scale():
    assert math.isclose(raw_to_rad(512 + 100, 512, -1), -100 * RAD_PER_UNIT)
    assert rad_to_raw(math.radians(150), 512, 1) == 1023  # clamp di batas atas


def test_pwm_gripper_conversion():
    assert math.isclose(us_to_rad(2500, 500, 1), math.pi)          # 2000 us = 180 derajat
    assert rad_to_us(math.pi / 4, 1000, 1) == 1500                  # 45 derajat = 500 us
    assert rad_to_us(10.0, 1000, 1, us_max=2000) == 2000            # clamp


def test_parse_state_and_health():
    m = parse_line('J 1234 512 500 -1 600 512 1500')
    assert m.kind == 'J' and m.stamp_ms == 1234 and m.values[2] == -1 and m.values[5] == 1500
    h = parse_line('H 118 35 36 40 38 33')
    assert h.kind == 'H' and h.values[0] == 118 and len(h.values) == 6
    assert parse_line('I 1 1 1 1 1').kind == 'I'
    assert parse_line('E LOWBATT 104').kind == 'E'
    assert parse_line('J 1 2 3').kind == 'UNKNOWN'


def test_format_goal():
    assert format_goal([512] * 5, 1500) == 'P 512 512 512 512 512 1500\n'
