"""Jalankan robot: robot_state_publisher + driver (+ RViz).

  ros2 launch ax12_arm_bringup arm.launch.py                 # hardware asli
  ros2 launch ax12_arm_bringup arm.launch.py fake:=true      # tanpa hardware
  ros2 launch ax12_arm_bringup arm.launch.py port:=/dev/ttyUSB1 rviz:=false
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc = FindPackageShare('ax12_arm_description')
    bringup = FindPackageShare('ax12_arm_bringup')
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([desc, 'urdf', 'ax12_arm.urdf.xacro'])]),
        value_type=str)

    fake = LaunchConfiguration('fake')
    port = LaunchConfiguration('port')
    rviz = LaunchConfiguration('rviz')

    return LaunchDescription([
        DeclareLaunchArgument('fake', default_value='false'),
        DeclareLaunchArgument('port', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('rviz', default_value='true'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}]),
        Node(package='ax12_arm_driver', executable='ax12_driver', name='ax12_driver',
             output='screen',
             parameters=[PathJoinSubstitution([bringup, 'config', 'arm.yaml']),
                         {'fake_hardware': ParameterValue(fake, value_type=bool),
                          'port': port}]),
        Node(package='rviz2', executable='rviz2', condition=IfCondition(rviz),
             arguments=['-d', PathJoinSubstitution([desc, 'rviz', 'display.rviz'])]),
    ])
