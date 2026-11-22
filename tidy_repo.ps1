<#
  tidy_repo.ps1 - Merapikan folder "Robot Arm"

  Cara pakai (PowerShell, dari folder F:\Projects\Robot Arm):
    powershell -ExecutionPolicy Bypass -File .\tidy_repo.ps1          # DRY RUN: hanya tampilkan rencana
    powershell -ExecutionPolicy Bypass -File .\tidy_repo.ps1 -Apply   # Eksekusi pemindahan

  Prinsip:
  - TIDAK ADA file yang dihapus. File sampah (venv, build ROS, cache, log) dipindah ke _to_delete\
    supaya Anda bisa cek dulu, lalu hapus manual folder _to_delete\ itu.
  - Desain final (STL/STEP) dipindah ke 01_design\, referensi lama ke 99_archive\.
  - Script aman dijalankan ulang: item yang sudah dipindah akan dilewati.
  - Path di script CAD (cad_scripts\*.py) otomatis disesuaikan dengan lokasi baru.
  - Tutup dulu VS Code / slicer / CAD yang sedang membuka file di folder ini.
#>
param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$Thingi = 'Robot Arm For AX-12A Dynamixel Actuators - 166430'

# Urutan penting: sampah di dalam ROS2\ dipindah dulu, baru folder induknya.
$Moves = @(
  # ---------- 1. Sampah / file hasil generate (bisa dibuat ulang) -> _to_delete ----------
  @('ROS2\.venv-cad',                                   '_to_delete\ROS2_venv-cad'),
  @('ROS2\compact_arm\ros2_ws\build',                   '_to_delete\compact_arm_ros2_ws_build'),
  @('ROS2\compact_arm\ros2_ws\install',                 '_to_delete\compact_arm_ros2_ws_install'),
  @('ROS2\compact_arm\ros2_ws\log',                     '_to_delete\compact_arm_ros2_ws_log'),
  @('ROS2\compact_arm\output\ros_logs',                 '_to_delete\compact_arm_ros_logs'),
  @('ROS2\compact_arm\output\ros_logs_gui',             '_to_delete\compact_arm_ros_logs_gui'),
  @('ROS2\compact_arm\__pycache__',                     '_to_delete\compact_arm_pycache'),
  @('ROS2\mesh_analysis\__pycache__',                   '_to_delete\mesh_analysis_pycache'),
  @('ROS2\mesh_analysis\separated_stl.zip',             '_to_delete\mesh_analysis_separated_stl.zip'),
  @('widowx_ax12_hybrid_base\__pycache__',              '_to_delete\hybrid_base_pycache'),
  @('MX-28_Arm-mk2.zip',                                '_to_delete\MX-28_Arm-mk2_rusak_224byte.zip'),

  # ---------- 2. Desain yang dipakai -> 01_design ----------
  @('AX12A_WidowX_Full_STL',                            '01_design\stl'),
  @('AX12A_WidowX_Full_STEP',                           '01_design\step'),
  @('widowx_ax12_hybrid_base',                          '01_design\cad_scripts'),
  @('01_design\cad_scripts_requirements.txt',           '01_design\cad_scripts\requirements.txt'),
  @($Thingi,                                            '01_design\source\ax12a_arm_thingiverse_166430'),

  # ---------- 3. Referensi & eksperimen lama -> 99_archive ----------
  @('widowx-mkii-robotic-arm',                          '99_archive\reference_designs\widowx_mkii_robotic_arm'),
  @('MX-28_Arm-mk2 (1)',                                '99_archive\reference_designs\mx28_arm_mk2'),
  @('ROS2\MX-28_Arm-mk2.stl',                           '99_archive\reference_designs\mx28_arm_mk2_stl\MX-28_Arm-mk2.stl'),
  @('pxpincher_ros-kinetic-devel\pxpincher_ros-kinetic-devel', '99_archive\reference_designs\pxpincher_ros_kinetic'),
  @('ROS2\reference_widowx',                            '99_archive\reference_designs\widowx_arm_description_ros1'),
  @('ROS2\compact_arm',                                 '99_archive\old_experiments\compact_arm'),
  @('ROS2\mesh_analysis',                               '99_archive\old_experiments\mesh_analysis'),
  @('ROS2\BUILD_CONSTRAINTS.md',                        '99_archive\old_experiments\BUILD_CONSTRAINTS_lama.md'),

  # ---------- 4. File unduhan asli (zip/rar) -> 99_archive\original_downloads ----------
  @('ARM.rar',                                          '99_archive\original_downloads\ARM.rar'),
  @('MX-28_Arm-mk2 (1).zip',                            '99_archive\original_downloads\MX-28_Arm-mk2 (1).zip'),
  @('pxpincher_ros-kinetic-devel.zip',                  '99_archive\original_downloads\pxpincher_ros-kinetic-devel.zip'),
  @("$Thingi.zip",                                      "99_archive\original_downloads\$Thingi.zip"),
  @('widowx-mkii-robotic-arm.zip',                      '99_archive\original_downloads\widowx-mkii-robotic-arm.zip'),

  # ---------- 5. Gripper lama versi AX-12A (diganti gripper servo 25 kg DS3225) ----------
  @('01_design\stl\09_wrist_rotate_x1.stl',           '99_archive\old_gripper_ax12a\09_wrist_rotate_x1.stl'),
  @('01_design\stl\10_the_crawer_base_x1.stl',        '99_archive\old_gripper_ax12a\10_the_crawer_base_x1.stl'),
  @('01_design\step\09_wrist_rotate.step',            '99_archive\old_gripper_ax12a\09_wrist_rotate.step'),
  @('01_design\step\10_the_crawer_base.step',         '99_archive\old_gripper_ax12a\10_the_crawer_base.step')
)

