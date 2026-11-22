"""Render preview images comparing original base vs WidowX-AX12A hybrid base."""
from pathlib import Path
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).resolve().parent
AX_FILES = ROOT.parent / "source" / "ax12a_arm_thingiverse_166430" / "files"
STL_DIR = ROOT / "stl"


def draw_combined(ax, mesh_color_list):
    all_tris = []
    all_colors = []
    light = np.array([0.4, -0.5, 0.77])
    for triangles, color in mesh_color_list:
        normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
        shade = 0.42 + 0.58 * np.abs(normal @ light)
        colors = shade[:, None] * np.array(color)[None, :]
        all_tris.append(triangles)
        all_colors.append(colors)
    tris = np.vstack(all_tris)
    cols = np.vstack(all_colors)
    col = Poly3DCollection(tris, facecolors=cols, edgecolors="none", rasterized=True)
    col.set_zsort("average")
    ax.add_collection3d(col)


def setup(ax, points, elev=26, azim=-52, span_override=None):
    lo, hi = points.min(axis=0), points.max(axis=0)
    mid = (lo + hi) / 2.0
    span = span_override if span_override else (hi - lo).max() * 0.56
    ax.set(
        xlim=(mid[0] - span, mid[0] + span),
        ylim=(mid[1] - span, mid[1] + span),
        zlim=(mid[2] - span * 0.75, mid[2] + span * 0.75),
    )
    ax.set_box_aspect((1, 1, 0.75))
    ax.view_init(elev, azim)
    ax.set_axis_off()


def main():
    m_old_legs = trimesh.load_mesh(AX_FILES / "base_legs_arbotix_m.stl")
    m_old_bot = trimesh.load_mesh(AX_FILES / "base_turn_table_bot.stl")
    m_tt = trimesh.load_mesh(AX_FILES / "base_turn_table.stl")

    m_new_legs = trimesh.load_mesh(STL_DIR / "base_legs_widowx_hybrid.stl")
    m_new_bot = trimesh.load_mesh(STL_DIR / "base_turn_table_bot_widowx.stl")
    m_pillars = trimesh.load_mesh(STL_DIR / "base_widowx_outer_pillars.stl")

    # Align turntable to (31.0, 65.0) at Z=86.0
    tt_shift = np.array([31.0 - 99.9, 65.0 - 65.0, 86.0])
    v_tt = m_tt.vertices + tt_shift
    f_tt = v_tt[m_tt.faces]

    v_old_bot = m_old_bot.vertices + np.array([0.0, 0.0, 82.0])
    f_old_bot = v_old_bot[m_old_bot.faces]

    v_new_bot = m_new_bot.vertices + np.array([0.0, 0.0, 82.0])
    f_new_bot = v_new_bot[m_new_bot.faces]

    v_pillars = m_pillars.vertices + np.array([0.0, 0.0, 5.0])
    f_pillars = v_pillars[m_pillars.faces]

    fig = plt.figure(figsize=(16, 10), facecolor="#f4f6f8")

    # Panel 1: Old base assembly (same scale as new)
    ax1 = fig.add_subplot(2, 2, 1, projection="3d", facecolor="#f4f6f8")
    draw_combined(ax1, [
        (m_old_legs.triangles, (0.12, 0.48, 0.82)),
        (f_old_bot, (0.18, 0.62, 0.90)),
        (f_tt, (0.28, 0.72, 0.95)),
    ])
    setup(ax1, np.vstack([m_new_legs.vertices, v_tt]), elev=26, azim=-50, span_override=102)
    ax1.set_title("1. Base Asli (90 x 90 mm) — Sempit & Rawan Jatuh", fontsize=12, fontweight="bold")

    # Panel 2: Hybrid Base + Original base_turn_table_bot.stl
    ax2 = fig.add_subplot(2, 2, 2, projection="3d", facecolor="#f4f6f8")
    draw_combined(ax2, [
        (m_new_legs.triangles, (0.10, 0.56, 0.44)),
        (f_old_bot, (0.18, 0.62, 0.90)),
        (f_tt, (0.28, 0.72, 0.95)),
    ])
    setup(ax2, np.vstack([m_new_legs.vertices, v_tt]), elev=26, azim=-50, span_override=102)
    ax2.set_title("2. Base Hybrid WidowX (190 x 190 mm) + Turntable Bot Asli", fontsize=12, fontweight="bold")

    # Panel 3: Hybrid Base + WidowX Top Deck + Outer Pillars
    ax3 = fig.add_subplot(2, 2, 3, projection="3d", facecolor="#f4f6f8")
    draw_combined(ax3, [
        (m_new_legs.triangles, (0.10, 0.56, 0.44)),
        (f_pillars, (0.35, 0.38, 0.42)),
        (f_new_bot, (0.85, 0.48, 0.14)),
        (f_tt, (0.28, 0.72, 0.95)),
    ])
    setup(ax3, np.vstack([m_new_legs.vertices, v_tt]), elev=26, azim=-50, span_override=102)
    ax3.set_title("3. Full WidowX 2-Deck Hybrid (190x190 + Deck Atas 112x112 + Pilar)", fontsize=12, fontweight="bold")

    # Panel 4: Individual new part close-up (base_turn_table_bot_widowx)
    ax4 = fig.add_subplot(2, 2, 4, projection="3d", facecolor="#f4f6f8")
    draw_combined(ax4, [(m_new_bot.triangles, (0.85, 0.48, 0.14))])
    setup(ax4, m_new_bot.vertices, elev=42, azim=-45)
    ax4.set_title("4. Detail base_turn_table_bot_widowx.stl (Oktagonal 112x112 mm)", fontsize=12, fontweight="bold")

    fig.suptitle("Perbandingan Base Asli AX-12A vs Base Hybrid Model WidowX MK-II", fontsize=16, fontweight="bold", y=0.97)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.91, wspace=0.05, hspace=0.12)
    out_img = ROOT / "preview_comparison.png"
    fig.savefig(out_img, dpi=150)
    plt.close(fig)
    print(f"Saved {out_img}")


if __name__ == "__main__":
    main()
