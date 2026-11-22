from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory("ax12_compact_description"))
    description = (share / "urdf" / "ax12_compact.urdf").read_text()
    demo = LaunchConfiguration("demo")
    return LaunchDescription([
        DeclareLaunchArgument("demo", default_value="false", description="Animate joint states; never sends commands to hardware."),
        DeclareLaunchArgument("rviz", default_value="true"),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": description}], output="screen"),
        Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui",
             condition=UnlessCondition(demo)),
        Node(package="ax12_compact_description", executable="demo_joint_states.py", condition=IfCondition(demo)),
        Node(package="rviz2", executable="rviz2", condition=IfCondition(LaunchConfiguration("rviz")),
             arguments=["-d", str(share / "rviz" / "display.rviz")]),
    ])
