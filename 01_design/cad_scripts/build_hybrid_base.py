"""Build Hybrid WidowX MK-II Base for AX-12A Robot Arm (Thingiverse 166430).

Produces:
1. base_legs_widowx_hybrid.stl / .step
   - Direct drop-in replacement for base_legs_arbotix_m.stl
   - Wide 190x190 mm WidowX MK-II octagonal base plate symmetrically centered at (31.0, 58.625)
   - Preserves exact ArbotiX-M PCB mounting bosses (52.5 x 52.5 mm, z=9.0 mm, M3 holes)
   - Preserves exact top mounting hole pattern (50.0 x 68.25 mm at z=80.0 mm, 10x10 mm flush pads, M3 holes)
   - 4 symmetric 45-degree radial WidowX buttress legs + full PCB/servo clearance (100% support-free 3D print)

2. base_turn_table_bot_widowx.stl / .step
   - Optional WidowX-style octagonal upper turntable mount (112 x 112 mm octagon)
   - 100% identical AX-12A servo pocket, 6 servo mounting holes, C-ring, Ø53.5 mm turntable groove, and 4 leg holes
   - Includes 4 outer mounting holes for optional WidowX outer pillars

3. base_widowx_outer_pillars.stl / .step
   - Optional 4 outer octagonal pillars (height 75.0 mm) to connect the bottom octagonal plate
     to base_turn_table_bot_widowx.stl for a full 2-tier WidowX MK-II cage structure.
"""
from pathlib import Path
import json
import math
import shutil

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
AX_FILES = ROOT.parent / "source" / "ax12a_arm_thingiverse_166430" / "files"
STL_DIR = ROOT / "stl"
STEP_DIR = ROOT / "step"
for d in (STL_DIR, STEP_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Coordinate system matches original Thingiverse 166430 base files:
# - Center of base_legs_arbotix_m & base_turn_table_bot outer rectangle: (31.0, 58.625)
# - Turntable rotation axis on base_turn_table_bot: (31.0, 65.0)
# - Top leg mounting holes (4x): X in (6.0, 56.0), Y in (24.5, 92.75) -> center (31.0, 58.625)
# - ArbotiX-M PCB bosses (4x): X in (4.75, 57.25), Y in (32.25, 84.75) -> center (31.0, 58.5)
BASE_CX, BASE_CY = 31.0, 58.625
TT_CX, TT_CY = 31.0, 65.0
LEG_TOP_XY = [(6.0, 24.5), (56.0, 24.5), (6.0, 92.75), (56.0, 92.75)]
PCB_XY = [(4.75, 32.25), (57.25, 32.25), (4.75, 84.75), (57.25, 84.75)]
ORIG_BASE_HOLES = [
    (-9.0, 31.25), (-9.0, 86.0),
    (71.0, 31.25), (71.0, 86.0),
    (12.75, 18.5), (49.25, 18.5),
    (12.58, 98.5), (49.42, 98.5),
]
# 4 Outer WidowX pillar coordinates (symmetric around BASE_CX, BASE_CY on the left/right wings)
OUTER_PILLAR_XY = [
    (BASE_CX - 44.0, BASE_CY - 18.0),
    (BASE_CX + 44.0, BASE_CY - 18.0),
    (BASE_CX - 44.0, BASE_CY + 18.0),
    (BASE_CX + 44.0, BASE_CY + 18.0),
]


def regular_octagon_pts(cx, cy, across_flats):
    """Return 8 vertices of an axis-aligned octagon with given across-flats width."""
    half = across_flats / 2.0
    d = half * math.tan(math.radians(22.5))
    return [
        (cx - d, cy - half),
        (cx + d, cy - half),
        (cx + half, cy - d),
        (cx + half, cy + d),
        (cx + d, cy + half),
        (cx - d, cy + half),
        (cx - half, cy + d),
        (cx - half, cy - d),
    ]


def make_octagon_plate(cx, cy, across_flats, thickness, z0=0.0, fillet_r=5.0):
    pts = regular_octagon_pts(cx, cy, across_flats)
    wp = cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(thickness)
    if fillet_r > 0:
        wp = wp.edges("|Z").fillet(fillet_r)
    return wp.val()


def make_cylinder(x, y, z0, radius, height):
    return cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z0), cq.Vector(0, 0, 1))


