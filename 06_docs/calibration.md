# Kalibrasi nol sendi

Tujuan: mengisi `zero_raw` dan `direction` di `04_ros2_ws/src/ax12_arm_bringup/config/arm.yaml`
supaya sudut di RViz = sudut robot asli.

1. Jalankan `ros2 launch ax12_arm_bringup arm.launch.py` (torque **off**, default).
2. Pegang lengan, posisikan ke **pose nol URDF**: lengan lurus tegak ke atas, wrist lurus, gripper tertutup.
3. Baca raw dari serial monitor firmware (baris `J`) atau sementara set semua `zero_raw` = 512 dan baca
   `ros2 topic echo /joint_states`, lalu hitung balik. Catat raw tiap sendi → `zero_raw`.
4. Gerakkan tiap sendi sedikit ke arah positif URDF (lihat sumbu di RViz dengan display TF). Bila RViz
   bergerak berlawanan → `direction: -1` untuk sendi itu.
5. Cek batas: gerakkan tiap sendi ke batas aman (tidak menabrak rangka/kabel), catat raw-nya →
   `LIMIT_MIN/LIMIT_MAX` di `03_firmware/ax12_bridge/ax12_bridge.ino`, upload ulang.
6. Verifikasi: nyalakan torque, kirim pose kecil, bandingkan robot vs RViz.

## Gripper servo 25 kg (PWM)

1. **Sebelum tuas dipasang**: `T 1`, kirim `G 1500` lewat serial monitor, pasang horn disc + adapter `11b`
   sehingga pin tuas berada di pose tengah.
2. Pasang tuas & jari. Naikkan/turunkan pulsa 50 µs per langkah (`G 1450`, `G 1400`, …) untuk mencari
   pulsa **jari terbuka penuh** dan pulsa **jari hampir bertemu** (sisakan ±1 mm, jangan menekan).
3. Isi `GRIP_US_MIN/MAX/SAFE` di firmware dan `gripper_us_min/max`, `gripper_zero_us` (= pulsa tertutup),
   `gripper_direction` di `arm.yaml`. Bila pulsa naik = menutup, pakai `gripper_direction: -1` dan
   `gripper_zero_us` = pulsa tertutup.

Catatan: AX-12A punya dead zone 300–360° (raw tidak valid di luar 0–1023). Pastikan pose kerja
tidak melewati daerah ini saat memasang horn.
