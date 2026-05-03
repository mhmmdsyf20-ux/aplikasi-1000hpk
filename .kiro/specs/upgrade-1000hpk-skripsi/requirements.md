# Requirements Document

## Introduction

Proyek ini merupakan upgrade aplikasi web **1000 Hari Pertama Kehidupan (1000 HPK)** yang sudah ada menjadi aplikasi skripsi lengkap berbasis Flask (Python). Aplikasi saat ini memiliki fitur dasar input data anak, dashboard status imunisasi sederhana, dan halaman edukasi. Upgrade ini mencakup migrasi database dari SQLite ke MySQL, redesign UI modern dengan Bootstrap 5, penambahan notifikasi WhatsApp untuk reminder jadwal imunisasi, visualisasi data dengan Chart.js, serta fitur manajemen lengkap yang layak untuk skripsi (autentikasi, laporan, manajemen data).

Aplikasi ini ditujukan untuk petugas kesehatan (bidan/puskesmas) dan admin dalam memantau tumbuh kembang anak pada periode 1000 HPK, khususnya jadwal imunisasi sesuai standar IDAI.

---

## Glossary

- **Sistem**: Aplikasi web 1000 HPK berbasis Flask
- **Admin**: Pengguna dengan hak akses penuh (manajemen user, laporan, konfigurasi)
- **Petugas**: Pengguna dengan hak akses terbatas (input data anak, lihat dashboard, kirim notifikasi)
- **Anak**: Entitas data yang merepresentasikan seorang anak dalam periode 1000 HPK
- **Orang_Tua**: Wali atau orang tua anak yang menerima notifikasi WhatsApp
- **Jadwal_Imunisasi**: Daftar vaksin beserta usia pemberian sesuai standar IDAI
- **Imunisasi**: Catatan pemberian vaksin pada seorang anak
- **Notifikasi**: Pesan WhatsApp yang dikirim kepada Orang_Tua sebagai pengingat jadwal imunisasi
- **Dashboard**: Halaman utama yang menampilkan ringkasan data dan grafik
- **Laporan**: Dokumen rekap data imunisasi yang dapat diekspor
- **Auth_Module**: Modul autentikasi yang menangani login, logout, dan manajemen sesi
- **WA_Gateway**: Layanan pengiriman pesan WhatsApp (Fonnte atau Twilio WhatsApp API)
- **Chart_Module**: Modul visualisasi data menggunakan Chart.js
- **DB_Module**: Modul koneksi dan operasi database MySQL menggunakan SQLAlchemy
- **HPK**: Hari Pertama Kehidupan — periode 1000 hari sejak konsepsi hingga usia 2 tahun
- **IDAI**: Ikatan Dokter Anak Indonesia — standar jadwal imunisasi nasional

---

## Requirements

### Requirement 1: Migrasi Database ke MySQL

**User Story:** Sebagai Admin, saya ingin database aplikasi menggunakan MySQL agar data lebih aman, skalabel, dan siap untuk lingkungan produksi skripsi.

#### Acceptance Criteria

1. THE DB_Module SHALL menggunakan MySQL sebagai database utama menggantikan SQLite, dengan koneksi melalui SQLAlchemy.
2. THE DB_Module SHALL menyediakan tabel `users` dengan kolom: `id`, `username`, `password_hash`, `role` (admin/petugas), `nama_lengkap`, `created_at`.
3. THE DB_Module SHALL menyediakan tabel `anak` dengan kolom: `id`, `nama`, `tanggal_lahir`, `jenis_kelamin`, `nama_ibu`, `no_hp_ortu`, `alamat`, `berat_lahir`, `panjang_lahir`, `created_by`, `created_at`.
4. THE DB_Module SHALL menyediakan tabel `imunisasi` dengan kolom: `id`, `anak_id`, `nama_vaksin`, `tanggal_jadwal`, `tanggal_realisasi`, `status` (terjadwal/selesai/terlewat), `catatan`, `petugas_id`.
5. THE DB_Module SHALL menyediakan tabel `notifikasi_log` dengan kolom: `id`, `anak_id`, `pesan`, `no_tujuan`, `status_kirim`, `waktu_kirim`.
6. WHEN aplikasi pertama kali dijalankan, THE DB_Module SHALL membuat semua tabel secara otomatis jika belum ada menggunakan `db.create_all()`.
7. IF koneksi ke MySQL gagal, THEN THE DB_Module SHALL menampilkan pesan error yang deskriptif dan menghentikan startup aplikasi.
8. THE DB_Module SHALL membaca konfigurasi koneksi MySQL (host, port, user, password, database name) dari file `.env` menggunakan `python-dotenv`.

