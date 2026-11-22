"""Robot + urutan pose demo berulang (mode idle pameran).

  ros2 launch ax12_arm_bringup demo.launch.py fake:=true
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup = FindPackageShare('ax12_arm_bringup')
    return LaunchDescription([
        DeclareLaunchArgument('fake', default_value='true'),
        DeclareLaunchArgument('port', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('rviz', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([bringup, 'launch', 'arm.launch.py'])),
            launch_arguments={'fake': LaunchConfiguration('fake'),
                              'port': LaunchConfiguration('port'),
                              'rviz': LaunchConfiguration('rviz')}.items()),
        Node(package='ax12_arm_driver', executable='demo_sequence', name='demo_sequence',
             output='screen',
             parameters=[PathJoinSubstitution([bringup, 'config', 'demo_poses.yaml'])]),
    ])
