"""Build Full Robot Arm STEP Assembly + Complete Separated STL Backup & Preview Package.

Creates two dedicated folders in F:\\Projects\\Robot Arm:
1. F:\\Projects\\Robot Arm\\AX12A_WidowX_Full_STEP
   - 00_FULL_ROBOT_ARM_ASSEMBLY.step (5-DOF arm, 5x AX-12A + 25kg DS3225 gripper servo, WidowX hybrid base)
   - 00_FULL_ROBOT_ARM_PRINTED_PARTS_ONLY.step (All printed structural parts in assembled pose)
   - Individual .step files for every single part (01 through 13) for CAD editing / backup

2. F:\\Projects\\Robot Arm\\AX12A_WidowX_Full_STL
   - 00_FULL_ROBOT_ARM_PREVIEW.stl (Combined full 3D robot arm mesh for instant 3D preview)
   - 00_FULL_ROBOT_ARM_PRINTED_PARTS_PREVIEW.stl (Combined printed parts in assembled pose)
   - Individual print-ready .stl files (01 through 12, placed at Z_min = 0) for replacing any broken part
   - High-res preview renders: PREVIEW_FULL_ROBOT_ARM.png & KATALOG_SEMUA_PART_STL.png
"""
from pathlib import Path
import json
import math
import shutil
import tempfile

import cadquery as cq
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape, TopoDS
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SHELL

import build_hybrid_base as hb
import build_gripper_ds3225 as gds

ROOT = Path(__file__).resolve().parent.parent
AX_ORIG_DIR = ROOT / "source" / "ax12a_arm_thingiverse_166430" / "files"
STEP_OUT_DIR = ROOT / "step"
STL_OUT_DIR = ROOT / "stl"

for d in (STEP_OUT_DIR, STL_OUT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def stl_to_cq_solid(stl_path, clean_zero_area=False, sew_tol=1e-2):
    """Load an STL file (optionally cleaning degenerate triangles) into a valid CadQuery Solid/Shell."""
    read_path = str(stl_path)
    tmp_path = None
    if clean_zero_area:
        m = trimesh.load_mesh(stl_path)
        m.update_faces(m.area_faces > 1e-4)
        m.remove_unreferenced_vertices()
        tmp = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
        tmp.close()
        m.export(tmp.name)
        read_path = tmp.name
        tmp_path = Path(tmp.name)

    shape = TopoDS_Shape()
    StlAPI_Reader().Read(shape, read_path)
    sew = BRepBuilderAPI_Sewing(sew_tol)
    sew.Add(shape)
    sew.Perform()
    sewed = sew.SewedShape()
    exp = TopExp_Explorer(sewed, TopAbs_SHELL)
    ms = BRepBuilderAPI_MakeSolid()
    shells = 0
    while exp.More():
        shells += 1
        ms.Add(TopoDS.Shell_s(exp.Current()))
        exp.Next()
    result = cq.Shape(ms.Solid()) if shells > 0 else cq.Shape(sewed)
    if tmp_path and tmp_path.exists():
        tmp_path.unlink()
    return result


def build_ax12a_servo_solid():
    """Build a detailed reference B-Rep solid of a Dynamixel AX-12A actuator.

    Local frame convention:
    - Origin (0, 0, 0) at center of output horn mounting face (front body face z=0)
    - Output horn protrudes to z = +5.0 mm (Ø22 mm)
    - Main body (32 x 50 x 32 mm): X in [-16, +16], Y in [-38.5, +11.5], Z in [-32, 0]
    - Rear passive hinge boss protrudes to z = -35.0 mm (Ø16 mm)
    """
    body = cq.Workplane("XY").box(32.0, 50.0, 32.0).val().translate((0.0, -13.5, -16.0))
    # Side mounting earschamfered profile visual detail
    flange_f = cq.Workplane("XY").box(32.0, 34.0, 3.0).val().translate((0.0, -18.5, -1.5))
    horn_boss = cq.Solid.makeCylinder(13.0, 1.5, cq.Vector(0, 0, 0.0), cq.Vector(0, 0, 1))
    horn_disc = cq.Solid.makeCylinder(11.0, 5.0, cq.Vector(0, 0, 0.0), cq.Vector(0, 0, 1))
    rear_boss = cq.Solid.makeCylinder(8.0, 3.0, cq.Vector(0, 0, -35.0), cq.Vector(0, 0, 1))
    servo = hb.fuse_all([body, flange_f, horn_boss, horn_disc, rear_boss])
    # Center screw recess on horn
    recess = cq.Solid.makeCylinder(3.0, 3.0, cq.Vector(0, 0, 3.0), cq.Vector(0, 0, 1))
    return servo.cut(recess).clean()


def build_arbotix_pcb_solid():
    """Build reference B-Rep solid of the ArbotiX-M controller board sitting on the 4 PCB standoffs."""
    pcb = cq.Workplane("XY", origin=(0, 0, 9.0)).center(31.0, 58.5).rect(62.0, 62.0).extrude(1.6).edges("|Z").fillet(2.0).val()
    chip = cq.Workplane("XY", origin=(0, 0, 10.6)).center(31.0, 58.5).rect(22.0, 22.0).extrude(4.0).val()
    hdr1 = cq.Workplane("XY", origin=(0, 0, 10.6)).center(14.0, 58.5).rect(6.0, 42.0).extrude(7.5).val()
    hdr2 = cq.Workplane("XY", origin=(0, 0, 10.6)).center(48.0, 58.5).rect(6.0, 42.0).extrude(7.5).val()
    holes = [cq.Solid.makeCylinder(1.6, 5.0, cq.Vector(x, y, 8.0), cq.Vector(0, 0, 1)) for x, y in hb.PCB_XY]
    return hb.cut_all(hb.fuse_all([pcb, chip, hdr1, hdr2]), holes)


def shape_to_trimesh(shape, tol=0.06):
    vs, fs = shape.tessellate(tol, 0.15)
    return trimesh.Trimesh(vertices=[v.toTuple() for v in vs], faces=fs, process=True)


def rot_x_mat(deg, center=(0.0, 0.0, 0.0)):
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    R = np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], dtype=float)
    T1 = np.eye(4); T1[:3, 3] = -np.array(center)
    T2 = np.eye(4); T2[:3, 3] = np.array(center)
    return T2 @ R @ T1