---

### Requirement 2: Autentikasi Pengguna (Admin & Petugas)

**User Story:** Sebagai Admin, saya ingin sistem memiliki autentikasi agar hanya pengguna terdaftar yang dapat mengakses dan mengelola data anak.

#### Acceptance Criteria

1. THE Auth_Module SHALL menyediakan halaman login dengan form username dan password.
2. WHEN pengguna memasukkan username dan password yang valid, THE Auth_Module SHALL membuat sesi login dan mengarahkan pengguna ke Dashboard.
3. IF pengguna memasukkan username atau password yang salah, THEN THE Auth_Module SHALL menampilkan pesan "Username atau password salah" tanpa mengungkap informasi mana yang salah.
4. THE Auth_Module SHALL menyimpan password dalam bentuk hash menggunakan `werkzeug.security` (bcrypt-based), bukan plaintext.
5. WHILE pengguna belum login, THE Sistem SHALL mengarahkan semua akses ke halaman yang dilindungi menuju halaman login.
6. WHEN pengguna menekan tombol logout, THE Auth_Module SHALL menghapus sesi dan mengarahkan ke halaman login.
7. THE Auth_Module SHALL membedakan hak akses: Admin dapat mengakses manajemen user dan laporan, Petugas hanya dapat mengakses data anak dan notifikasi.
8. IF pengguna dengan role Petugas mencoba mengakses halaman Admin, THEN THE Auth_Module SHALL menampilkan halaman error 403 Forbidden.
9. THE Auth_Module SHALL menyediakan fitur manajemen user oleh Admin: tambah, edit, nonaktifkan akun Petugas.

---

### Requirement 3: Manajemen Data Anak

**User Story:** Sebagai Petugas, saya ingin mengelola data anak secara lengkap agar informasi yang tersimpan cukup untuk keperluan pemantauan 1000 HPK.

#### Acceptance Criteria

1. THE Sistem SHALL menyediakan form input data anak dengan field: nama lengkap, tanggal lahir, jenis kelamin, nama ibu, nomor HP orang tua (format Indonesia: 08xx atau +62xx), alamat, berat lahir (gram), panjang lahir (cm).
2. WHEN Petugas menyimpan data anak baru, THE Sistem SHALL memvalidasi bahwa semua field wajib (nama, tanggal lahir, jenis kelamin, nama ibu, no HP) terisi sebelum menyimpan ke database.
3. IF nomor HP orang tua tidak sesuai format Indonesia (diawali 08 atau +62, panjang 10–15 digit), THEN THE Sistem SHALL menampilkan pesan validasi "Format nomor HP tidak valid".
4. THE Sistem SHALL menyediakan halaman daftar anak dengan fitur pencarian berdasarkan nama anak atau nama ibu.
5. THE Sistem SHALL menyediakan fitur edit data anak untuk memperbaiki informasi yang sudah tersimpan.
6. WHEN data anak baru disimpan, THE Sistem SHALL secara otomatis membuat jadwal imunisasi awal berdasarkan tanggal lahir sesuai standar IDAI (BCG, Hepatitis B, Polio 0, DPT-HB-Hib 1-3, Campak, dll).
7. THE Sistem SHALL menghitung dan menampilkan umur anak dalam hari dan bulan secara otomatis berdasarkan tanggal lahir.
8. IF anak berusia lebih dari 730 hari (2 tahun), THEN THE Sistem SHALL menandai anak tersebut sebagai "Melewati periode 1000 HPK".

---

### Requirement 4: Manajemen Jadwal Imunisasi IDAI

**User Story:** Sebagai Petugas, saya ingin sistem mengelola jadwal imunisasi sesuai standar IDAI agar pemantauan imunisasi anak akurat dan terstruktur.

#### Acceptance Criteria

