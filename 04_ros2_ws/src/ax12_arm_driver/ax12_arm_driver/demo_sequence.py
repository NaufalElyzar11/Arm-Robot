"""demo_sequence — memutar daftar pose berulang (mis. untuk mode idle pameran).

Pose dibaca dari parameter (lihat ax12_arm_bringup/config/demo_poses.yaml):
  sequence: [home, kiri, ...]          urutan nama pose
  poses.<nama>: [6 nilai rad]          urutan sama dengan joint_names
  hold_s: detik menunggu di tiap pose
Saat mulai, node menyalakan torque lewat service driver (bila enable_torque: true).
"""
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool

from .driver_node import DEFAULT_JOINTS


class DemoSequence(Node):
    def __init__(self):
        super().__init__('demo_sequence', automatically_declare_parameters_from_overrides=True)
        p = self.get_parameter_or
        self.names = list(p('joint_names', Parameter('joint_names', value=DEFAULT_JOINTS)).value)
        self.sequence = list(p('sequence', Parameter('sequence', value=['home'])).value)
        self.hold_s = float(p('hold_s', Parameter('hold_s', value=3.0)).value)
        driver = p('driver_name', Parameter('driver_name', value='/ax12_driver')).value
        enable = p('enable_torque', Parameter('enable_torque', value=True)).value

        self.poses = {}
        for name in self.sequence:
            if self.has_parameter(f'poses.{name}'):
                vals = list(self.get_parameter(f'poses.{name}').value)
                if len(vals) == len(self.names):
                    self.poses[name] = [float(v) for v in vals]
                    continue
            self.get_logger().error(f'Pose "{name}" tidak ada / panjangnya bukan {len(self.names)}; dilewati')
        self.sequence = [s for s in self.sequence if s in self.poses]
        if not self.sequence:
            raise RuntimeError('Tidak ada pose valid')

        self.pub = self.create_publisher(JointState, f'{driver}/command', 10)
        self.idx = 0
        self.ready = not enable
        if enable:
            self.cli = self.create_client(SetBool, f'{driver}/set_torque')
            self.get_logger().info('Menunggu service set_torque...')
            self.cli.wait_for_service()
            fut = self.cli.call_async(SetBool.Request(data=True))
            fut.add_done_callback(self._torque_done)
        self.create_timer(self.hold_s, self.tick)

    def _torque_done(self, fut):
        res = fut.result()
        self.ready = bool(res and res.success)
        self.get_logger().info(f'Torque: {res.message if res else "tidak ada respons"}')

    def tick(self):
        if not self.ready:
            return
        name = self.sequence[self.idx]
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = list(self.names)
        js.position = self.poses[name]
        self.pub.publish(js)
        self.get_logger().info(f'Pose: {name}')
        self.idx = (self.idx + 1) % len(self.sequence)


def main(args=None):
    rclpy.init(args=args)
    node = DemoSequence()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
