"""Preliminary point-mass screening, not a rated payload or CAD validation."""
import json
from math import hypot
from pathlib import Path

G = 9.81
AX_MASS = 0.0546
MG_MASS = 0.0134


def evaluate(name, upper, forearm, wrist, gripper):
    # Straight horizontal chain; approximate each distal servo COM at its joint.
    # Base and shoulder servos are assumed centered at the base/shoulder.
    elbow_x = upper
    wrist_pitch_x = upper + forearm
    wrist_roll_x = wrist_pitch_x + wrist
    gripper_x = wrist_roll_x + gripper
    masses = [
        ("elbow_AX12A", AX_MASS, elbow_x),
        ("wrist_pitch_AX12A", AX_MASS, wrist_pitch_x),
        ("wrist_roll_AX12A", AX_MASS, wrist_roll_x),
        ("gripper_MG90S", MG_MASS, gripper_x),
    ]
    return {
        "scenario": name,
        "shoulder_to_gripper_servo_m": gripper_x,
        "distal_servo_mass_kg": sum(m for _, m, _ in masses),
        "shoulder_torque_servos_only_Nm": sum(m * G * x for _, m, x in masses),
        "elbow_torque_servos_only_Nm": sum(m * G * max(0, x-elbow_x) for _, m, x in masses),
        "point_masses": [{"name": n, "mass_kg": m, "shoulder_horizontal_distance_m": x} for n, m, x in masses],
    }


def main():
    result = {
        "assumptions": [
            "Static straight horizontal chain; motor COM approximated at joint axis.",
            "No printed frame, horns, bearings, cables, fasteners, finger mass or payload.",
            "No acceleration, friction, joint COM offsets or counterbalance.",
            "Reference lengths from Interbotix Xacro; not measured from user STL.",
            "Compact dimensions are a study scenario, not a confirmed fitting assembly.",
        ],
        "AX12A_screening_torque_Nm": 1.5 / 5,
        "screening_note": "One fifth of published stall at 12 V; not a continuous torque guarantee.",
        "sources": [
            "https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/",
            "https://towerpro.com.tw/product/mg90s-3/",
            "../reference_widowx/widowx_arm_description/urdf/widowx.urdf.xacro",
        ],
        "scenarios": [
            evaluate("WidowX-length chain with AX12A substituted", hypot(0.04825, 0.14203), 0.14203, 0.0715, 0.043),
            evaluate("Compact study 60+60+45+35 mm", 0.06, 0.06, 0.045, 0.035),
        ],
    }
    dest = Path(__file__).with_name("empty_arm_estimate.json")
    dest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for row in result["scenarios"]:
        print(f"{row['scenario']}: shoulder={row['shoulder_torque_servos_only_Nm']:.3f} Nm; elbow={row['elbow_torque_servos_only_Nm']:.3f} Nm")


if __name__ == "__main__":
    main()
