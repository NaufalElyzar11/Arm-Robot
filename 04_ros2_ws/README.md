# 04_ros2_ws — Workspace ROS 2 Jazzy

| Paket | Isi |
|---|---|
| `ax12_arm_description` | URDF/xacro (panjang link dari CAD, belum diverifikasi fisik), RViz config, launch `display.launch.py` |
| `ax12_arm_driver` | Node `ax12_driver` (serial ↔ firmware v0.2: 5 AX-12A + gripper PWM, mode `fake_hardware`), node `demo_sequence` |
| `ax12_arm_bringup` | Launch `arm.launch.py`, `demo.launch.py`, config `arm.yaml`, `demo_poses.yaml` |

## Setup di WSL (sekali)

```bash
bash "/mnt/f/Projects/Robot Arm/04_ros2_ws/setup_wsl.sh"
```

Source tetap di `F:\…\04_ros2_ws\src` (di-symlink), build di `~/ax12_ws` supaya cepat.
Cek distro dulu bila ragu: `ls /opt/ros` harus menampilkan `jazzy`.

## Menjalankan

```bash
ros2 launch ax12_arm_description display.launch.py         # lihat model, gerakkan slider
ros2 launch ax12_arm_bringup arm.launch.py fake:=true      # driver tanpa hardware
ros2 service call /ax12_driver/set_torque std_srvs/srv/SetBool "{data: true}"
ros2 topic pub --once /ax12_driver/command sensor_msgs/msg/JointState \
  "{name: [joint2_shoulder, joint6_gripper], position: [0.3, 1.0]}"   # gripper: 0 = tertutup
ros2 launch ax12_arm_bringup demo.launch.py fake:=true     # loop pose demo
ros2 run rqt_robot_monitor rqt_robot_monitor               # tegangan & suhu (/diagnostics)
ros2 service call /ax12_driver/estop std_srvs/srv/Trigger  # torque off (lengan akan jatuh!)
```

## Menghubungkan adapter USB-TTL ke WSL

WSL tidak otomatis melihat port USB. Pakai **usbipd-win** (PowerShell sebagai Administrator):

```powershell
winget install usbipd
usbipd list                       # cari BUSID adapter (CP210x / CH340 / FTDI)
usbipd bind --busid <BUSID>       # sekali saja
usbipd attach --wsl --busid <BUSID>   # tiap kali dicolok ulang
```

Di WSL: `ls /dev/ttyUSB*` → jalankan `arm.launch.py port:=/dev/ttyUSB0`.

## Langkah berikutnya

1. Verifikasi panjang link (sudah diisi dari CAD) dengan robot fisik setelah dirakit.
2. Kalibrasi `zero_raw` & `direction` di `ax12_arm_bringup/config/arm.yaml` (lihat `06_docs/calibration.md`).
3. Mesh per link (lihat `ax12_arm_description/meshes/README.md`).
4. IK: lengan 5-DOF tidak bisa mencapai sembarang orientasi 6D. Pilihan: IK analitik sendiri
   (yaw + planar 3-link + roll) — paling cocok, atau MoveIt dengan IK position-only.
5. Bila butuh MoveIt penuh: ganti driver Python ini dengan hardware interface `ros2_control`.
