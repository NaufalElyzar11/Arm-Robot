#!/usr/bin/env python3
"""Kinematic visualization ONLY; no actuator commands or hardware connection."""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class DemoJointStates(Node):
    def __init__(self):
        super().__init__("compact_arm_demo")
        self.publisher = self.create_publisher(JointState, "joint_states", 10)
        self.start_time = self.get_clock().now()
        self.create_timer(1.0 / 30.0, self.publish)

    def publish(self):
        seconds = (self.get_clock().now() - self.start_time).nanoseconds * 1e-9
        phase = seconds * 0.35
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ["base_yaw", "shoulder_pitch", "elbow_pitch", "wrist_pitch", "wrist_roll", "gripper"]
        msg.position = [0.5*math.sin(phase), 0.3*math.sin(phase), -0.6*math.sin(phase),
                        0.3*math.sin(phase), 0.6*math.sin(phase), 0.35*(1-math.cos(phase))]
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = DemoJointStates()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