1. THE Sistem SHALL menyimpan jadwal imunisasi IDAI lengkap sebagai referensi, mencakup minimal: BCG (0 hari), Hepatitis B (0 hari), Polio 0 (0 hari), DPT-HB-Hib 1 (60 hari), DPT-HB-Hib 2 (120 hari), DPT-HB-Hib 3 (180 hari), Polio 1-4 (60, 120, 180, 270 hari), Campak/MR (270 hari), Booster DPT (540 hari), Booster Campak (540 hari).
2. WHEN data anak baru disimpan, THE Sistem SHALL membuat entri jadwal imunisasi untuk setiap vaksin IDAI dengan tanggal jadwal = tanggal lahir + offset hari vaksin.
3. WHEN Petugas menandai imunisasi sebagai selesai, THE Sistem SHALL menyimpan tanggal realisasi dan mengubah status menjadi "selesai".
4. WHEN tanggal jadwal imunisasi telah lewat dan status masih "terjadwal", THE Sistem SHALL mengubah status menjadi "terlewat" secara otomatis saat halaman dashboard dibuka.
5. THE Sistem SHALL menampilkan daftar imunisasi per anak dengan status visual: terjadwal (biru), selesai (hijau), terlewat (merah).
6. THE Sistem SHALL menampilkan imunisasi yang jatuh tempo dalam 7 hari ke depan sebagai "Imunisasi Mendatang" di dashboard.

---

### Requirement 5: UI Modern dengan Bootstrap 5

**User Story:** Sebagai Petugas, saya ingin tampilan aplikasi modern dan responsif agar nyaman digunakan di berbagai perangkat termasuk smartphone.

#### Acceptance Criteria

1. THE Sistem SHALL menggunakan Bootstrap 5 sebagai framework CSS utama untuk semua halaman.
2. THE Sistem SHALL menyediakan sidebar navigasi yang responsif dengan menu: Dashboard, Data Anak, Jadwal Imunisasi, Notifikasi, Edukasi, Laporan (khusus Admin).
3. THE Sistem SHALL menampilkan kartu ringkasan (summary cards) di Dashboard: total anak terdaftar, imunisasi hari ini, imunisasi mendatang (7 hari), imunisasi terlewat.
4. THE Sistem SHALL menggunakan warna yang konsisten: hijau untuk status selesai, kuning/oranye untuk mendatang, merah untuk terlewat, biru untuk informasi umum.
5. THE Sistem SHALL menampilkan tabel data dengan fitur sorting dan pagination (10 baris per halaman default).
6. THE Sistem SHALL berfungsi dengan baik pada layar dengan lebar minimal 320px (mobile) hingga 1920px (desktop).
7. THE Sistem SHALL menampilkan notifikasi toast/flash message setelah operasi berhasil atau gagal (simpan data, kirim notifikasi, dll).

---

### Requirement 6: Visualisasi Data dengan Chart.js

**User Story:** Sebagai Admin, saya ingin melihat grafik dan statistik imunisasi agar dapat memantau cakupan imunisasi secara visual dan membuat keputusan berbasis data.

#### Acceptance Criteria

1. THE Chart_Module SHALL menampilkan grafik donut/pie di Dashboard yang menunjukkan proporsi status imunisasi: selesai, terjadwal, terlewat.
2. THE Chart_Module SHALL menampilkan grafik batang (bar chart) yang menunjukkan jumlah imunisasi per bulan dalam 6 bulan terakhir.
3. THE Chart_Module SHALL menampilkan grafik progress imunisasi per anak (persentase vaksin selesai dari total vaksin yang dijadwalkan).
4. WHEN Admin membuka halaman Laporan, THE Chart_Module SHALL menampilkan grafik cakupan imunisasi per jenis vaksin (persentase anak yang sudah mendapat vaksin tertentu).
5. THE Chart_Module SHALL memperbarui data grafik secara otomatis setiap kali halaman dimuat tanpa memerlukan refresh manual.
6. THE Chart_Module SHALL menggunakan Chart.js versi 4.x yang dimuat dari CDN.

---

### Requirement 7: Notifikasi WhatsApp

**User Story:** Sebagai Petugas, saya ingin mengirim reminder jadwal imunisasi via WhatsApp kepada orang tua anak agar mereka tidak melewatkan jadwal imunisasi.

#### Acceptance Criteria