# Folder yang seharusnya kosong setelah pemindahan
$EmptyDirsToRemove = @('pxpincher_ros-kinetic-devel', 'ROS2')

# Penyesuaian path di script CAD setelah dipindah
# CATATAN: koma unary ,@(...) wajib untuk daftar berisi SATU pasangan, kalau tidak PowerShell
# meratakan array dan mengganti karakter per karakter (bug v1 yang merusak 2 file).
$Patches = @(
  @{ File = '01_design\cad_scripts\build_full_robot_package.py'; Pairs = @(
      @("AX_ORIG_DIR = ROOT / `"$Thingi`" / `"files`"", 'AX_ORIG_DIR = ROOT / "source" / "ax12a_arm_thingiverse_166430" / "files"'),
      @('STEP_OUT_DIR = ROOT / "AX12A_WidowX_Full_STEP"', 'STEP_OUT_DIR = ROOT / "step"'),
      @('STL_OUT_DIR = ROOT / "AX12A_WidowX_Full_STL"',   'STL_OUT_DIR = ROOT / "stl"')
  )},
  @{ File = '01_design\cad_scripts\build_hybrid_base.py'; Pairs = @(
      ,@("AX_FILES = ROOT.parent / `"$Thingi`" / `"files`"", 'AX_FILES = ROOT.parent / "source" / "ax12a_arm_thingiverse_166430" / "files"')
  )},
  @{ File = '01_design\cad_scripts\render_preview.py'; Pairs = @(
      ,@("AX_FILES = ROOT.parent / `"$Thingi`" / `"files`"", 'AX_FILES = ROOT.parent / "source" / "ax12a_arm_thingiverse_166430" / "files"')
  )}
)

$log = New-Object System.Collections.Generic.List[string]
function Say([string]$msg, [string]$color = 'Gray') { Write-Host $msg -ForegroundColor $color; $log.Add($msg) }

if ($Apply) { Say "=== MODE: APPLY (file akan dipindah) ===" 'Yellow' }
else        { Say "=== MODE: DRY RUN (tidak ada yang diubah). Tambahkan -Apply untuk eksekusi ===" 'Cyan' }

$ok = 0; $skip = 0; $fail = 0
foreach ($m in $Moves) {
  $src = Join-Path $Root $m[0]
  $dst = Join-Path $Root $m[1]
  if (-not (Test-Path -LiteralPath $src)) { Say "  [lewati] tidak ada: $($m[0])" 'DarkGray'; $skip++; continue }
  if (Test-Path -LiteralPath $dst)        { Say "  [lewati] tujuan sudah ada: $($m[1])" 'DarkYellow'; $skip++; continue }
  Say "  [pindah] $($m[0])  ->  $($m[1])" 'Green'
  if ($Apply) {
    try {
      $parent = Split-Path -Parent $dst
      if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
      Move-Item -LiteralPath $src -Destination $dst
      $ok++
    } catch {
      Say "  [GAGAL] $($m[0]): $($_.Exception.Message)" 'Red'; $fail++
    }
  }
}

foreach ($d in $EmptyDirsToRemove) {
  $p = Join-Path $Root $d
  if (-not $Apply) { Say "  [hapus folder jika kosong] $d" 'Green'; continue }
  if (Test-Path -LiteralPath $p) {
    $left = @(Get-ChildItem -LiteralPath $p -Force -Recurse -File -ErrorAction SilentlyContinue)
    if ($left.Count -eq 0) {
      Say "  [hapus folder kosong] $d" 'Green'
      if ($Apply) { Remove-Item -LiteralPath $p -Recurse -Force }
    } else {
      Say "  [biarkan] $d masih berisi $($left.Count) file (cek manual)" 'DarkYellow'
    }
  }
}

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
foreach ($pt in $Patches) {
  $f = Join-Path $Root $pt.File
  if (-not (Test-Path -LiteralPath $f)) {
    if ($Apply) { Say "  [patch lewati] belum ada: $($pt.File)" 'DarkYellow' } else { Say "  [patch] $($pt.File) (setelah dipindah)" 'Green' }
    continue
  }
  $text = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
  $changed = $false
  foreach ($pair in $pt.Pairs) {
    if ($text.Contains($pair[0])) { $text = $text.Replace($pair[0], $pair[1]); $changed = $true }
  }
  if ($changed) {
    Say "  [patch path] $($pt.File)" 'Green'
    if ($Apply) { [System.IO.File]::WriteAllText($f, $text, $utf8NoBom) }
  } else {
    Say "  [patch lewati] $($pt.File) sudah sesuai" 'DarkGray'
  }
}

if ($Apply) {
  Say ""
  Say "Selesai: $ok dipindah, $skip dilewati, $fail gagal." 'Yellow'
  Say "Cek isi _to_delete\ lalu hapus manual jika sudah yakin (+/- 0.5 GB)." 'Yellow'
  $logDir = Join-Path $Root '99_archive'
  if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
  $log | Set-Content -LiteralPath (Join-Path $logDir ("tidy_log_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".txt")) -Encoding UTF8
} else {
  Say ""
  Say "Ini baru rencana. Jalankan lagi dengan -Apply untuk mengeksekusi." 'Cyan'
}
