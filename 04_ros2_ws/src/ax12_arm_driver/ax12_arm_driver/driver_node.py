"""ax12_driver — node ROS 2 penghubung ke firmware ax12_bridge v0.2 (5x AX-12A + gripper servo PWM).

Topic & service (nama relatif node, default node name "ax12_driver"):
  sub  ~/command       sensor_msgs/JointState   target posisi (rad) per nama sendi; sendi yang tidak disebut tetap
  pub  joint_states    sensor_msgs/JointState   posisi aktual (rad), 50 Hz dari firmware
  pub  /diagnostics    diagnostic_msgs/DiagnosticArray   tegangan bus & suhu servo AX
  srv  ~/set_torque    std_srvs/SetBool
  srv  ~/estop         std_srvs/Trigger         torque off semua (lengan akan jatuh!)

Catatan gripper: servo PWM tidak punya feedback. Nilai gripper di joint_states adalah
PERINTAH yang sedang dikirim firmware (sudah melewati pembatas kecepatan), bukan posisi terukur.

Parameter penting:
  fake_hardware (bool)  true = simulasi tanpa Arduino
  port, baud            serial adapter USB-TTL (di WSL biasanya /dev/ttyUSB0 setelah usbipd attach)
  zero_raw, direction   5 nilai untuk AX-12A (hasil kalibrasi)
  gripper_zero_us, gripper_direction, gripper_deg_per_2000us, gripper_us_min/max
"""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import SetBool, Trigger
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue

from .protocol import (N_AX, format_goal, parse_line, rad_to_raw, rad_to_us,
                       raw_to_rad, us_to_rad)

try:
    import serial  # python3-serial
except ImportError:  # memungkinkan fake mode walau pyserial belum terpasang
    serial = None

DEFAULT_JOINTS = [
    'joint1_base_yaw', 'joint2_shoulder', 'joint3_elbow',
    'joint4_wrist_pitch', 'joint5_wrist_roll', 'joint6_gripper',
]


