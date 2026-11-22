# AX-12A compact arm — prototipe V1

Desain baru untuk **5 AX-12A + 1 MG90S**, rangka cetak PLA, dan model gerak ROS2. Status: **prototipe untuk uji pasang**. File STEP adalah solid parametrik dari desain baru ini; bukan pemulihan CAD asli WidowX dari STL.

Tujuan pertama adalah bergerak dan menjepit benda PLA/plastik kecil. Benda **10 gram** dipakai sebagai skenario perhitungan awal, bukan batas payload yang telah diuji. Tidak ada motor fisik yang diperintah oleh software yang disertakan.

## Buka hasil

- `output/assembly.step`: assembly zero pose, dengan part serta representasi sederhana servo terpisah dan bernama.
- `output/step/`: 8 solid part cetak, satu STEP per part, dalam frame lokal link.
- `output/stl/`: 8 STL part cetak, satu unit masing-masing; sudah ditempatkan pada Z minimum nol. Beberapa part tetap membutuhkan support.
- `output/coupons/`: 5 kupon/sampel untuk pemeriksaan dudukan sebelum mencetak semua part.
- `output/assembly_preview.png` dan `output/parts_preview.png`: gambar assembly dan daftar part.
- `output/parts.csv`: dimensi CAD dan perkiraan berat PLA solid.
- `ros2_ws/src/ax12_compact_description`: paket ROS2 dengan URDF, mesh, RViz, slider sendi, dan demonstrasi gerak.

Mesh abu-abu pada assembly adalah envelope servo untuk perancangan ruang; **jangan dicetak sebagai pengganti servo**. Jangan mengganti mesh pada URDF dengan STL versi cetak tanpa transform: orientasi dan origin versi cetak berbeda dari mesh lokal link dalam paket ROS2.

## Susunan dan ukuran

| Bagian | Aktuator / jarak |
| --- | --- |
| Putaran base | AX-12A 1; sumbu 55 mm di atas dasar |
| Bahu | AX-12A 2; sumbu 44 mm di atas sumbu base |
| Siku | AX-12A 3; 65 mm dari sumbu bahu |
| Tekuk pergelangan | AX-12A 4; 65 mm dari sumbu siku |
| Putar pergelangan | AX-12A 5; 65 mm dari sumbu tekuk pergelangan |
| Gripper | MG90S; satu rahang tetap dan satu rahang berputar |

Lima sendi menentukan posisi/orientasi lengan; gripper menambah satu gerakan buka-tutup. Ini bukan lengan dengan enam DOF orientasi bebas. Angka jarak adalah jarak sumbu, bukan panjang keseluruhan bracket.

Rentang sendi URDF sengaja dibatasi untuk prototipe: base ±90°, bahu ±37°, siku ±49°, wrist pitch ±40°, wrist roll ±57°, gripper 0–40°. Itu rentang model yang disampel, bukan zero atau limit firmware motor yang sudah dikalibrasi. Demo memakai rentang lebih kecil. Slider RViz tidak melakukan pencegahan tabrakan atau pembatasan torsi aktif.

## Cetak kupon dulu

Gunakan Kobra X, nozzle 0,4 mm, PLA, layer awal 0,20 mm. Gunakan profil suhu PLA yang telah cocok untuk filamen Anda; file G-code tidak disediakan karena profil mesin/filamen belum diverifikasi.

