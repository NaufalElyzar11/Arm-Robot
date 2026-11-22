cmake_minimum_required(VERSION 3.8)
project(ax12_arm_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf launch rviz meshes config
  DESTINATION share/${PROJECT_NAME})

ament_package()