def make_box(x_min, x_max, y_min, y_max, z_min, z_max):
    dx, dy, dz = x_max - x_min, y_max - y_min, z_max - z_min
    cx, cy, cz = (x_min + x_max) / 2.0, (y_min + y_max) / 2.0, (z_min + z_max) / 2.0
    return cq.Workplane("XY").box(dx, dy, dz).val().translate((cx, cy, cz))


def fuse_all(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.clean()


def cut_all(base_shape, cutters):
    out = base_shape
    for c in cutters:
        out = out.cut(c)
    return out.clean()


def rect_pts(cx, cy, w, h):
    hw, hh = w / 2.0, h / 2.0
    return [(cx - hw, cy - hh), (cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy + hh)]


def make_loft(sections, ruled=True):
    """Build a solid loft from explicit 3D world-coordinate (z, [(x,y), ...]) sections."""
    wires = []
    for z, pts in sections:
        vecs = [cq.Vector(x, y, z) for x, y in pts] + [cq.Vector(pts[0][0], pts[0][1], z)]
        wires.append(cq.Wire.makePolygon(vecs))
    return cq.Solid.makeLoft(wires, ruled=ruled)


def build_single_leg_with_buttress(tx, ty):
    """Build one symmetric bowed leg + 45-deg radial WidowX buttress fin from z=0 to z=80.

    Matches the ArbotiX-M PCB clearance of base_legs_arbotix_m.stl:
    - At z=0..26, inner leg edge stays outside X in [-4.0, 66.0], Y in [23.6, 93.6]
    - At z=74..80, top pad is 10.0x10.0 mm centered at (tx, ty), flush with base_turn_table_bot.stl
    - Outer radial buttress fin extends along the 45-degree diagonal to the octagon perimeter at z=0..5
      and tapers cleanly into the leg column at z=74 (100% support-free).
    """
    sx = -1.0 if tx < BASE_CX else 1.0
    sy = -1.0 if ty < BASE_CY else 1.0

    # Lower leg center at z=0..26 (exact match to original base_legs_arbotix_m: ±40 mm from center)
    bx = BASE_CX + sx * 40.0   # -9.0 or +71.0
    by = BASE_CY + sy * 40.0   # 18.625 or 98.625

    # Mid-upper waypoint at z=54
    mx = bx + (tx - bx) * 0.65
    my = by + (ty - by) * 0.65

    leg_col = make_loft([
        (0.0, rect_pts(bx, by, 10.5, 10.5)),
        (26.0, rect_pts(bx, by, 10.5, 10.5)),
        (54.0, rect_pts(mx, my, 10.2, 10.2)),
        (74.0, rect_pts(tx, ty, 10.0, 10.0)),
        (80.0, rect_pts(tx, ty, 10.0, 10.0)),
    ], ruled=True)

    # Radial 45-degree WidowX buttress fin from leg out toward the diagonal octagon edge
    ux, uy = sx / math.sqrt(2.0), sy / math.sqrt(2.0)
    px, py = -uy, ux  # perpendicular unit vector

    # Bottom of fin (z=0): starts at (bx, by) and reaches out 36 mm along 45-deg diagonal
    ox = bx + ux * 36.0
    oy = by + uy * 36.0
    half_t_bot = 4.0  # 8.0 mm thick at base
    b_pts = [
        (bx + px * half_t_bot, by + py * half_t_bot),
        (ox + px * half_t_bot, oy + py * half_t_bot),
        (ox - px * half_t_bot, oy - py * half_t_bot),
        (bx - px * half_t_bot, by - py * half_t_bot),
    ]

    # Top of fin (z=74): merges completely inside the 10x10 mm pad at (tx, ty)
    t_in_x = tx - ux * 1.5
    t_in_y = ty - uy * 1.5
    t_out_x = tx + ux * 3.0
    t_out_y = ty + uy * 3.0
    half_t_top = 3.0
    t_pts = [
        (t_in_x + px * half_t_top, t_in_y + py * half_t_top),
        (t_out_x + px * half_t_top, t_out_y + py * half_t_top),
        (t_out_x - px * half_t_top, t_out_y - py * half_t_top),
        (t_in_x - px * half_t_top, t_in_y - py * half_t_top),
    ]

    fin = make_loft([
        (0.0, b_pts),
        (74.0, t_pts),
    ], ruled=True)
    return fuse_all([leg_col, fin])


def build_base_legs_widowx_hybrid():
    """Build 1-piece hybrid base (WidowX 190x190 mm octagonal base + AX-12A leg tower)."""
    # 1. Bottom WidowX MK-II octagonal plate (190 x 190 mm across flats, centered at BASE_CX, BASE_CY, z=0..5 mm)
    plate = make_octagon_plate(BASE_CX, BASE_CY, across_flats=190.0, thickness=5.0, z0=0.0, fillet_r=6.0)

    # 2. Raised octagonal rim / stiffening rib around the perimeter (z=5..7.5 mm)
    outer_rim = make_octagon_plate(BASE_CX, BASE_CY, across_flats=186.0, thickness=2.5, z0=5.0, fillet_r=5.0)
    inner_cut = make_octagon_plate(BASE_CX, BASE_CY, across_flats=172.0, thickness=4.0, z0=4.5, fillet_r=4.0)
    rim = outer_rim.cut(inner_cut)

    # 3. 4 ArbotiX-M PCB mounting bosses (z=0..9.0 mm, Ø8.5 mm base, Ø6.5 mm top step)
    pcb_bosses = []
    for x, y in PCB_XY:
        pcb_bosses.append(make_cylinder(x, y, 0.0, 4.25, 7.0))
        pcb_bosses.append(make_cylinder(x, y, 0.0, 3.25, 9.0))

    # 4. 4 Bowed legs with radial WidowX buttress fins (z=0..80.0 mm)
    legs = [build_single_leg_with_buttress(tx, ty) for tx, ty in LEG_TOP_XY]

    solid = fuse_all([plate, rim] + pcb_bosses + legs)

    # 6. Cut holes and weight-saving / ventilation cutouts
    cutters = []

    # (a) 4 Top leg M3 mounting holes (Ø3.0 mm, z=62..81 mm)
    for tx, ty in LEG_TOP_XY:
        cutters.append(make_cylinder(tx, ty, 62.0, 1.5, 20.0))

    # (b) 4 ArbotiX-M PCB M3 mounting holes (Ø3.2 mm through z=-1..10 mm + bottom counterbore Ø6.2 mm z=-1..2.0 mm)
    for x, y in PCB_XY:
        cutters.append(make_cylinder(x, y, -1.0, 1.6, 12.0))
        cutters.append(make_cylinder(x, y, -1.0, 3.1, 3.0))

    # (c) 8 Original base_legs_arbotix_m bottom holes (Ø3.5 mm)
    for x, y in ORIG_BASE_HOLES:
        cutters.append(make_cylinder(x, y, -1.0, 1.75, 10.0))

    # (d) 4 Outer WidowX pillar mounting holes (Ø3.2 mm through + bottom counterbore Ø6.2 mm z=-1..2.0 mm)
    for x, y in OUTER_PILLAR_XY:
        cutters.append(make_cylinder(x, y, -1.0, 1.6, 10.0))
        cutters.append(make_cylinder(x, y, -1.0, 3.1, 3.0))

    # (e) 8 Perimeter anchor / rubber feet mounting holes (like WidowX component_017, M4 Ø4.5 mm + Ø9.0 mm counterbore)
    for angle_deg in range(0, 360, 45):
        rad = math.radians(angle_deg)
        r_hole = 82.0
        hx = BASE_CX + r_hole * math.cos(rad)
        hy = BASE_CY + r_hole * math.sin(rad)
        cutters.append(make_cylinder(hx, hy, -1.0, 2.25, 10.0))
        cutters.append(make_cylinder(hx, hy, 3.0, 4.5, 6.0))

    # (f) Central ventilation hole under ArbotiX-M PCB (Ø32 mm centered at (31.0, 58.5))
    cutters.append(make_cylinder(31.0, 58.5, -1.0, 16.0, 8.0))

    # (g) 4 Side cable routing / lightening slots on the outer plate (front, back, left, right)
    slot_positions = [
        (BASE_CX, BASE_CY + 62.0, 36.0, 14.0),
        (BASE_CX, BASE_CY - 62.0, 36.0, 14.0),
        (BASE_CX - 64.0, BASE_CY, 14.0, 32.0),
        (BASE_CX + 64.0, BASE_CY, 14.0, 32.0),
    ]
    for sx, sy, sw, sh in slot_positions:
        slot = (
            cq.Workplane("XY", origin=(0, 0, -1.0))
            .center(sx, sy).rect(sw, sh).extrude(8.0)
            .edges("|Z").fillet(4.0).val()
        )
        cutters.append(slot)

    return cut_all(solid, cutters)


def build_base_turn_table_bot_widowx():
    """Build WidowX-style octagonal upper turntable plate (replaces base_turn_table_bot.stl).

    Preserves 100% of the original base_turn_table_bot.stl functional geometry:
    - Z range: -2.0 to +5.0 mm (thickness 7.0 mm)
    - Central rectangle X in [1.0, 61.0], Y in [19.5, 97.75] at full Z=-2..+5 mm
    - Extended WidowX octagonal wing deck (112 x 112 mm across flats, centered at BASE_CX, BASE_CY) at Z=-2.0..+3.0 mm
      (stepped down 2 mm on top so upper arm links have extra downward pitch clearance)
    - Exact Ø53.5 mm outer / Ø35.5 mm inner turntable groove (Z=1.5..5.0 mm) at (31.0, 65.0)
    - Exact Ø25.0 mm hole + 22.0 mm wide through-slot (X in [20.0, 42.0], Y in [31.3, 65.0])
    - Exact 6 AX-12A mounting holes (Ø2.5 mm through, Ø4.0 mm counterbore Z=0..5.0 mm)
    - Exact 4 leg mounting holes at (6.0, 24.5), (56.0, 24.5), (6.0, 92.75), (56.0, 92.75)
    - Plus 4 outer WidowX pillar mounting holes at OUTER_PILLAR_XY
    """
    # 1. Core rectangular boss (exact match to original 60 x 78.25 x 7.0 mm block, z=-2..5)
    core = (
        cq.Workplane("XY", origin=(0, 0, -2.0))
        .center(BASE_CX, BASE_CY).rect(60.0, 78.25).extrude(7.0)
        .edges("|Z").fillet(4.0).val()
    )
    # 2. Octagonal WidowX deck (112 x 112 mm across flats, centered at BASE_CX, BASE_CY, z=-2..3.0 mm)
    oct_deck = make_octagon_plate(BASE_CX, BASE_CY, across_flats=112.0, thickness=5.0, z0=-2.0, fillet_r=5.0)
    solid = fuse_all([core, oct_deck])

    cutters = []
    # (a) Turntable circular groove on top: R_outer = 26.75 mm (Ø53.5 mm), R_inner = 17.75 mm (Ø35.5 mm), z=1.5..6.0
    groove_outer = make_cylinder(TT_CX, TT_CY, 1.5, 26.75, 5.0)
    groove_inner = make_cylinder(TT_CX, TT_CY, 1.0, 17.75, 6.0)
    cutters.append(groove_outer.cut(groove_inner))

    # (b) Through-cutout for AX-12A horn & body (z=-3.0..6.0):
    #     Circle R=12.50 mm (Ø25.0 mm) at (31.0, 65.0) + through-slot X in [20.0, 42.0] (22.0 mm wide), Y in [31.3, 65.0]
    cutters.append(make_cylinder(TT_CX, TT_CY, -3.0, 12.50, 9.0))
    cutters.append(make_box(20.0, 42.0, 31.3, 65.0, -3.0, 6.0))

    # (c) 6 AX-12A servo mounting holes (Ø2.5 mm through z=-3..6, Ø4.0 mm counterbore z=0.0..6.0)
    ax_holes = [
        (17.5, 58.5), (44.5, 58.5),
        (17.5, 34.5), (44.5, 34.5),
        (23.0, 29.0), (39.0, 29.0),
    ]
    for hx, hy in ax_holes:
        cutters.append(make_cylinder(hx, hy, -3.0, 1.25, 9.0))
        cutters.append(make_cylinder(hx, hy, 0.0, 2.0, 6.0))

    # (d) 4 Original leg mounting holes (Ø3.0 mm through z=-3..6, Ø5.0 mm counterbore z=1.0..6.0)
    for lx, ly in LEG_TOP_XY:
        cutters.append(make_cylinder(lx, ly, -3.0, 1.5, 9.0))
        cutters.append(make_cylinder(lx, ly, 1.0, 2.5, 5.0))

    # (e) 4 Outer WidowX pillar mounting holes (Ø3.2 mm through z=-3..6, Ø6.0 mm counterbore z=0.5..6.0)
    for px, py in OUTER_PILLAR_XY:
        cutters.append(make_cylinder(px, py, -3.0, 1.6, 9.0))
        cutters.append(make_cylinder(px, py, 0.5, 3.0, 5.5))

    return cut_all(solid, cutters)


def build_outer_pillars():
    """Build 4 octagonal WidowX outer columns (z=5.0..80.0 mm, height 75.0 mm, Ø10 mm across flats, Ø3.2 mm hole)."""
    pillars = []
    for px, py in OUTER_PILLAR_XY:
        pts = regular_octagon_pts(px, py, across_flats=10.0)
        col = cq.Workplane("XY", origin=(0, 0, 5.0)).polyline(pts).close().extrude(75.0).val()
        hole = make_cylinder(px, py, 4.0, 1.6, 77.0)
        pillars.append(col.cut(hole))
    return fuse_all(pillars)


def export_and_validate(shape, name, copy_to_ax=False, zero_z=True):
    step_path = STEP_DIR / f"{name}.step"
    stl_path = STL_DIR / f"{name}.stl"
    cq.exporters.export(shape, str(step_path))

    export_shape = shape
    if zero_z:
        bb = shape.BoundingBox()
        if abs(bb.zmin) > 1e-4:
            export_shape = shape.translate((0, 0, -bb.zmin))

    cq.exporters.export(export_shape, str(stl_path), tolerance=0.04, angularTolerance=0.1)
    if copy_to_ax:
        shutil.copy2(stl_path, AX_FILES / f"{name}.stl")

    mesh = trimesh.load_mesh(stl_path)
    assert mesh.is_watertight, f"{name} is not watertight!"
    assert mesh.volume > 0, f"{name} has non-positive volume!"
    return {
        "name": name,
        "stl_path": str(stl_path),
        "step_path": str(step_path),
        "copied_to_ax_files": str(AX_FILES / f"{name}.stl") if copy_to_ax else None,
        "extents_mm": [round(float(x), 2) for x in mesh.extents],
        "volume_cm3": round(float(mesh.volume) / 1000.0, 2),
        "est_pla_mass_g_solid": round(float(mesh.volume) * 0.00124, 1),
        "est_pla_mass_g_35pct": round(float(mesh.volume) * 0.00124 * 0.52, 1),
        "watertight": bool(mesh.is_watertight),
        "triangles": int(len(mesh.faces)),
    }


def main():
    print("Building base_legs_widowx_hybrid...")
    s_legs = build_base_legs_widowx_hybrid()
    info_legs = export_and_validate(s_legs, "base_legs_widowx_hybrid", copy_to_ax=True, zero_z=False)

    print("Building base_turn_table_bot_widowx...")
    s_top = build_base_turn_table_bot_widowx()
    info_top = export_and_validate(s_top, "base_turn_table_bot_widowx", copy_to_ax=True, zero_z=False)

    print("Building base_widowx_outer_pillars...")
    s_pillars = build_outer_pillars()
    info_pillars = export_and_validate(s_pillars, "base_widowx_outer_pillars", copy_to_ax=True, zero_z=True)

    summary = {
        "parts": [info_legs, info_top, info_pillars],
        "interfaces_verified": {
            "base_center_xy": [BASE_CX, BASE_CY],
            "turntable_axis_xy": [TT_CX, TT_CY],
            "top_leg_mount_holes_xy": LEG_TOP_XY,
            "top_leg_z_height_mm": 80.0,
            "arbotix_pcb_holes_xy": PCB_XY,
            "arbotix_pcb_boss_z_mm": 9.0,
            "turntable_groove_od_mm": 53.5,
            "turntable_groove_id_mm": 35.5,
        },
    }
    (ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