1. Cetak `ax12_body_mount.stl` dan `ax12_horn_pattern.stl`. Periksa lubang bodi, empat lubang horn pada PCD 16 mm, akses sekrup pusat, dan ruang putar. Lubang clearance desain 2,3 mm untuk sekrup nominal M2. Pola bodi memakai jarak melintang 27 mm dan pitch 8 mm sesuai gambar ROBOTIS.
2. Cetak `mg90s_cradle.stl`, `mg90s_cap.stl`, dan `mg90s_horn_slots.stl`. Uji badan MG90S, posisi horn bawaan, jalur kabel, dan celah penjepit. Tambahkan shim tipis atau sesuaikan dimensi CAD bila casing/horn unit aktual berbeda. Jangan paksa servo masuk.
3. Setelah cocok, cetak 8 part di `output/stl/`. Awali dengan 4 perimeter dan 5 lapis atas/bawah. Infill 30–40% boleh menjadi titik awal uji; ketebalan dan orientasi lapisan tetap menentukan kekuatan. Nilai massa/inersia model dihitung sebagai PLA solid, bukan hasil slicing infill tersebut.
4. `moving_finger` dan `gripper_cap` dapat diletakkan datar. Link bertingkat, adapter yaw/wrist, gripper body, dan terutama dek atas base perlu diperiksa support-nya pada preview slicer. Hilangkan support dari lubang dan permukaan pasang sebelum perakitan.

Semua STL memakai mm; impor 100%. Jangan menskalakan model seluruhnya untuk membetulkan lubang. Gunakan parameter sumber dan kupon yang dikoreksi. Base harus dibaut/dijepit ke meja atau papan yang stabil.

## Hardware dan perakitan

- 5 AX-12A dengan horn asli serta hardware dudukan yang sesuai.
- 1 MG90S dengan horn bawaan. Gripper menggunakan horn itu; tidak mencetak spline pengganti.
- Sekrup M2 untuk 8 posisi dudukan bodi per servo dan 4 posisi horn per servo. Gunakan nut/hardware bodi asli yang sesuai unit. Panjang harus dipilih setelah mengukur tumpukan part dan kedalaman lubang; jangan membiarkan ujung sekrup menekan bagian dalam servo.
- Pola horn AX-12A berjarak 0,5 mm dari bidang horn nominal dalam model; gunakan washer/spacer 0,5 mm yang sesuai. Plate cetak tebal 3 mm. Gambar ROBOTIS menyebut kedalaman tap horn 4 mm, sehingga kedalaman masuk sekrup harus kurang dari batas itu.
- 4 baut M2 sekitar 22 mm dengan mur/washer untuk cap MG90S; konfirmasi panjang setelah uji pasang. Posisi mur di bawah cradle harus tetap dapat diakses.
- Sekrup kecil yang cocok dengan horn MG90S untuk slot jari, serta sekrup penahan horn bawaan. Ukuran slot 1,8 mm; posisi/lubang horn aktual perlu dicocokkan.
- Bantalan karet/busa tipis pada rahang; empat lubang base berdiameter 4,5 mm untuk penjangkaran.

Urutan: pasang AX base pada stand, sambungkan yaw adapter ke horn base, pasang servo bahu, lalu upper link + servo siku, forearm link + servo wrist pitch, wrist adapter + servo wrist roll, dan gripper. Pasang MG90S ke cradle, cap, lalu jari ke horn. Pastikan orientasi netral motor sesuai zero mekanis sebelum horn dikencangkan; jangan menganggap posisi register tengah otomatis sesuai gambar.

Desain V1 memakai tumpuan horn satu sisi. Kemampuan menahan gaya radial, kelenturan bracket, dan umur material belum diuji fisik. Baut, kabel, horn detail, konektor, dan bentuk casing kecil tidak dimodelkan lengkap. Clearance digital terhadap envelope belum membuktikan akses alat atau kecocokan semua hardware. Uji kupon dan perakitan manual menentukan revisi berikutnya.

## Daya dan kontrol

AX-12A memakai bus TTL half-duplex DYNAMIXEL Protocol 1.0; MG90S memakai sinyal servo hobi. MG90S memerlukan rail tegangan sesuai unitnya dan ground sinyal bersama; jangan sambungkan ke rail 12 V AX-12A. Driver hardware, suplai, ID motor, zero, dan limit fisik belum dikonfigurasi. Paket ini hanya mengirim `JointState` dan TF untuk visualisasi; tidak mengirim perintah ke bus atau PWM.

