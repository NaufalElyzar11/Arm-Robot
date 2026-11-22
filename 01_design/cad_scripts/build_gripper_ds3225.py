"""Gripper untuk servo standar 25 kg (DS3225-class) menggantikan AX-12A ke-6.

Semua part dimodelkan di FRAME GRIPPER "g" yang sama dengan file asli Thingiverse
`the_crawer_base.stl`:
  - z = 0  : sisi bawah plat gripper (dulu = muka depan AX-12A)
  - sumbu horn gripper di (X=31, Y=65), sejajar +Z; sumbu ini segaris dengan sumbu wrist roll
  - jari (12) meluncur sepanjang X di sayap plat; tuas (11) di z = 5.5 .. 11

Konsep:
  09  gripper_cradle   : dudukan berbentuk U. Dasarnya dibaut ke horn AX-12A wrist roll
                         (4x M2, PCD 16), dua dinding menyangga "kuping" (ear) DS3225.
  10  gripper_base     : plat crawer asli + kaki ke kuping servo, lubang horn diperbesar,
                         lubang AX-12A lama ditutup. Baut M3x30 tembus plat-kaki-kuping-dinding
                         cradle, mur M3 terkunci di dinding cradle.
  11b horn_adapter_25t : piringan yang dibaut ke horn aluminium bulat 25T (Ø20, 4x M3 PCD 14).
                         Menyediakan 2 pin tuas di radius 8 mm & tinggi z=5 -> kinematika
                         gripper persis sama dengan versi AX-12A (tuas 11 & jari 12 tidak berubah).

!!! UKUR SERVO & HORN ANDA DENGAN JANGKA SORONG, lalu sesuaikan parameter di bawah. !!!
Nilai default = DS3225 / servo standar 40x20 mm pada umumnya + horn disc aluminium 25T Ø20.
"""
import math

import cadquery as cq

# ----------------------------------------------------------------- parameter servo (UKUR!)
DS_BODY_L = 40.0            # panjang bodi (arah Y_g)
DS_BODY_W = 20.0            # lebar bodi (arah X_g)
DS_CASE_H = 40.5            # bawah bodi -> permukaan atas case (tanpa spline)
DS_SHAFT_FROM_END = 10.0    # pusat poros output -> ujung bodi terdekat
DS_EAR_TOTAL_L = 54.5       # panjang total termasuk kedua kuping
DS_EAR_HOLE_PITCH_L = 49.5  # jarak lubang kuping sepanjang bodi
DS_EAR_HOLE_PITCH_W = 10.0  # jarak lubang kuping melintang
DS_EAR_T = 2.5              # tebal kuping
DS_EAR_TOP_BELOW_CASE_TOP = 11.0  # permukaan ATAS kuping -> permukaan atas case
HORN_TOP_ABOVE_CASE_TOP = 5.0     # permukaan atas horn disc (terpasang) -> atas case
HORN_DISC_D = 20.0
HORN_DISC_T = 4.0
HORN_HOLE_PCD = 14.0        # 4 lubang M3 ulir di horn disc

# ----------------------------------------------------------------- parameter desain
HX, HY = 31.0, 65.0         # sumbu horn gripper = sumbu wrist roll (frame g)
PLATE_T = 5.0               # tebal plat crawer asli
ADAPTER_T = 3.0
ADAPTER_D = 24.0
LEVER_PIN_R = 8.0           # = radius lubang horn AX-12A (PCD 16) -> tuas asli tetap cocok
LEVER_PIN_ANGLE = 195.7     # orientasi pin pada pose assembly (derajat, frame g)
PIN_PILOT_D = 2.1           # untuk sekrup M2.5 self-tapping
M3_CLEAR_D = 3.4
M3_CSK_D = 6.4
M3_NUT_AF = 5.8             # celah kunci mur M3 (5.5 + toleransi)
M3_NUT_T = 2.8
M2_CLEAR_D = 2.4
M2_HEAD_D = 4.4
M2_HEAD_CB = 1.6
SHIM_ALLOWANCE = 1.0        # kaki sengaja dibuat 1 mm lebih pendek -> setel dengan ring M3
SERVO_BOTTOM_CLEAR = 2.0    # servo menggantung di kuping, tidak menapak di dasar cradle
CRADLE_BASE_T = 5.0
CRADLE_WALL_X = 24.0
CRADLE_WALL_CLEAR = 0.5     # celah dinding cradle ke ujung bodi servo
HORN_CLEAR_R = 13.0         # lubang plat di sekitar horn+adapter
AX_HORN_PCD = 16.0          # pola baut horn AX-12A (wrist roll)
AX_HORN_CENTER_D = 8.4

