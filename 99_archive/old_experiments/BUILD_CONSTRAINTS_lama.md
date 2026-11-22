# Kebutuhan robot fisik dan simulasi

Diperbarui 6 Oktober 2026 berdasarkan informasi pengguna.

## Perangkat yang dikonfirmasi

- Servo lengan: **5 unit DYNAMIXEL AX-12A**, semuanya tersedia menurut pengguna.
- Servo gripper: **MG90S** sebagai pilihan awal pengguna; belum dikonfirmasi sudah tersedia atau belum.
- Printer: Anycubic Kobra X, sesuai nama yang disampaikan pengguna.
- Nozzle: 0,4 mm.
- Filamen: PLA; merek dan profil material belum diketahui.
- Tujuan: rangka yang dapat dicetak dan dirakit, serta model artikulasi ROS2 yang sesuai robot fisik.
- Model awal: `MX-28_Arm-mk2.stl`, terkait WidowX MKII menurut tautan pengguna.

## Konfigurasi awal yang dipakai

| Aktuator | Fungsi |
| --- | --- |
| AX-12A 1 | Rotasi base / yaw |
| AX-12A 2 | Bahu / pitch |
| AX-12A 3 | Siku / pitch |
| AX-12A 4 | Tekuk pergelangan / pitch |
| AX-12A 5 | Putar pergelangan / roll |
| MG90S | Buka-tutup gripper |

Ini 5 DOF lengan ditambah 1 aktuator gripper, bukan lengan 6 DOF. Pengguna kemudian menegaskan target benda cetakan PLA/plastik kecil dan meminta pekerjaan dilanjutkan. Skenario desain awal dipilih 10 gram untuk perhitungan, bukan target angka yang diberikan pengguna atau payload tervalidasi. Uji awal hardware tetap dimulai tanpa benda, kemudian benda ringan.

Desain kompak baru, STEP/STL per part, kupon uji pasang, dan paket visualisasi ROS2 tersedia di `compact_arm/README.md`. File ini berisi pertimbangan awal; dimensi prototipe terbaru bersumber dari `compact_arm/design.json` dan laporan pemeriksaannya di `compact_arm/output/validation.json`. Prototipe belum diuji cetak atau dirakit fisik.

MG90S menurut halaman TowerPro: massa 13,4 gram, dimensi nominal 22,8 × 12,2 × 28,5 mm, stall torque 1,8 kgf·cm pada 4,8 V. Detail tab mounting/horn perlu mengikuti unit aktual. Gunakan suplai teratur sesuai spesifikasi unit, bukan rail 12 V AX-12A. Halaman produk memuat angka tegangan yang tidak sepenuhnya konsisten, sehingga angka torsi pada tegangan lebih tinggi tidak dijadikan dasar desain.

## Ketidakcocokan yang memengaruhi desain

WidowX MKII pabrikan memakai kombinasi MX-64, MX-28, dan AX-12. Menggunakan AX-12A untuk semua sendi merupakan perubahan desain, bukan penggantian langsung yang sudah tervalidasi. Identitas setiap servo dalam STL belum dipetakan secara pasti.

| Servo | Dimensi W × H × D menurut ROBOTIS | Stall torque pada 12 V |
| --- | --- | --- |
| AX-12A | 32 × 50 × 40 mm | 1,5 N·m |
| MX-28 | 35,6 × 50,6 × 35,5 mm | 2,5 N·m |
| MX-64 | 40,2 × 61,1 × 41 mm | 6,0 N·m |

Dimensi luar bukan spesifikasi lengkap dudukan. Posisi lubang, horn, dukungan poros, akses baut, dan ruang kabel harus mengikuti drawing servo dan hardware aktual. Jangan mengecilkan seluruh STL secara seragam untuk menyesuaikan servo: jarak lubang dan ukuran bearing/baut juga akan ikut berubah.

ROBOTIS menyarankan perancangan beban AX-12A sekitar seperlima atau kurang dari stall torque untuk gerak stabil. Dengan angka stall pada 12 V, pedoman awal ini setara 0,3 N·m; bukan jaminan continuous torque atau payload robot.

Contoh hitungan statis untuk sendi bahu dengan lengan horizontal:

`tau = g * (massa_payload * jarak_payload + jumlah(massa_komponen * jarak_pusat_massanya))`

Benda 100 gram pada jarak horizontal 30 cm sendiri memerlukan sekitar 0,294 N·m. Massa gripper, servo distal, bracket, dan kabel belum masuk hitungan itu, begitu juga percepatan dan gesekan. Karena itu, kapasitas angkat tidak boleh dihitung dari stall torque saja. Target pertama sekarang tanpa payload; jangkauan final belum ditetapkan.

### Perkiraan awal lengan kosong

Script `mesh_analysis/estimate_empty_arm.py` membandingkan dua rantai lurus horizontal dengan tiga AX-12A distal dan satu MG90S sebagai massa titik. Hasil tersimpan dalam `mesh_analysis/empty_arm_estimate.json`.

- Panjang rantai referensi WidowX (jarak sumbu dari Xacro): kebutuhan torsi bahu sekitar **0,485 N·m hanya dari servo distal**.
- Skenario studi lebih pendek 60 + 60 + 45 + 35 mm: sekitar **0,211 N·m hanya dari servo distal**.

