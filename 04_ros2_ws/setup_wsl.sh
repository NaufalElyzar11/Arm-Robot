#!/usr/bin/env bash
# Siapkan workspace ROS 2 Jazzy di WSL untuk lengan AX-12A.
# Jalankan dari WSL:  bash "/mnt/f/Projects/Robot Arm/04_ros2_ws/setup_wsl.sh"
#
# Source code tetap di F:\ (satu sumber kebenaran, bisa diedit dari Windows),
# tapi build/install/log ada di ~/ax12_ws (filesystem Linux, jauh lebih cepat & tanpa masalah permission).
set -euo pipefail

REPO_SRC="${REPO_SRC:-/mnt/f/Projects/Robot Arm/04_ros2_ws/src}"
WS="${WS:-$HOME/ax12_ws}"
ROS_DISTRO_EXPECTED=jazzy

if [ ! -f "/opt/ros/${ROS_DISTRO_EXPECTED}/setup.bash" ]; then
  echo "ROS 2 ${ROS_DISTRO_EXPECTED} tidak ditemukan di /opt/ros. Cek: ls /opt/ros" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO_EXPECTED}/setup.bash"

echo "==> Workspace: $WS  (source dari $REPO_SRC)"
mkdir -p "$WS/src"
for pkg in "$REPO_SRC"/*/; do
  pkg="${pkg%/}"
  name="$(basename "$pkg")"
  ln -sfn "$pkg" "$WS/src/$name"
  echo "    link src/$name"
done

echo "==> Paket sistem"
sudo apt-get update
sudo apt-get install -y \
  python3-colcon-common-extensions python3-rosdep python3-serial python3-pytest \
  ros-${ROS_DISTRO_EXPECTED}-xacro \
  ros-${ROS_DISTRO_EXPECTED}-robot-state-publisher \
  ros-${ROS_DISTRO_EXPECTED}-joint-state-publisher \
  ros-${ROS_DISTRO_EXPECTED}-joint-state-publisher-gui \
  ros-${ROS_DISTRO_EXPECTED}-rviz2 \
  ros-${ROS_DISTRO_EXPECTED}-rqt-robot-monitor

if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update
cd "$WS"
rosdep install --from-paths src --ignore-src -r -y --rosdistro "${ROS_DISTRO_EXPECTED}"

echo "==> Akses port serial (berlaku setelah logout/login WSL: 'wsl --shutdown')"
sudo usermod -aG dialout "$USER" || true

echo "==> Build"
colcon build --symlink-install

LINE="source $WS/install/setup.bash"
if ! grep -qxF "$LINE" "$HOME/.bashrc"; then
  echo "source /opt/ros/${ROS_DISTRO_EXPECTED}/setup.bash" >> "$HOME/.bashrc"
  echo "$LINE" >> "$HOME/.bashrc"
fi

cat <<MSG

Selesai. Buka terminal baru (atau: source $WS/install/setup.bash), lalu coba:
  ros2 launch ax12_arm_description display.launch.py           # model + slider
  ros2 launch ax12_arm_bringup demo.launch.py fake:=true        # demo tanpa hardware
Build ulang setelah mengubah kode:  cd $WS && colcon build --symlink-install
MSG