# ----------------------------------------------------------------- turunan (frame g)
Z_ADAPTER_TOP = PLATE_T                     # = tinggi muka horn AX-12A di desain asli
Z_HORN_TOP = Z_ADAPTER_TOP - ADAPTER_T      # 2.0
Z_CASE_TOP = Z_HORN_TOP - HORN_TOP_ABOVE_CASE_TOP   # -3.0
Z_EAR_TOP = Z_CASE_TOP - DS_EAR_TOP_BELOW_CASE_TOP  # -14.0
Z_EAR_BOT = Z_EAR_TOP - DS_EAR_T                    # -16.5
Z_SERVO_BOT = Z_CASE_TOP - DS_CASE_H                # -43.5
Z_CRADLE_BASE_TOP = Z_SERVO_BOT - SERVO_BOTTOM_CLEAR  # -45.5
Z_CRADLE_BOT = Z_CRADLE_BASE_TOP - CRADLE_BASE_T      # -50.5  (menempel muka horn wrist roll)
Z_LEG_BOT = Z_EAR_TOP + SHIM_ALLOWANCE              # -13.0

BODY_Y0 = HY + DS_SHAFT_FROM_END - DS_BODY_L        # 35.0
BODY_Y1 = HY + DS_SHAFT_FROM_END                    # 75.0
BODY_YC = (BODY_Y0 + BODY_Y1) / 2.0                 # 55.0
EAR_Y0 = BODY_YC - DS_EAR_TOTAL_L / 2.0             # 27.75
EAR_Y1 = BODY_YC + DS_EAR_TOTAL_L / 2.0             # 82.25
EAR_HOLES = [(HX + sx * DS_EAR_HOLE_PITCH_W / 2.0, BODY_YC + sy * DS_EAR_HOLE_PITCH_L / 2.0)
             for sy in (-1, 1) for sx in (-1, 1)]

# Jarak muka horn wrist roll -> bawah plat gripper (dipakai assembly & URDF)
WRIST_HORN_TO_PLATE = -Z_CRADLE_BOT                 # 50.5 mm


def _box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0)).val()


