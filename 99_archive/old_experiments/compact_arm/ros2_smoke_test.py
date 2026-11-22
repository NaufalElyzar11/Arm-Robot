"""Run under sourced ROS2 Jazzy Python. Own processes only, isolated DDS domain."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
os.environ["ROS_DOMAIN_ID"] = "173"
os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
os.environ["ROS_LOG_DIR"] = str(OUT / "ros_logs")

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_msgs.msg import TFMessage


def main():
    joint_messages, tf_messages = [], []
    log_path = OUT / "ros2_smoke.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(["ros2", "launch", "ax12_compact_description", "display.launch.py", "demo:=true", "rviz:=false"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        rclpy.init()
        node = Node("compact_arm_verifier")
        subscriptions = [node.create_subscription(JointState, "/joint_states", joint_messages.append, 10),
                         node.create_subscription(TFMessage, "/tf", tf_messages.append, 10)]
        try:
            deadline = time.monotonic()+12
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=.2)
                if process.poll() is not None:
                    raise RuntimeError("ROS launch exited; inspect ros2_smoke.log")
            assert len(joint_messages) > 30
            assert len(tf_messages) > 30
            names = ["base_yaw", "shoulder_pitch", "elbow_pitch", "wrist_pitch", "wrist_roll", "gripper"]
            assert joint_messages[-1].name == names
            movement = [max(m.position[i] for m in joint_messages)-min(m.position[i] for m in joint_messages) for i in range(6)]
            assert all(x > .01 for x in movement)
            assert all(math.isfinite(x) for m in joint_messages for x in m.position)
            children = sorted({t.child_frame_id for m in tf_messages for t in m.transforms})
            assert set(children) == {"yaw_link", "upper_link", "forearm_link", "wrist_link", "hand_link", "finger_link"}
            result = {"ros_distro": "jazzy", "platform": "WSL Ubuntu-24.04", "joint_state_messages": len(joint_messages),
                      "tf_messages": len(tf_messages), "all_six_joints_move": True, "observed_joint_excursions_rad": movement,
                      "tf_children": children, "hardware_commands_sent": False, "passed": True}
            (OUT / "ros2_validation.json").write_text(json.dumps(result, indent=2))
            print(json.dumps(result, indent=2))
        finally:
            node.destroy_node()
            rclpy.shutdown()
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()