Keduanya belum memasukkan rangka, jari, horn, kabel, baut, atau dinamika. Posisi pusat massa dianggap berada pada sumbu sendi, bukan hasil pengukuran assembly. Angka ini untuk membandingkan arah desain, bukan prediksi kinerja final. Geometri pendek juga belum diperiksa terhadap benturan antarbodi servo dan ruang pemasangan. Hasil menunjukkan alasan untuk memperpendek lengan atau memakai penyeimbang bila semua sendi memakai AX-12A; menyalin panjang WidowX langsung tidak layak diasumsikan berhasil hanya karena payload nol.

## Implikasi pencetakan

PLA dan nozzle 0,4 mm dapat dipakai untuk prototipe pasang dan pemeriksaan gerak, tetapi tidak membuktikan bahwa geometri bracket aluminium asli cukup kuat bila dicetak. Suhu sekitar servo, arah lapisan, ketebalan penampang, dan berat rangka harus diperhitungkan.

Untuk kupon uji dudukan, titik awal yang diusulkan adalah layer 0,20 mm dan 4 perimeter, dengan profil suhu/kecepatan PLA yang telah dikalibrasi pada printer pengguna. Ini usulan uji awal, bukan profil final untuk seluruh rangka. Celah pasang dan lubang baut perlu dikalibrasi menggunakan kupon sebelum mencetak part lengkap. Ketebalan dan infill rangka final dipilih setelah beban dan orientasi cetak diketahui.

Hasil ekstraksi 82 STL belum diubah untuk AX-12A dan belum dinyatakan siap cetak. Rincian mesh dan file pratinjau tersedia di `mesh_analysis/README.md`.

## Implikasi ROS2

Jika ukuran link atau dudukan berubah, transform sendi dan mesh ROS2 harus mengikuti geometri hasil desain tersebut. AX-12A memiliki rentang posisi nominal 0–300 derajat; batas URDF harus dipetakan terhadap zero mekanis dan dibatasi lagi oleh tabrakan/kabel. Jangan menyalin limit, massa, atau inersia WidowX referensi tanpa pemeriksaan.

## Pilihan servo gripper

Servo hobi dapat digunakan jika dudukan horn, linkage, rentang gerak, dan catu dayanya didesain sesuai model servo yang dipilih. "SG/MG" bukan spesifikasi model yang cukup untuk memastikan kecocokan. Label "25 kg" pada servo biasanya mengacu pada 25 kgf·cm, sekitar 2,45 N·m; nilai torsi serta tegangan pengukurannya tetap harus diperiksa pada datasheet. Angka itu bukan kapasitas angkat 25 kg.

Gripper yang lebih berat meningkatkan torsi gravitasi pada bahu dan siku. Sebagai ilustrasi, tambahan massa 50 gram pada jarak horizontal 30 cm menambah sekitar 0,147 N·m di bahu. Itu sudah hampir setengah pedoman awal 0,3 N·m AX-12A di atas. Memilih servo gripper terbesar tanpa kebutuhan gaya jepit yang jelas dapat mengurangi kemampuan lengan membawa benda.

Gaya jepit dipengaruhi radius horn/linkage, posisi mekanisme, efisiensi, dan gesekan bantalan jari terhadap benda. Tidak dapat ditentukan dari label torsi saja.

Jika servo gripper yang dipilih memakai kontrol pulsa/PWM, diperlukan output pengendali yang sesuai; servo itu tidak menerima paket bus TTL DYNAMIXEL secara langsung. Catu daya mengikuti tegangan servo yang dipilih, dengan referensi ground bersama untuk sinyal kontrol. Pada ROS2, driver gripper dan konversi posisi ke bukaan jari harus mengikuti mekanisme aktual. Servo tanpa feedback posisi tidak menyediakan pengukuran posisi hanya dari sinyal perintah.

## Informasi yang masih diperlukan

1. Untuk finalisasi dudukan: ukuran horn, hardware pemasangan dan unit MG90S aktual; jangkauan dapat dipilih berdasarkan kelayakan mekanis.
2. Untuk menjalankan paket simulasi: distribusi ROS2, sistem operasi, dan apakah targetnya visualisasi RViz atau juga simulasi fisika. Hal ini tidak menghalangi studi mekanis.
3. Kontroler, antarmuka bus DYNAMIXEL, dan sumber daya sebelum integrasi hardware. Belum ada perintah gerak yang dijalankan ke motor.

## Sumber spesifikasi

- [ROBOTIS AX-12A](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/)
- [ROBOTIS MX-28](https://emanual.robotis.com/docs/en/dxl/mx/mx-28/)
- [ROBOTIS MX-64](https://emanual.robotis.com/docs/en/dxl/mx/mx-64/)
- [Interbotix: WidowX MKII dan material rangka](https://www.interbotix.com/Robotic-Arms)
- [Prusa: karakteristik PLA](https://help.prusa3d.com/article/pla_2062)
- [TowerPro MG90S](https://towerpro.com.tw/product/mg90s-3/)