def _cyl(x, y, z0, h, d):
    return cq.Solid.makeCylinder(d / 2.0, h, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def _fuse(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.clean()


def _cut(shape, tools):
    for t in tools:
        shape = shape.cut(t)
    return shape.clean()


def _hex_prism(x, y, z0, h, af, angle_deg=0.0):
    r = af / math.sqrt(3.0)
    pts = [(x + r * math.cos(math.radians(60 * i + angle_deg)), y + r * math.sin(math.radians(60 * i + angle_deg)))
           for i in range(6)]
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(h).val()


# ================================================================= part referensi DS3225
def build_ds3225_reference():
    body = _box(HX - DS_BODY_W / 2, HX + DS_BODY_W / 2, BODY_Y0, BODY_Y1, Z_SERVO_BOT, Z_CASE_TOP)
    ears = _box(HX - DS_BODY_W / 2, HX + DS_BODY_W / 2, EAR_Y0, EAR_Y1, Z_EAR_BOT, Z_EAR_TOP)
    boss = _cyl(HX, HY, Z_CASE_TOP, 1.0, 13.0)
    spline = _cyl(HX, HY, Z_CASE_TOP, Z_HORN_TOP - Z_CASE_TOP - 0.5, 6.0)
    horn = _cyl(HX, HY, Z_HORN_TOP - HORN_DISC_T, HORN_DISC_T, HORN_DISC_D)
    grommet = _box(HX - 4, HX + 4, BODY_Y0 - 3.0, BODY_Y0, Z_SERVO_BOT + 3, Z_SERVO_BOT + 9)
    s = _fuse([body, ears, boss, spline, horn, grommet])
    holes = [_cyl(x, y, Z_EAR_BOT - 1, DS_EAR_T + 2, 4.5) for x, y in EAR_HOLES]
    horn_holes = [_cyl(HX + HORN_HOLE_PCD / 2 * math.cos(math.radians(a)), HY + HORN_HOLE_PCD / 2 * math.sin(math.radians(a)),
                       Z_HORN_TOP - HORN_DISC_T - 0.5, HORN_DISC_T + 1, 3.0) for a in (45, 135, 225, 315)]
    return _cut(s, holes + horn_holes)


# ================================================================= 09 cradle
def build_gripper_cradle():
    wx0, wx1 = HX - CRADLE_WALL_X / 2, HX + CRADLE_WALL_X / 2
    wall_lo_y = (EAR_Y0 - 1.25, BODY_Y0 - CRADLE_WALL_CLEAR)      # sisi kabel (jauh dari poros)
    wall_hi_y = (BODY_Y1 + CRADLE_WALL_CLEAR, EAR_Y1 + 1.25)      # sisi poros
    base = _box(wx0, wx1, wall_lo_y[0], wall_hi_y[1], Z_CRADLE_BOT, Z_CRADLE_BASE_TOP)
    base = base.fillet(4.0, [e for e in base.Edges() if abs(e.tangentAt().z) > 0.99])
    w_lo = _box(wx0, wx1, wall_lo_y[0], wall_lo_y[1], Z_CRADLE_BASE_TOP - 0.01, Z_EAR_BOT)
    w_hi = _box(wx0, wx1, wall_hi_y[0], wall_hi_y[1], Z_CRADLE_BASE_TOP - 0.01, Z_EAR_BOT)
    s = _fuse([base, w_lo, w_hi])

    tools = []
    # lubang baut kuping + kantong mur (masuk dari sisi luar dinding)
    for x, y in EAR_HOLES:
        tools.append(_cyl(x, y, Z_CRADLE_BASE_TOP, Z_EAR_BOT - Z_CRADLE_BASE_TOP + 1, M3_CLEAR_D))
        z_nut = Z_EAR_BOT - 8.0
        outer = wall_lo_y[0] if y < HY else wall_hi_y[1]
        y_in = y
        y_out = outer - 1.0 if y < HY else outer + 1.0
        nut = _hex_prism(x, y_in, z_nut, M3_NUT_T, M3_NUT_AF, angle_deg=30.0)
        slot = _box(x - M3_NUT_AF / 2, x + M3_NUT_AF / 2, min(y_in, y_out), max(y_in, y_out), z_nut, z_nut + M3_NUT_T)
        tools += [nut, slot]
    # celah kabel servo di dinding sisi jauh dari poros
    tools.append(_box(HX - 5.5, HX + 5.5, wall_lo_y[0] - 1, wall_lo_y[1] + 1, Z_CRADLE_BASE_TOP - 0.01, Z_CRADLE_BASE_TOP + 11.0))
    # pola horn AX-12A (wrist roll): 4x M2 tembus + counterbore dari atas, lubang tengah
    for a in (0, 90, 180, 270):
        x = HX + AX_HORN_PCD / 2 * math.cos(math.radians(a))
        y = HY + AX_HORN_PCD / 2 * math.sin(math.radians(a))
        tools.append(_cyl(x, y, Z_CRADLE_BOT - 1, CRADLE_BASE_T + 2, M2_CLEAR_D))
        tools.append(_cyl(x, y, Z_CRADLE_BASE_TOP - M2_HEAD_CB, M2_HEAD_CB + 1, M2_HEAD_D))
    tools.append(_cyl(HX, HY, Z_CRADLE_BOT - 1, CRADLE_BASE_T + 2, AX_HORN_CENTER_D))
    # pengurangan berat di dasar (di luar area horn)
    tools.append(_box(HX - 6, HX + 6, wall_lo_y[1] + 3, HY - 12, Z_CRADLE_BOT - 1, Z_CRADLE_BASE_TOP + 1))
    return _cut(s, tools)


# ================================================================= 10 plat gripper
def build_gripper_base(orig_base_solid):
    """Plat crawer asli dimodifikasi: tutup lubang AX lama, tambah kaki & pad, perbesar lubang horn."""
    patch = _box(14.5, 47.5, 26.5, BODY_Y0, 0.0, PLATE_T)
    patch = patch.fillet(4.5, [e for e in patch.Edges() if abs(e.tangentAt().z) > 0.99 and e.Center().y < 30])
    side_l = _box(14.5, 20.5, 26.5, 52.5, 0.0, PLATE_T)
    side_r = _box(41.5, 47.5, 26.5, 52.5, 0.0, PLATE_T)
    pad_top = _box(HX - 11, HX + 11, 76.0, EAR_Y1 + 3.0, 0.0, PLATE_T)
    pad_top = pad_top.fillet(3.0, [e for e in pad_top.Edges() if abs(e.tangentAt().z) > 0.99 and e.Center().y > 80])
    leg_lo = _box(HX - DS_BODY_W / 2, HX + DS_BODY_W / 2, EAR_Y0, BODY_Y0 - CRADLE_WALL_CLEAR, Z_LEG_BOT, 0.01)
    leg_hi = _box(HX - DS_BODY_W / 2, HX + DS_BODY_W / 2, BODY_Y1 + CRADLE_WALL_CLEAR, EAR_Y1, Z_LEG_BOT, 0.01)
    s = _fuse([orig_base_solid, patch, side_l, side_r, pad_top, leg_lo, leg_hi])

    tools = [_cyl(HX, HY, Z_CASE_TOP, PLATE_T - Z_CASE_TOP + 1, 2 * HORN_CLEAR_R)]
    for x, y in EAR_HOLES:
        tools.append(_cyl(x, y, Z_LEG_BOT - 1, PLATE_T - Z_LEG_BOT + 2, M3_CLEAR_D))
        tools.append(_cyl(x, y, PLATE_T - 3.2, 4.0, M3_CSK_D))   # counterbore kepala baut M3
    return _cut(s, tools)


# ================================================================= 11b adapter horn
def build_horn_adapter():
    z0 = Z_HORN_TOP
    s = _cyl(HX, HY, z0, ADAPTER_T, ADAPTER_D)
    tools = [_cyl(HX, HY, z0 - 1, ADAPTER_T + 2, 6.5)]
    for a in (45, 135, 225, 315):   # baut M3 kepala countersunk ke horn disc
        x = HX + HORN_HOLE_PCD / 2 * math.cos(math.radians(a + LEVER_PIN_ANGLE))
        y = HY + HORN_HOLE_PCD / 2 * math.sin(math.radians(a + LEVER_PIN_ANGLE))
        tools.append(_cyl(x, y, z0 - 1, ADAPTER_T + 2, M3_CLEAR_D))
        tools.append(cq.Solid.makeCone(M3_CLEAR_D / 2, M3_CSK_D / 2, 1.6, cq.Vector(x, y, z0 + ADAPTER_T - 1.6), cq.Vector(0, 0, 1)))
    for a in (LEVER_PIN_ANGLE, LEVER_PIN_ANGLE + 180):   # pin tuas (radius 8 = horn AX-12A)
        x = HX + LEVER_PIN_R * math.cos(math.radians(a))
        y = HY + LEVER_PIN_R * math.sin(math.radians(a))
        tools.append(_cyl(x, y, z0 - 1, ADAPTER_T + 2, PIN_PILOT_D))
    return _cut(s, tools)


if __name__ == "__main__":
    for name, fn in [("ds3225", build_ds3225_reference), ("cradle", build_gripper_cradle), ("adapter", build_horn_adapter)]:
        sh = fn()
        bb = sh.BoundingBox()
        print(f"{name:8s} valid={sh.isValid()} vol={sh.Volume()/1000:.1f}cm3 bbox=({bb.xmin:.1f},{bb.ymin:.1f},{bb.zmin:.1f})..({bb.xmax:.1f},{bb.ymax:.1f},{bb.zmax:.1f})")
    print("Z levels:", dict(case_top=Z_CASE_TOP, ear_top=Z_EAR_TOP, ear_bot=Z_EAR_BOT, servo_bot=Z_SERVO_BOT,
                            cradle_bot=Z_CRADLE_BOT, leg_bot=Z_LEG_BOT, wrist_horn_to_plate=WRIST_HORN_TO_PLATE))