## Menjalankan ROS2 Jazzy di komputer ini

Paket disiapkan untuk WSL `Ubuntu-24.04`. Dari PowerShell di folder proyek:

```powershell
& '.\compact_arm\run_ros2.ps1'
```

Ini membuka RViz dan slider sendi. Untuk demo otomatis:

```powershell
& '.\compact_arm\run_ros2.ps1' -Demo
```

Atau dari Ubuntu/WSL:

```bash
source /opt/ros/jazzy/setup.bash
cd '/mnt/f/Projects/Robot Arm/ROS2/compact_arm/ros2_ws'
colcon build --packages-select ax12_compact_description
source install/setup.bash
ros2 launch ax12_compact_description display.launch.py
# Demo tanpa GUI slider:
ros2 launch ax12_compact_description display.launch.py demo:=true
```

Untuk tes tanpa jendela: tambahkan `rviz:=false` pada mode demo. Tutup dengan Ctrl+C. Tampilan WSLg diperlukan untuk RViz/slider. Instalasi tambahan yang dilakukan pada sesi ini: paket `ros-jazzy-joint-state-publisher-gui`; dependensi CAD Windows terisolasi di `.venv-cad` pada root proyek.

## Yang diperiksa dan batasnya

- Setiap part CAD satu solid valid. Delapan STL part dan lima STL kupon tertutup, dengan orientasi face konsisten pada part utama.
- URDF diperiksa dengan parser; referensi semua mesh ada; inersia estimasi positif.
- `output/validation.json` menyimpan benturan volume CAD pada zero pose, ujung rentang tiap sendi, kombinasi sendi, dan sampel lintasan demo. Pemeriksaan ini diskret, bukan sertifikasi seluruh ruang gerak.
- Massa PLA dihitung dari volume solid dan densitas 1,24 g/cm³. Massa motor memakai spesifikasi pabrikan dan distribusi seragam pada envelope. Baut/kabel, kelenturan, gesekan, percepatan, panas, dan gaya jepit belum masuk model.
- Sweep statis dengan benda uji 10 gram adalah penilaian awal, bukan bukti payload. Jangan memakai torsi stall sebagai rating operasi terus-menerus.
- `output/ros2_validation.json` mencatat hasil tes ROS2, bila tes berhasil. `ros2_smoke.log` menyimpan log eksekusi. RViz merupakan visualisasi kinematika; konfigurasi Gazebo/MoveIt2 dan kontrol hardware belum dibuat.

## Mengubah dan membangun ulang

Parameter jarak sumbu ada di `design.json`; detail dudukan di `build.py`. Satu sumber ini menghasilkan STEP, STL, frame URDF, massa dan inersia, sehingga perubahan geometri tidak perlu disalin manual antarformat.

```powershell
& '.\.venv-cad\Scripts\python.exe' compact_arm/build.py
& '.\.venv-cad\Scripts\python.exe' compact_arm/validate.py
& '.\.venv-cad\Scripts\python.exe' compact_arm/render_preview.py
```

Lalu build ulang paket ROS2 dengan `colcon`. `output/stl` adalah orientasi cetak; `ros2_ws/src/.../meshes` adalah koordinat lokal link. Jangan menukar keduanya.

## Referensi

- [ROBOTIS AX-12A dan gambar dimensi](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/); gambar disimpan di `reference/ax-12a_dimension.png`.
- [TowerPro MG90S](https://towerpro.com.tw/product/mg90s-3/). Varian/drawing MG90S berbeda; kupon harus dicocokkan dengan unit yang dipakai.
- [WidowX asli menggunakan MX-64, MX-28, dan AX-12](https://www.interbotix.com/Robotic-Arms). Pergantian semua motor menjadi AX-12A mengubah kebutuhan desain; tidak menunjukkan kesalahan pada desain asli.
