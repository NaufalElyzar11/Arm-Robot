param([switch]$Demo)
$ErrorActionPreference = 'Stop'
$workspacePath = Join-Path $PSScriptRoot 'ros2_ws'
$demoValue = if ($Demo) { 'true' } else { 'false' }
$command = 'source /opt/ros/jazzy/setup.bash && source install/setup.bash && ros2 launch ax12_compact_description display.launch.py demo:=' + $demoValue
& wsl.exe -d Ubuntu-24.04 --cd $workspacePath -- bash -lc $command
if ($LASTEXITCODE -ne 0) { throw "ROS2 launch exited with code $LASTEXITCODE" }
