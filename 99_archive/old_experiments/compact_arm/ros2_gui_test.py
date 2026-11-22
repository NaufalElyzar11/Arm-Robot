"""Check slider startup without opening windows; no hardware access."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parent
os.environ.update(ROS_DOMAIN_ID="174", ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST", QT_QPA_PLATFORM="offscreen", ROS_LOG_DIR=str(ROOT / "output" / "ros_logs_gui"))
import rclpy
from sensor_msgs.msg import JointState


def main():
    messages = []
    with (ROOT / "output" / "ros2_gui.log").open("w") as log:
        process = subprocess.Popen(["ros2", "launch", "ax12_compact_description", "display.launch.py", "rviz:=false"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        rclpy.init()
        node = rclpy.create_node("slider_startup_verifier")
        sub = node.create_subscription(JointState, "joint_states", messages.append, 10)
        try:
            end = time.monotonic()+10
            while time.monotonic()<end:
                rclpy.spin_once(node, timeout_sec=.2)
            assert process.poll() is None
            assert len(messages)>10
            assert len(messages[-1].name)==6
            result = {"slider_started_offscreen": True, "joint_state_messages": len(messages), "joint_names": messages[-1].name,
                      "rviz_visual_check": False, "hardware_commands_sent": False}
            (ROOT / "output" / "ros2_gui_validation.json").write_text(json.dumps(result, indent=2))
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