def rot_y_mat(deg, center=(0.0, 0.0, 0.0)):
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    R = np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], dtype=float)
    T1 = np.eye(4); T1[:3, 3] = -np.array(center)
    T2 = np.eye(4); T2[:3, 3] = np.array(center)
    return T2 @ R @ T1


def rot_z_mat(deg, center=(0.0, 0.0, 0.0)):
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    R = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
    T1 = np.eye(4); T1[:3, 3] = -np.array(center)
    T2 = np.eye(4); T2[:3, 3] = np.array(center)
    return T2 @ R @ T1


def trans_mat(dx, dy, dz):
    T = np.eye(4)
    T[:3, 3] = [dx, dy, dz]
    return T


def apply_mat_to_shape(shape, M):
    mat = cq.Matrix([
        [float(M[0, 0]), float(M[0, 1]), float(M[0, 2]), float(M[0, 3])],
        [float(M[1, 0]), float(M[1, 1]), float(M[1, 2]), float(M[1, 3])],
        [float(M[2, 0]), float(M[2, 1]), float(M[2, 2]), float(M[2, 3])],
    ])
    return shape.transformGeometry(mat)


def shrink_step(path, decimals=6):
    """Bulatkan koordinat CARTESIAN_POINT (1 nm) -> file STEP jauh lebih kecil, geometri identik secara praktis."""
    import re
    num = re.compile(r"-?\d+\.\d+(?:E[-+]?\d+)?")

    def fix_line(line):
        if "CARTESIAN_POINT" not in line:
            return line
        def r(mo):
            v = round(float(mo.group(0)), decimals)
            t = f"{v:.{decimals}f}".rstrip("0")
            return t if not t.endswith(".") else t + "0"
        return num.sub(r, line)

    txt = Path(path).read_text(encoding="utf-8", errors="replace")
    Path(path).write_text("".join(fix_line(l) for l in txt.splitlines(keepends=True)), encoding="utf-8")


def mat_to_location(M):
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetValues(float(M[0, 0]), float(M[0, 1]), float(M[0, 2]), float(M[0, 3]),
                float(M[1, 0]), float(M[1, 1]), float(M[1, 2]), float(M[1, 3]),
                float(M[2, 0]), float(M[2, 1]), float(M[2, 2]), float(M[2, 3]))
    return cq.Location(t)


def apply_mat_to_mesh(mesh, M):
    m = mesh.copy()
    m.apply_transform(M)
    return m


def zero_z_mesh(mesh):
    m = mesh.copy()
    bmin = m.bounds[0]
    cx, cy = (m.bounds[0, 0] + m.bounds[1, 0]) / 2.0, (m.bounds[0, 1] + m.bounds[1, 1]) / 2.0
    m.apply_translation([-cx, -cy, -bmin[2]])
    return m