1. THE Sistem SHALL menyediakan halaman Notifikasi yang menampilkan daftar anak dengan imunisasi yang jatuh tempo dalam 7 hari ke depan.
2. WHEN Petugas menekan tombol "Kirim Notifikasi" untuk satu anak, THE WA_Gateway SHALL mengirim pesan WhatsApp ke nomor HP orang tua anak tersebut.
3. THE WA_Gateway SHALL mengirim pesan dengan format: "Yth. Orang tua [nama anak], jadwal imunisasi [nama vaksin] pada [tanggal] sudah mendekat. Harap datang ke [nama fasilitas]. Info: 1000HPK App."
4. WHEN Petugas menekan tombol "Kirim Semua", THE WA_Gateway SHALL mengirim notifikasi ke semua orang tua yang anaknya memiliki jadwal imunisasi dalam 7 hari ke depan.
5. IF pengiriman pesan WhatsApp gagal (API error, nomor tidak valid), THEN THE WA_Gateway SHALL mencatat kegagalan di tabel `notifikasi_log` dengan status "gagal" dan pesan error.
6. WHEN notifikasi berhasil dikirim, THE Sistem SHALL mencatat log pengiriman di tabel `notifikasi_log` dengan status "terkirim" dan waktu pengiriman.
7. THE Sistem SHALL membaca konfigurasi WA_Gateway (API key, nomor pengirim) dari file `.env`.
8. THE Sistem SHALL mendukung dua pilihan WA_Gateway yang dapat dikonfigurasi: Fonnte (lokal/Indonesia) atau Twilio WhatsApp API.
9. WHEN Petugas membuka halaman Notifikasi, THE Sistem SHALL menampilkan riwayat 20 notifikasi terakhir yang dikirim beserta statusnya.

---

### Requirement 8: Laporan dan Ekspor Data

**User Story:** Sebagai Admin, saya ingin mengekspor laporan data imunisasi agar dapat digunakan untuk pelaporan ke dinas kesehatan atau keperluan skripsi.

#### Acceptance Criteria

1. THE Sistem SHALL menyediakan halaman Laporan yang hanya dapat diakses oleh Admin.
2. WHEN Admin memilih rentang tanggal dan menekan "Generate Laporan", THE Sistem SHALL menampilkan tabel rekap imunisasi sesuai filter tanggal.
3. THE Sistem SHALL menyediakan tombol ekspor laporan ke format PDF menggunakan library `reportlab` atau `weasyprint`.
4. THE Sistem SHALL menyediakan tombol ekspor laporan ke format Excel (.xlsx) menggunakan library `openpyxl`.
5. THE Laporan SHALL mencakup kolom: nama anak, tanggal lahir, umur (bulan), nama vaksin, tanggal jadwal, tanggal realisasi, status, nama petugas.
6. THE Sistem SHALL menampilkan ringkasan statistik di halaman Laporan: total anak, total imunisasi selesai, total imunisasi terlewat, persentase cakupan.

---

### Requirement 9: Halaman Edukasi 1000 HPK (Upgrade)

**User Story:** Sebagai Petugas, saya ingin halaman edukasi yang lebih lengkap dan informatif agar dapat digunakan sebagai referensi edukasi kepada orang tua.

#### Acceptance Criteria

1. THE Sistem SHALL menampilkan konten edukasi 1000 HPK yang terstruktur dalam kategori: Nutrisi Ibu Hamil, ASI Eksklusif, MPASI, Imunisasi, Stimulasi Tumbuh Kembang.
2. THE Sistem SHALL menampilkan timeline visual periode 1000 HPK (0–270 hari kehamilan, 0–365 hari usia 0-1 tahun, 366–730 hari usia 1-2 tahun).
3. THE Sistem SHALL menyematkan video edukasi dari YouTube menggunakan iframe yang responsif.
4. THE Sistem SHALL menampilkan tabel jadwal imunisasi IDAI lengkap sebagai referensi yang dapat dicetak.

---

### Requirement 10: Keamanan dan Konfigurasi Aplikasi

**User Story:** Sebagai Admin, saya ingin aplikasi memiliki keamanan dasar yang memadai agar data anak terlindungi dari akses tidak sah.

#### Acceptance Criteria

1. THE Sistem SHALL menggunakan `SECRET_KEY` Flask yang kuat (minimal 32 karakter acak) yang dibaca dari file `.env`.
2. THE Sistem SHALL menggunakan CSRF protection pada semua form menggunakan `Flask-WTF`.
3. THE Sistem SHALL membatasi ukuran upload file maksimal 5MB jika fitur upload foto anak ditambahkan di masa depan.
4. THE Sistem SHALL menyediakan file `.env.example` sebagai template konfigurasi tanpa nilai sensitif.
5. THE Sistem SHALL menyertakan file `.gitignore` yang mengecualikan `.env`, `__pycache__`, dan file database lokal.
6. IF sesi pengguna tidak aktif selama lebih dari 60 menit, THEN THE Auth_Module SHALL secara otomatis menghapus sesi dan mengarahkan ke halaman login.