class Ax12Driver(Node):
    def __init__(self):
        super().__init__('ax12_driver')
        self.declare_parameter('fake_hardware', False)
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('joint_names', DEFAULT_JOINTS)
        self.declare_parameter('zero_raw', [512, 512, 512, 512, 512])
        self.declare_parameter('direction', [1, 1, 1, 1, 1])
        self.declare_parameter('gripper_zero_us', 1000)      # pulsa saat jari tertutup (sudut 0 di URDF)
        self.declare_parameter('gripper_direction', 1)
        self.declare_parameter('gripper_deg_per_2000us', 180.0)
        self.declare_parameter('gripper_us_min', 1000)
        self.declare_parameter('gripper_us_max', 2000)
        self.declare_parameter('fake_speed_rad_s', 1.0)
        self.declare_parameter('low_voltage_warn', 10.8)
        self.declare_parameter('temperature_warn_c', 60)

        self.fake = self.get_parameter('fake_hardware').value
        self.names = list(self.get_parameter('joint_names').value)
        self.zero = list(self.get_parameter('zero_raw').value)
        self.dir = list(self.get_parameter('direction').value)
        self.g_zero = float(self.get_parameter('gripper_zero_us').value)
        self.g_dir = int(self.get_parameter('gripper_direction').value)
        self.g_deg = float(self.get_parameter('gripper_deg_per_2000us').value)
        self.g_min = int(self.get_parameter('gripper_us_min').value)
        self.g_max = int(self.get_parameter('gripper_us_max').value)
        if len(self.names) != N_AX + 1 or len(self.zero) != N_AX or len(self.dir) != N_AX:
            raise ValueError(f'joint_names harus {N_AX + 1} nama; zero_raw & direction harus {N_AX} nilai')

        self.pos_raw = list(self.zero)          # posisi AX terakhir yang diketahui
        self.goal_raw = list(self.zero)
        self.grip_us = int(self.g_zero)         # perintah gripper terakhir (diketahui)
        self.grip_goal_us = int(self.g_zero)
        self.torque = False
        self.ser = None
        self.rx_buf = b''

        self.js_pub = self.create_publisher(JointState, 'joint_states', 10)
        self.diag_pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self.create_subscription(JointState, '~/command', self.on_command, 10)
        self.create_service(SetBool, '~/set_torque', self.on_set_torque)
        self.create_service(Trigger, '~/estop', self.on_estop)

        if self.fake:
            self.get_logger().warn('FAKE HARDWARE: tidak ada Arduino, posisi disimulasikan.')
            self.fake_dt = 0.02
            self.create_timer(self.fake_dt, self.fake_step)
        else:
            self.create_timer(0.005, self.poll_serial)
            self.create_timer(2.0, self.ensure_serial)
            self.ensure_serial()

    # ------------------------------------------------------------------ konversi
    def ax_rad(self, i, raw):
        return raw_to_rad(raw, self.zero[i], self.dir[i])

    def ax_raw(self, i, rad):
        return rad_to_raw(rad, self.zero[i], self.dir[i])

    def grip_rad(self, us):
        return us_to_rad(us, self.g_zero, self.g_dir, self.g_deg)

    def grip_to_us(self, rad):
        return rad_to_us(rad, self.g_zero, self.g_dir, self.g_deg, self.g_min, self.g_max)

    # ------------------------------------------------------------------ serial
    def ensure_serial(self):
        if self.fake or (self.ser is not None and self.ser.is_open):
            return
        if serial is None:
            self.get_logger().error('pyserial belum terpasang: sudo apt install python3-serial')
            return
        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        try:
            self.ser = serial.Serial(port, baud, timeout=0)
            self.get_logger().info(f'Terhubung ke {port} @ {baud}')
            self.send('PING\n')
            self.send('S\n')
        except (serial.SerialException, OSError) as e:
            self.ser = None
            self.get_logger().error(f'Gagal buka {port}: {e} (coba lagi 2 s)', throttle_duration_sec=10.0)

    def send(self, text: str):
        if self.ser is None:
            return False
        try:
            self.ser.write(text.encode('ascii'))
            return True
        except (serial.SerialException, OSError) as e:
            self.get_logger().error(f'Serial putus: {e}')
            self.ser = None
            return False

    def poll_serial(self):
        if self.ser is None:
            return
        try:
            waiting = self.ser.in_waiting
            if waiting:
                self.rx_buf += self.ser.read(waiting)
        except (serial.SerialException, OSError) as e:
            self.get_logger().error(f'Serial putus: {e}')
            self.ser = None
            return
        while b'\n' in self.rx_buf:
            raw_line, self.rx_buf = self.rx_buf.split(b'\n', 1)
            self.handle_line(raw_line.decode('ascii', errors='replace'))
        if len(self.rx_buf) > 1024:
            self.rx_buf = b''

    def handle_line(self, line: str):
        msg = parse_line(line)
        if msg.kind == 'J':
            ax, grip = msg.values[:N_AX], msg.values[N_AX]
            missing = [self.names[i] for i, v in enumerate(ax) if v < 0]
            for i, v in enumerate(ax):
                if v >= 0:
                    self.pos_raw[i] = v
            if grip >= 0:
                self.grip_us = grip
            if missing:
                self.get_logger().warn(f'Servo tidak merespons: {missing}', throttle_duration_sec=5.0)
            self.publish_joint_states()
        elif msg.kind == 'H':
            self.publish_health(msg.values[0], msg.values[1:])
        elif msg.kind == 'I':
            absent = [self.names[i] for i, v in enumerate(msg.values) if v == 0]
            if absent:
                self.get_logger().warn(f'Servo AX tidak ditemukan: {absent}')
            else:
                self.get_logger().info('Semua servo AX merespons. (Gripper PWM tidak bisa dicek otomatis.)')
        elif msg.kind == 'E':
            if msg.text.startswith('LOWBATT'):
                self.torque = False
            self.get_logger().error(f'Firmware: {msg.text}')
        elif msg.kind == 'OK':
            if msg.text.startswith('T '):
                self.torque = msg.text.endswith('1')
            if msg.text.startswith('BOOT'):
                self.torque = False
                self.get_logger().warn('Arduino reset (torque off).')
            self.get_logger().debug(f'Firmware OK: {msg.text}')

    # ------------------------------------------------------------------ fake
    def fake_step(self):
        step = self.get_parameter('fake_speed_rad_s').value * self.fake_dt
        for i in range(N_AX):
            cur, tgt = self.ax_rad(i, self.pos_raw[i]), self.ax_rad(i, self.goal_raw[i])
            if abs(tgt - cur) <= step:
                self.pos_raw[i] = self.goal_raw[i]
            else:
                self.pos_raw[i] = self.ax_raw(i, cur + math.copysign(step, tgt - cur))
        cur, tgt = self.grip_rad(self.grip_us), self.grip_rad(self.grip_goal_us)
        if abs(tgt - cur) <= step:
            self.grip_us = self.grip_goal_us
        else:
            self.grip_us = self.grip_to_us(cur + math.copysign(step, tgt - cur))
        self.publish_joint_states()

    # ------------------------------------------------------------------ ROS
    def publish_joint_states(self):
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = list(self.names)
        js.position = [self.ax_rad(i, self.pos_raw[i]) for i in range(N_AX)] + [self.grip_rad(self.grip_us)]
        self.js_pub.publish(js)

    def publish_health(self, volt_dv, temps):
        warn_v = self.get_parameter('low_voltage_warn').value
        warn_t = self.get_parameter('temperature_warn_c').value
        st = DiagnosticStatus()
        st.name = 'ax12_arm: power & servos'
        st.hardware_id = 'ax12_bridge'
        volts = volt_dv / 10.0 if volt_dv > 0 else math.nan
        hot = [self.names[i] for i, t in enumerate(temps) if t >= warn_t]
        if volt_dv <= 0:
            st.level, st.message = DiagnosticStatus.WARN, 'Tegangan tidak terbaca'
        elif volts < warn_v:
            st.level, st.message = DiagnosticStatus.WARN, f'Baterai rendah {volts:.1f} V'
        elif hot:
            st.level, st.message = DiagnosticStatus.WARN, f'Servo panas: {hot}'
        else:
            st.level, st.message = DiagnosticStatus.OK, f'{volts:.1f} V'
        st.values = [KeyValue(key='voltage_V', value=f'{volts:.1f}'),
                     KeyValue(key='torque_enabled', value=str(self.torque)),
                     KeyValue(key='gripper_cmd_us', value=str(self.grip_us))]
        st.values += [KeyValue(key=f'temp_{self.names[i]}_C', value=str(t)) for i, t in enumerate(temps)]
        arr = DiagnosticArray()
        arr.header.stamp = self.get_clock().now().to_msg()
        arr.status = [st]
        self.diag_pub.publish(arr)
        if st.level != DiagnosticStatus.OK:
            self.get_logger().warn(st.message, throttle_duration_sec=10.0)

    def on_command(self, msg: JointState):
        if not self.torque:
            self.get_logger().warn('Perintah diabaikan: torque off (panggil ~/set_torque true)',
                                   throttle_duration_sec=5.0)
            return
        if len(msg.position) != len(msg.name):
            self.get_logger().warn('JointState command: jumlah name dan position tidak sama')
            return
        index = {n: i for i, n in enumerate(self.names)}
        for name, rad in zip(msg.name, msg.position):
            i = index.get(name)
            if i is None or not math.isfinite(rad):
                continue
            if i < N_AX:
                self.goal_raw[i] = self.ax_raw(i, rad)
            else:
                self.grip_goal_us = self.grip_to_us(rad)
        if not self.fake:
            self.send(format_goal(self.goal_raw, self.grip_goal_us))

    def on_set_torque(self, req, res):
        if req.data:
            self.goal_raw = list(self.pos_raw)  # firmware juga menyamakan goal AX ke posisi sekarang
            self.grip_goal_us = self.grip_us
        if self.fake:
            self.torque = req.data
            res.success, res.message = True, f'fake torque={self.torque}'
            return res
        if self.ser is None:
            res.success, res.message = False, 'Serial belum terhubung'
            return res
        ok = self.send('T 1\n' if req.data else 'T 0\n')
        if ok:
            self.torque = req.data  # dikonfirmasi lagi saat balasan "OK T x" diterima
        res.success = ok
        res.message = f'torque={req.data}' if ok else 'gagal kirim'
        return res

    def on_estop(self, req, res):
        self.torque = False
        ok = True if self.fake else self.send('X\n')
        res.success, res.message = ok, 'ESTOP: torque off'
        self.get_logger().warn('ESTOP dipanggil')
        return res

    def destroy_node(self):
        # Sengaja TIDAK mematikan torque saat node berhenti: lengan akan jatuh.
        # Servo tetap menahan posisi terakhir; matikan dengan ~/estop atau saklar daya.
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Ax12Driver()
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