def main():
    print("1. Loading / building all individual parts...")
    s_base_legs = hb.build_base_legs_widowx_hybrid()
    s_top_widowx = hb.build_base_turn_table_bot_widowx()
    s_pillars = hb.build_outer_pillars()
    s_servo = build_ax12a_servo_solid()
    s_pcb = build_arbotix_pcb_solid()

    s_top_orig = stl_to_cq_solid(AX_ORIG_DIR / "base_turn_table_bot.stl")
    s_spacer = stl_to_cq_solid(AX_ORIG_DIR / "base_turn_table_spacer.stl")
    s_turntable = stl_to_cq_solid(AX_ORIG_DIR / "base_turn_table.stl")
    s_f4_f3 = stl_to_cq_solid(AX_ORIG_DIR / "f4_n_f3.stl", clean_zero_area=True, sew_tol=0.05)
    s_flange = stl_to_cq_solid(AX_ORIG_DIR / "servo_hinge_flange.stl")
    s_wrist = stl_to_cq_solid(AX_ORIG_DIR / "wrist.stl")
    s_claw_base_orig = stl_to_cq_solid(AX_ORIG_DIR / "the_crawer_base.stl")
    # --- Gripper versi servo 25 kg (DS3225), lihat build_gripper_ds3225.py ---
    s_cradle = gds.build_gripper_cradle()
    s_claw_base = gds.build_gripper_base(s_claw_base_orig)
    s_horn_adapter = gds.build_horn_adapter()
    s_ds3225 = gds.build_ds3225_reference()
    s_claw_lever = stl_to_cq_solid(AX_ORIG_DIR / "the_crawer_lever.stl")
    s_claw_finger = stl_to_cq_solid(AX_ORIG_DIR / "the_crawer.stl")

    # Individual part catalog: (id_prefix, name, shape, qty_needed, description)
    part_catalog = [
        ("01_base_legs_widowx_hybrid", s_base_legs, "x1", "Base Bawah Oktagonal Lebar WidowX (190x190x80 mm)"),
        ("02_base_turn_table_bot_widowx", s_top_widowx, "x1", "Deck Atas Turntable Model Oktagonal WidowX (112x112x7 mm)"),
        ("02b_base_turn_table_bot_original", s_top_orig, "x1_opsional", "Deck Atas Turntable Kotak Asli (60x78.25x7 mm - Cadangan)"),
        ("03_base_widowx_outer_pillars", s_pillars, "x1set", "4 Tiang Luar Oktagonal WidowX (Tinggi 75 mm)"),
        ("04_base_turn_table_spacer", s_spacer, "x1", "Spacer Horn Servo Base (Ø22x2.5 mm)"),
        ("05_base_turn_table", s_turntable, "x1", "Meja Putar Base + Dudukan Servo Bahu (Ø56x20.7 mm)"),
        ("06_f4_n_f3_arm_link", s_f4_f3, "x2", "Lengan Utama Bahu-Siku & Siku-Pergelangan (Cetak 2x)"),
        ("07_servo_hinge_flange", s_flange, "x3", "Flange Engsel Belakang Servo Bahu/Siku/Wrist (Cetak 3x)"),
        ("08_wrist", s_wrist, "x1", "Bracket Pergelangan Tangan Pitch-ke-Roll (48.2x54.7x43 mm)"),
        ("09_gripper_cradle_ds3225", s_cradle, "x1", "Dudukan Servo 25kg: dibaut ke horn wrist roll, menyangga kuping servo"),
        ("10_gripper_base_ds3225", s_claw_base, "x1", "Plat Gripper + kaki ke kuping servo 25kg (modifikasi the_crawer_base)"),
        ("11_the_crawer_lever", s_claw_lever, "x2", "Tuas Penghubung Horn Gripper (Cetak 2x - Kiri & Kanan, tidak berubah)"),
        ("11b_horn_adapter_25t", s_horn_adapter, "x1", "Adapter horn disc aluminium 25T -> pin tuas R8 (pengganti horn AX-12A)"),
        ("12_the_crawer_finger", s_claw_finger, "x2", "Jari Penjepit Gripper (Cetak 2x - Kiri & Kanan)"),
        ("13_dynamixel_ax12a_reference", s_servo, "ref_5x", "Model Referensi Servo Dynamixel AX-12A (Bukan untuk dicetak)"),
        ("14_servo_ds3225_reference", s_ds3225, "ref_1x", "Model Referensi Servo 25kg DS3225 + horn disc (Bukan untuk dicetak)"),
    ]

    manifest_rows = []
    meshes_by_id = {}

    print("2. Exporting individual STEP and print-ready STL files...")
    for pid, shape, qty_tag, desc in part_catalog:
        step_file = STEP_OUT_DIR / f"{pid}.step"
        cq.exporters.export(shape, str(step_file))

        raw_mesh = shape_to_trimesh(shape, tol=0.05)
        meshes_by_id[pid] = raw_mesh

        if not pid.startswith(("13_", "14_")):
            # Orientasi cetak: plat gripper DS3225 dibalik (muka atas rata di bed, kaki menghadap ke atas)
            print_mesh = apply_mat_to_mesh(raw_mesh, rot_x_mat(180.0)) if pid.startswith("10_gripper_base") else raw_mesh
            bed_mesh = zero_z_mesh(print_mesh)
            stl_file = STL_OUT_DIR / f"{pid}_{qty_tag}.stl"
            bed_mesh.export(str(stl_file))
            ext = [round(float(x), 2) for x in bed_mesh.extents]
            manifest_rows.append({
                "id": pid,
                "stl_file": stl_file.name,
                "step_file": step_file.name,
                "qty": qty_tag,
                "size_mm": f"{ext[0]} x {ext[1]} x {ext[2]}",
                "watertight": bool(bed_mesh.is_watertight),
                "description": desc,
            })
            print(f"   Exported {stl_file.name:48s} | {ext[0]:6.2f} x {ext[1]:6.2f} x {ext[2]:6.2f} mm")

    print("3. Assembling complete 3D Robot Arm in articulated preview pose...")
    # World coordinate frame:
    # Base bottom at Z = 0.0, Turntable axis at (X=31.0, Y=65.0)
    # Shoulder pitch axis at (X=31.0, Y=65.0, Z=129.03), axis parallel to X

    # Joint angles for a natural, stable 3D preview pose (similar to IMG_2082 / IMG_2091):
    # In link-local normalization below, +Y_link is along the link.
    # Starting from horizontal +Y, rotating by +105 deg around X points the upper arm upward and slightly back (-15 deg from vertical +Z).
    # Then forearm at +35 deg from horizontal (+Y and +Z), and wrist at -15 deg from horizontal (pointing forward +Y and slightly down).
    ang_shoulder = 100.0   # deg from +Y in YZ plane (100 deg = 10 deg back from vertical +Z)
    ang_elbow = 25.0       # deg from +Y in YZ plane (25 deg = 65 deg forward from upper arm)
    ang_wrist = -20.0      # deg from +Y in YZ plane (-20 deg = angled slightly down toward object)

    # Normalization transforms to local joint frames centered at (31.0, 0.0, 0.0):
    # (a) f4_n_f3 link: in STL, hinge axis is at (Y=65.33, Z=39.31), X_center=6.22, link extends along +Y (length L=92.06 mm)
    T_f4_norm = trans_mat(31.0 - 6.22, -65.33, -39.31)
    L_link = 92.06

    # (b) AX-12A servo at a horizontal X-hinge (horn on -X side at X=31-16=15, body X in [15, 47], bottom at -Y_link):
    #     In build_ax12a_servo_solid(), horn is +Z_s, top is +Y_s, bottom is -Y_s (-38.5..+11.5), width is X_s (-16..+16).
    #     We want:
    #       +Z_s (horn) -> -X_world
    #       +Y_s (top/bottom length) -> +Y_link (so bottom -38.5 is at -38.5 along Y_link!)
    #       +X_s -> +Z_link
    #     That is a -90 deg rotation around Y_s, then shifted to X = 31.0 - 16.0 = 15.0!
    T_servo_on_link = trans_mat(15.0, 0.0, 0.0) @ rot_y_mat(-90.0)

    # (c) servo_hinge_flange at +X side of a horizontal X-hinge:
    #     In STL, flange is X in [0, 6.5] (1.5 mm flange at X=0..1.5, 5 mm boss at X=1.5..6.5).
    #     Flip X (rotate 180 around Z) so boss points in -X into the ear at X=47..50, flange outside at X=50..51.5!
    T_flange_on_joint = trans_mat(53.5, 0.0, 0.0) @ rot_z_mat(180.0)

    # Shoulder joint world position:
    S_pt = np.array([31.0, 65.0, 129.03])
    T_shoulder_world = trans_mat(0.0, S_pt[1], S_pt[2]) @ rot_x_mat(ang_shoulder, center=(31.0, 0.0, 0.0))

    # Elbow joint world position:
    E_pt = (T_shoulder_world @ np.array([31.0, L_link, 0.0, 1.0]))[:3]
    T_elbow_world = trans_mat(0.0, E_pt[1], E_pt[2]) @ rot_x_mat(ang_elbow, center=(31.0, 0.0, 0.0))

    # Wrist Pitch joint world position:
    W_pt = (T_elbow_world @ np.array([31.0, L_link, 0.0, 1.0]))[:3]

    # In wrist.stl:
    # Hinge axis is at (Y=44.78, Z=136.94), X_center=54.65.
    # Its top plate (where Wrist Roll Servo 5 mounts) is at Z_stl = 165.64 (+28.70 mm along +Z_stl from hinge).
    # So if we normalize wrist.stl by translating (-23.65, -44.78, -136.94), the wrist assembly extends along +Z_local!
    # Rotating by -90 deg around X maps +Z_local -> +Y_link (along the arm extension direction)!
    T_wrist_norm = rot_x_mat(-90.0, center=(31.0, 0.0, 0.0)) @ trans_mat(31.0 - 54.65, -44.78, -136.94)
    T_wrist_world = trans_mat(0.0, W_pt[1], W_pt[2]) @ rot_x_mat(ang_wrist, center=(31.0, 0.0, 0.0))

    # Inside the unrotated normalized wrist frame (before T_wrist_norm's -90 deg X-rotation, where Wrist Roll axis is (X=31, Y=0) along +Z):
    # - wrist.stl top plate is at Z_w = +23.42 .. +28.70 mm.
    # - Servo 5 (Wrist Roll): back face at Z_w = +28.70, front face (horn base) at Z_w = +60.70, horn tip at Z_w = +65.70.
    #   In wrist.stl, the 10 mounting holes extend toward +Y_stl (Y_stl = 44.78..80.8), so the bottom of Servo 5 (-Y_s) points toward +Y_w (rotate 180 around Z_s)!
    T_servo5_in_w = trans_mat(31.0, 0.0, 60.70) @ rot_z_mat(180.0) @ trans_mat(0.0, 0.0, 0.0)

    # - wrist_rotate.stl: in STL, boss is Z_stl=155.36..160.36, plate is Z_stl=160.36..165.64.
    #   Shifted by Z = +60.70 - 155.36 = -94.66 in Z_stl (or +42.28 relative to Z_hinge=136.94), its boss sits at Z_w = 60.70..65.70 and plate at Z_w = 65.70..70.98!
    T_wrist_rot_in_w = trans_mat(31.0 - 54.65, -44.78, -155.36 + 60.70)

    # - Servo 6 (Gripper): back face sits on top of wrist_rotate plate (Z_w = 70.98), front face (horn base) at Z_w = 102.98!
    T_servo6_in_w = trans_mat(31.0, 0.0, 102.98) @ rot_z_mat(180.0)

    # - the_crawer_base.stl: in STL, horn center is at (31.0, 65.0), bottom holes at Y=29.0 (-Y direction), Z in [0, 5.0].
    #   To match Servo 6 (rotated 180 deg in Z so bottom is +Y_w), rotate crawer_base + levers + claws by 180 deg around Z about (31.0, 65.0),
    #   then translate (0, -65.0, +102.98)!
    # Versi DS3225: bawah cradle menempel muka horn wrist roll (Z_w = 65.70);
    # bawah plat gripper berada WRIST_HORN_TO_PLATE di atasnya.
    Z_PLATE_W = 65.70 + gds.WRIST_HORN_TO_PLATE
    T_gripper_in_w = trans_mat(0.0, -65.0, Z_PLATE_W) @ rot_z_mat(180.0, center=(31.0, 65.0, 0.0))

    # Left and Right Claws & Levers in the_crawer_base frame (where horn is at (31.0, 65.0), Z in [0, 5]):
    # From .pk2 File 4: Left claw is R_y(-90) + translate(27.621, -33.0, 86.5), then opened slightly (-4 mm in X)
    T_claw_L_in_g = trans_mat(25.0, -33.0, 86.5) @ rot_y_mat(-90.0)
    # Right claw is Left claw mirrored across X = 31.0 (or rotated 180 around Z at (31.0, 65.0) — wait: in IMG_2071, both claws have their flat face toward X=31 and sloped back on the outside, which is a mirror across X=31, or let's check!)
    # Wait: in IMG_2064 and IMG_2071, one claw has the double rail on the front and one on the back -> rotated 180 deg around Z at (31.0, 65.0)!
    T_claw_R_in_g = rot_z_mat(180.0, center=(31.0, 65.0, 0.0)) @ T_claw_L_in_g

    # Levers in gripper frame (Z_stl in [11.0, 16.5] -> shifted by Z = -5.5 to Z in [5.5, 11.0], Y shifted by +12.8 to align hole with horn):
    T_lever_L_in_g = trans_mat(3.0, 10.5, -5.5)
    T_lever_R_in_g = rot_z_mat(180.0, center=(31.0, 65.0, 0.0)) @ T_lever_L_in_g

    W_map = T_wrist_world @ rot_x_mat(-90.0, center=(31.0, 0.0, 0.0))

    # Build complete list of assembled instances: (instance_name, part_id, shape, transform_matrix, rgb_color, is_printed)
    C_BASE = (0.10, 0.56, 0.44)      # Teal green for WidowX hybrid base
    C_DECK = (0.86, 0.49, 0.14)      # Orange for WidowX upper deck
    C_PILLAR = (0.36, 0.40, 0.45)    # Slate grey for outer pillars
    C_ARM = (0.14, 0.52, 0.86)       # Dynamixel blue for upper arm / wrist / gripper printed parts
    C_SERVO = (0.18, 0.20, 0.23)     # Charcoal black for AX-12A actuators
    C_PCB = (0.12, 0.32, 0.58)       # Dark blue PCB
    C_CRADLE = (0.93, 0.56, 0.16)    # Orange: cradle servo 25kg
    C_ADAPTER = (0.80, 0.22, 0.22)   # Merah: adapter horn 25T

    instances = [
        # Base & Electronics
        ("01_base_legs_widowx_hybrid", "01_base_legs_widowx_hybrid", s_base_legs, np.eye(4), C_BASE, True),
        ("02_base_turn_table_bot_widowx", "02_base_turn_table_bot_widowx", s_top_widowx, trans_mat(0, 0, 82.0), C_DECK, True),
        ("03_base_widowx_outer_pillars", "03_base_widowx_outer_pillars", s_pillars, trans_mat(0, 0, 0.0), C_PILLAR, True),
        ("ax12a_servo_1_base_yaw", "13_dynamixel_ax12a_reference", s_servo, trans_mat(31.0, 65.0, 80.0), C_SERVO, False),
        ("04_base_turn_table_spacer", "04_base_turn_table_spacer", s_spacer, trans_mat(-13.0, 5.0, 81.0), C_ARM, True),
        ("05_base_turn_table", "05_base_turn_table", s_turntable, trans_mat(31.0, 65.0, 85.5) @ rot_z_mat(90.0) @ trans_mat(-99.9, -65.0, 0.0), C_ARM, True),

        # Shoulder Joint & Upper Arm (Link 1)
        ("ax12a_servo_2_shoulder_pitch", "13_dynamixel_ax12a_reference", s_servo, trans_mat(0.0, S_pt[1], S_pt[2]) @ rot_x_mat(90.0, center=(31.0, 0.0, 0.0)) @ T_servo_on_link, C_SERVO, False),
        ("07_servo_hinge_flange_1_shoulder", "07_servo_hinge_flange", s_flange, T_shoulder_world @ T_flange_on_joint, C_ARM, True),
        ("06_f4_n_f3_link_1_upper_arm", "06_f4_n_f3_arm_link", s_f4_f3, T_shoulder_world @ T_f4_norm, C_ARM, True),

        # Elbow Joint & Forearm (Link 2)
        ("ax12a_servo_3_elbow_pitch", "13_dynamixel_ax12a_reference", s_servo, T_shoulder_world @ trans_mat(0.0, L_link, 0.0) @ T_servo_on_link, C_SERVO, False),
        ("07_servo_hinge_flange_2_elbow", "07_servo_hinge_flange", s_flange, T_elbow_world @ T_flange_on_joint, C_ARM, True),
        ("06_f4_n_f3_link_2_forearm", "06_f4_n_f3_arm_link", s_f4_f3, T_elbow_world @ T_f4_norm, C_ARM, True),

        # Wrist Pitch Joint & Wrist Bracket
        ("ax12a_servo_4_wrist_pitch", "13_dynamixel_ax12a_reference", s_servo, T_elbow_world @ trans_mat(0.0, L_link, 0.0) @ T_servo_on_link, C_SERVO, False),
        ("07_servo_hinge_flange_3_wrist", "07_servo_hinge_flange", s_flange, T_wrist_world @ T_flange_on_joint, C_ARM, True),
        ("08_wrist_bracket", "08_wrist", s_wrist, T_wrist_world @ T_wrist_norm, C_ARM, True),

        # Wrist Roll & Gripper Assembly
        ("ax12a_servo_5_wrist_roll", "13_dynamixel_ax12a_reference", s_servo, W_map @ T_servo5_in_w, C_SERVO, False),
        ("09_gripper_cradle_ds3225", "09_gripper_cradle_ds3225", s_cradle, W_map @ T_gripper_in_w, C_CRADLE, True),
        ("servo_25kg_ds3225_gripper", "14_servo_ds3225_reference", s_ds3225, W_map @ T_gripper_in_w, C_SERVO, False),
        ("10_gripper_base_ds3225", "10_gripper_base_ds3225", s_claw_base, W_map @ T_gripper_in_w, C_ARM, True),
        ("11b_horn_adapter_25t", "11b_horn_adapter_25t", s_horn_adapter, W_map @ T_gripper_in_w, C_ADAPTER, True),
        ("11_the_crawer_lever_left", "11_the_crawer_lever", s_claw_lever, W_map @ T_gripper_in_w @ T_lever_L_in_g, C_ARM, True),
        ("11_the_crawer_lever_right", "11_the_crawer_lever", s_claw_lever, W_map @ T_gripper_in_w @ T_lever_R_in_g, C_ARM, True),
        ("12_the_crawer_finger_left", "12_the_crawer_finger", s_claw_finger, W_map @ T_gripper_in_w @ T_claw_L_in_g, C_ARM, True),
        ("12_the_crawer_finger_right", "12_the_crawer_finger", s_claw_finger, W_map @ T_gripper_in_w @ T_claw_R_in_g, C_ARM, True),
    ]

    print("4. Exporting Full Assembly STEP and STL files...")
    asm_full = cq.Assembly(name="AX12A_WidowX_Hybrid_Robot_Arm_Full")
    asm_printed = cq.Assembly(name="AX12A_WidowX_Hybrid_Printed_Parts_Only")

    full_meshes = []
    printed_meshes = []
    render_items = []

    meshes_by_id["arbotix"] = shape_to_trimesh(s_pcb, tol=0.06)

    for inst_name, pid, shape, M, rgb, is_printed in instances:
        # Instance (shape yang sama + Location) -> geometri part berulang hanya ditulis sekali di STEP
        cq_col = cq.Color(*rgb)
        loc = mat_to_location(M)
        asm_full.add(shape, name=inst_name, loc=loc, color=cq_col)
        if is_printed:
            asm_printed.add(shape, name=inst_name, loc=loc, color=cq_col)

        m_inst = apply_mat_to_mesh(meshes_by_id[pid], M)
        full_meshes.append(m_inst)
        if is_printed:
            printed_meshes.append(m_inst)
        render_items.append((m_inst.triangles, rgb))

    full_step_path = STEP_OUT_DIR / "00_FULL_ROBOT_ARM_ASSEMBLY.step"
    printed_step_path = STEP_OUT_DIR / "00_FULL_ROBOT_ARM_PRINTED_PARTS_ONLY.step"
    asm_full.export(str(full_step_path))
    asm_printed.export(str(printed_step_path))
    shrink_step(full_step_path)
    shrink_step(printed_step_path)
    print(f"   Saved {full_step_path} ({full_step_path.stat().st_size / (1024*1024):.2f} MB)")
    print(f"   Saved {printed_step_path} ({printed_step_path.stat().st_size / (1024*1024):.2f} MB)")

    combined_full_stl = STL_OUT_DIR / "00_FULL_ROBOT_ARM_PREVIEW.stl"
    combined_printed_stl = STL_OUT_DIR / "00_FULL_ROBOT_ARM_PRINTED_PARTS_PREVIEW.stl"
    trimesh.util.concatenate(full_meshes).export(str(combined_full_stl))
    trimesh.util.concatenate(printed_meshes).export(str(combined_printed_stl))
    print(f"   Saved {combined_full_stl} ({combined_full_stl.stat().st_size / (1024*1024):.2f} MB)")

    print("5. Rendering 3D Assembly & Spare Parts Catalog Previews...")
    all_pts = np.vstack([m.vertices for m in full_meshes])

    def draw_scene(ax, elev, azim, title):
        all_tris, all_cols = [], []
        light = np.array([0.4, -0.5, 0.77])
        for tris, color in render_items:
            normal = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
            normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
            shade = 0.42 + 0.58 * np.abs(normal @ light)
            cols = shade[:, None] * np.array(color)[None, :]
            all_tris.append(tris)
            all_cols.append(cols)
        poly = Poly3DCollection(np.vstack(all_tris), facecolors=np.vstack(all_cols), edgecolors="none", rasterized=True)
        poly.set_zsort("average")
        ax.add_collection3d(poly)
        lo, hi = all_pts.min(axis=0), all_pts.max(axis=0)
        mid = (lo + hi) / 2.0
        span = (hi - lo).max() * 0.52
        ax.set(xlim=(mid[0] - span, mid[0] + span), ylim=(mid[1] - span, mid[1] + span), zlim=(mid[2] - span, mid[2] + span))
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev, azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=12, fontweight="bold")

    fig = plt.figure(figsize=(18, 8), facecolor="#f4f6f8")
    ax1 = fig.add_subplot(1, 3, 1, projection="3d", facecolor="#f4f6f8")
    draw_scene(ax1, elev=22, azim=-48, title="1. Perspektif Isometrik Depan")
    ax2 = fig.add_subplot(1, 3, 2, projection="3d", facecolor="#f4f6f8")
    draw_scene(ax2, elev=12, azim=0, title="2. Tampak Samping (Jangkauan & Stabilitas Base)")
    ax3 = fig.add_subplot(1, 3, 3, projection="3d", facecolor="#f4f6f8")
    draw_scene(ax3, elev=24, azim=135, title="3. Perspektif Belakang")
    fig.suptitle("Full Assembly 3D Preview — Lengan 5-DOF (5x AX-12A) + Gripper Servo 25kg DS3225 + Base Hybrid WidowX MK-II", fontsize=15, fontweight="bold", y=0.96)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.02, top=0.88, wspace=0.02)
    preview_img = STL_OUT_DIR / "PREVIEW_FULL_ROBOT_ARM.png"
    fig.savefig(preview_img, dpi=150)
    shutil.copy2(preview_img, STEP_OUT_DIR / "PREVIEW_FULL_ROBOT_ARM.png")
    plt.close(fig)

    # Render 13-part spare-part catalog
    printable_list = [p for p in part_catalog if not p[0].startswith(("13_", "14_"))]
    fig2 = plt.figure(figsize=(18, 11), facecolor="white")
    light = np.array([0.4, -0.5, 0.77])
    for idx, (pid, _, qty_tag, desc) in enumerate(printable_list, 1):
        ax = fig2.add_subplot(3, 5, idx, projection="3d", facecolor="white")
        m = zero_z_mesh(meshes_by_id[pid])
        tris = m.triangles
        normal = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
        shade = 0.42 + 0.58 * np.abs(normal @ light)
        c_base = C_BASE if "01_" in pid else (C_DECK if "02_" in pid else (C_PILLAR if "03_" in pid else C_ARM))
        cols = shade[:, None] * np.array(c_base)[None, :]
        poly = Poly3DCollection(tris, facecolors=cols, edgecolors="none", rasterized=True)
        poly.set_zsort("average")
        ax.add_collection3d(poly)
        lo, hi = m.vertices.min(axis=0), m.vertices.max(axis=0)
        mid = (lo + hi) / 2.0
        span = (hi - lo).max() * 0.58
        ax.set(xlim=(mid[0] - span, mid[0] + span), ylim=(mid[1] - span, mid[1] + span), zlim=(mid[2] - span, mid[2] + span))
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(28, -50)
        ax.set_axis_off()
        ext = m.extents
        ax.set_title(f"{pid}\n({qty_tag}) | {ext[0]:.0f}x{ext[1]:.0f}x{ext[2]:.0f} mm", fontsize=8.5, fontweight="bold")

    fig2.suptitle(f"Katalog Lengkap {len(printable_list)} File STL Siap Cetak (Versi Gripper Servo 25kg DS3225)", fontsize=15, fontweight="bold", y=0.97)
    fig2.subplots_adjust(left=0.01, right=0.99, bottom=0.02, top=0.90, wspace=0.05, hspace=0.18)
    cat_img = STL_OUT_DIR / "KATALOG_SEMUA_PART_STL.png"
    fig2.savefig(cat_img, dpi=150)
    shutil.copy2(cat_img, STEP_OUT_DIR / "KATALOG_SEMUA_PART_STL.png")
    plt.close(fig2)

    (STL_OUT_DIR / "manifest.json").write_text(json.dumps(manifest_rows, indent=2), encoding="utf-8")
    print("Done! All STEP and STL files generated successfully.")


if __name__ == "__main__":
    main()
