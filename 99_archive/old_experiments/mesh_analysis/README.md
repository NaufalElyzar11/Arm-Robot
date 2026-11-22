# Hasil pemisahan model WidowX

STL asli: `../MX-28_Arm-mk2.stl`. File asli tidak diubah.

## File yang bisa dibuka

- `separated_stl/component_001.stl` sampai `component_082.stl`: 82 kelompok mesh terpisah, masih dalam posisi assembly asli.
- `robot_separated.obj`: assembly yang sama dengan 82 objek bernama. Saat impor, pilih pemisahan berdasarkan **object** jika aplikasi menyatukannya.
- `assembly_preview.png`: pratinjau assembly dengan warna kelompok.
- `components_001_028.png`, `components_029_056.png`, `components_057_082.png`: katalog bentuk dan nomor file. Ukuran tampilan tiap kotak disesuaikan sendiri, bukan perbandingan skala.
- `components.csv`: dimensi, posisi, jumlah segitiga, dan hasil pemeriksaan edge setiap kelompok.
- `summary.json` dan `export_validation.json`: ringkasan analisis dan verifikasi ekspor.

## Yang sudah diverifikasi

464.914 segitiga dipisahkan berdasarkan konektivitas titik dengan koordinat persis sama, tanpa toleransi penggabungan atau perbaikan geometri. Semua rekaman segitiga pada 82 STL hasil ekspor sama persis dengan rekaman asal. Jumlah objek dan face OBJ juga cocok. Tidak ada segitiga berluas nol.

69 kelompok memiliki tepat dua segitiga pada setiap edge. Ini hanya pemeriksaan topologi edge, bukan jaminan mesh bebas self-intersection, orientasi normal benar, atau siap cetak. 13 kelompok memiliki edge non-manifold: **002, 003, 005, 010, 016, 029–036**. Tidak ditemukan boundary edge pada pemeriksaan ini.

Satu kelompok mesh tidak otomatis satu part mekanis. Benda yang bersentuhan pada titik identik dapat masuk kelompok yang sama; permukaan terpisah milik satu benda juga dapat menghasilkan kelompok berbeda. ID diurutkan berdasarkan jumlah segitiga, bukan urutan assembly atau link robot.

Ukuran bounding box seluruh model adalah **196,995 × 353,375 × 284,037 satuan STL**. STL tidak menyimpan satuan; jika sumber memakai mm, ini sekitar 197 × 353 × 284 mm. Konfirmasi terhadap ukuran komponen nyata sebelum mencetak atau mengubah skala ke meter.

## Untuk 3D printing

Hasil ekstraksi adalah bahan pemeriksaan, belum paket part siap cetak.

Model mencakup hardware dan elektronik. Dari bentuknya, kelompok 001 tampak sebagai PCB; beberapa kelompok besar lain adalah servo atau assembly servo; 051–058 tampak sebagai baut dan 059–076 sebagai ring. Itu bukan komponen yang perlu diganti dengan hasil cetak.

Kandidat rangka/plat yang dapat diperiksa lebih dulu: **009, 011, 012, 014, 017, 026, 027, 028**. Kelompok **035–038** tampak terkait jari/linkage gripper, tetapi 035–036 memiliki edge non-manifold. Klasifikasi ini berdasarkan pemeriksaan visual, belum dicocokkan dengan BOM pabrikan. Kelompok 005 juga menyerupai rangka, tetapi memiliki banyak edge non-manifold dan memerlukan pemeriksaan lanjutan.

Impor satu STL kandidat ke slicer, konfirmasi skala, kemudian atur orientasi dan letakkan di bed. Posisi XYZ masih mengikuti assembly; orientasi cetak belum dioptimalkan. Periksa lubang, ketebalan, toleransi, dan kecocokan terhadap servo/bearing/baut sebenarnya. Jangan mencetak seluruh assembly sebagai satu benda untuk membuat robot yang dapat dirakit.

WidowX asli menggunakan bracket aluminium dan material lain, sehingga penggantian dengan plastik memerlukan evaluasi geometri dan kekuatan. Jenis printer, bahan, motor yang dipakai, dan target payload diperlukan untuk menentukan adaptasinya.

## Untuk ROS2

STL tetap dapat menjadi mesh visual robot; konversi OBJ atau STEP saja tidak menciptakan sendi. Komponen yang bergerak bersama harus dikelompokkan menjadi link. URDF/Xacro menyimpan hubungan parent-child, posisi dan arah sumbu sendi, serta batas geraknya. Simulasi fisika juga memerlukan model collision, massa, pusat massa, inersia, dan konfigurasi kontrol yang sesuai.

Referensi dari repositori Interbotix sudah diunduh ke `../reference_widowx/`. Folder `widowx_arm_description/meshes` berisi mesh per-link yang jauh lebih sederhana; `urdf/widowx.urdf.xacro` berisi definisi lengan, dan `urdf/widowx_gripper.xacro` definisi gripper. Mesh referensi ini bukan hasil pemisahan STL pengguna dan bukan file manufaktur.

Referensi tersebut **masih paket ROS1/catkin**, belum port ROS2. Xacro mencantumkan massa 1 kg dan inersia diagonal 1 pada sejumlah link; nilai tersebut perlu diganti dengan data fisik yang benar untuk simulasi dinamika. Kecocokan dimensi dengan STL pengguna belum divalidasi. Belum dibuat atau diuji model ROS2 bergerak, Gazebo, atau konfigurasi MoveIt2 pada tahap ini.

## Sumber

- Sumber model yang diberikan pengguna: https://sketchfab.com/3d-models/widowx-mkii-robotic-arm-2270059391764e93aa01ad5d6a3000c1 (halaman tidak berhasil dibaca melalui alat web pada sesi ini).
- Referensi robot: https://github.com/Interbotix/widowx_arm
- Commit referensi yang disimpan: `503dc5d146f5525af97de8165334b6a064b198c8`; daftar file ada di `../reference_widowx/SOURCE.json`. Metadata lisensi BSD dipertahankan dalam `package.xml` referensi.
- Informasi material dan aktuator: https://www.interbotix.com/Robotic-Arms

## Menjalankan ulang

Dengan Python, NumPy, SciPy, dan Matplotlib:

```powershell
python mesh_analysis/inspect_stl.py
python mesh_analysis/export_components.py
```

Script pertama menganalisis topologi; script kedua mengekspor dan memverifikasi mesh serta membuat pratinjau. Tidak ada perbaikan, rescale, atau pemotongan geometri otomatis.
