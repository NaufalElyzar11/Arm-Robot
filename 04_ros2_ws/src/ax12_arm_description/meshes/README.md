# Mesh visual per link

Kosong untuk sementara — URDF memakai bentuk primitif.

Langkah mengisi (Fase 2 / digital twin):
1. Buka `01_design/step/00_FULL_ROBOT_ARM_ASSEMBLY.step` di CAD (FreeCAD/Fusion/Onshape).
2. Kelompokkan part (servo + bracket) per link sesuai tabel sendi di `01_design/README.md`.
3. Pindahkan origin tiap kelompok ke sumbu sendi induknya (frame URDF), arah +Z mengikuti pose nol (lengan tegak).
4. Ekspor STL dalam **meter** (atau mm lalu `scale="0.001 0.001 0.001"`), maks ~50k segitiga per link.
5. Ganti `<geometry><box …/></geometry>` di visual dengan
   `<mesh filename="package://ax12_arm_description/meshes/link2_upper_arm.stl" scale="0.001 0.001 0.001"/>`.
