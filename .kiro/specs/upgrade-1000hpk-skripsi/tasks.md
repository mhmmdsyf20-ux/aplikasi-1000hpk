# Implementation Plan: Upgrade Aplikasi 1000 HPK Skripsi

## Overview

Rencana implementasi ini mengkonversi desain teknis upgrade aplikasi 1000 HPK menjadi langkah-langkah coding yang inkremental. Dimulai dari fondasi (struktur proyek, konfigurasi, model database), kemudian membangun setiap Blueprint secara berurutan, dan diakhiri dengan integrasi penuh. Setiap task membangun di atas task sebelumnya sehingga tidak ada kode yang tergantung (orphaned).

Stack: **Python 3.10+, Flask 3.x, SQLAlchemy 2.x, MySQL 8.x, Bootstrap 5.3, Chart.js 4.x**

---

## Tasks

- [x] 1. Setup struktur proyek, konfigurasi, dan fondasi aplikasi
  - Buat struktur direktori lengkap sesuai desain: `models/`, `blueprints/`, `services/`, `templates/`, `static/`, `tests/`
  - Buat `requirements.txt` dengan semua dependensi yang diperlukan (Flask 3.x, Flask-SQLAlchemy, Flask-Login, Flask-WTF, PyMySQL, python-dotenv, openpyxl, WeasyPrint/ReportLab, Hypothesis, pytest, pytest-flask)
  - Buat `config.py` yang membaca semua variabel dari `.env` (SECRET_KEY, DB_*, WA_GATEWAY, NAMA_FASILITAS)
  - Buat `extensions.py` untuk inisialisasi `db`, `login_manager`, dan `csrf`
  - Buat `app.py` baru sebagai application factory (`create_app()`) dengan registrasi semua Blueprint dan error handlers (403, 404, 500)
  - Buat `.env.example` dengan semua key yang diperlukan tanpa nilai sensitif
  - Buat `.gitignore` yang mengecualikan `.env`, `__pycache__`, `*.pyc`, file database lokal
  - _Requirements: 1.8, 10.1, 10.4, 10.5_

- [ ] 2. Implementasi model database (SQLAlchemy ORM)
  - [x] 2.1 Buat model `User` di `models/user.py`
    - Implementasi class `User(db.Model, UserMixin)` dengan semua kolom sesuai ERD
    - Implementasi method `set_password()` dan `check_password()` menggunakan `werkzeug.security`
    - _Requirements: 1.2, 2.4_

  - [ ] 2.2 Tulis property test untuk password hashing (Property 1)
    - **Property 1: Password hashing adalah round-trip yang aman**
    - **Validates: Requirements 2.4**

  - [x] 2.3 Buat model `Anak` di `models/anak.py`
    - Implementasi class `Anak(db.Model)` dengan semua kolom sesuai ERD
    - Implementasi property `umur_hari`, `umur_bulan`, dan `melewati_1000hpk`
    - _Requirements: 1.3, 3.7, 3.8_

  - [ ] 2.4 Tulis property test untuk kalkulasi umur dan flag 1000 HPK (Property 8)
    - **Property 8: Kalkulasi umur anak dan flag 1000 HPK**
    - **Validates: Requirements 3.7, 3.8**

  - [x] 2.5 Buat model `Imunisasi` di `models/imunisasi.py`
    - Implementasi class `Imunisasi(db.Model)` dengan semua kolom sesuai ERD
    - _Requirements: 1.4_

  - [x] 2.6 Buat model `NotifikasiLog` di `models/notifikasi_log.py`
    - Implementasi class `NotifikasiLog(db.Model)` dengan semua kolom sesuai ERD termasuk `error_message`
    - _Requirements: 1.5_

  - [x] 2.7 Buat `models/__init__.py` yang mengekspor semua model
    - Pastikan `db.create_all()` dapat membuat semua tabel secara otomatis
    - Tambahkan penanganan error koneksi MySQL yang deskriptif di `app.py`
    - _Requirements: 1.1, 1.6, 1.7_

  - [x] 2.8 Tulis unit tests untuk semua model di `tests/test_smoke.py`
    - Verifikasi skema tabel, relasi FK, dan nilai default
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [-] 3. Implementasi autentikasi (Auth Blueprint)
  - [x] 3.1 Buat `blueprints/auth/routes.py` dengan route login dan logout
    - Implementasi GET/POST `/login` dengan form username dan password
    - Implementasi GET `/logout` yang menghapus sesi dan redirect ke login
    - Konfigurasi `PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)` untuk session timeout
    - _Requirements: 2.1, 2.2, 2.6, 10.6_

  - [x] 3.2 Buat `services/auth_service.py`
    - Implementasi fungsi autentikasi yang memverifikasi username dan password
    - Implementasi custom decorator `@role_required('admin')` untuk proteksi route
    - Konfigurasi `login_manager.unauthorized_handler` untuk redirect ke login
    - _Requirements: 2.3, 2.5, 2.7, 2.8_

  - [ ] 3.3 Tulis property test untuk kredensial yang salah (Property 2)
    - **Property 2: Kredensial yang salah selalu ditolak**
    - **Validates: Requirements 2.3**

  - [ ] 3.4 Tulis property test untuk proteksi route tanpa autentikasi (Property 3)
    - **Property 3: Semua route yang dilindungi mengarahkan ke login jika belum autentikasi**
    - **Validates: Requirements 2.5**

  - [ ] 3.5 Tulis property test untuk akses kontrol role (Property 4)
    - **Property 4: Akses kontrol role — Petugas tidak dapat mengakses route Admin**
    - **Validates: Requirements 2.7, 2.8**

  - [x] 3.6 Buat route manajemen user Admin di `blueprints/auth/routes.py`
    - Implementasi GET/POST `/admin/users` untuk daftar dan tambah user
    - Implementasi GET/POST `/admin/users/<id>/edit` untuk edit dan nonaktifkan user
    - Proteksi semua route dengan `@role_required('admin')`
    - _Requirements: 2.9_

  - [x] 3.7 Tulis unit tests autentikasi di `tests/test_auth.py`
    - Test login berhasil, login gagal, logout, session timeout, akses 403
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 2.7, 2.8_

- [x] 4. Checkpoint — Pastikan semua tests lulus
  - Pastikan semua tests lulus, tanyakan kepada user jika ada pertanyaan.

- [ ] 5. Implementasi manajemen data anak (Anak Blueprint)
  - [x] 5.1 Buat `services/anak_service.py` dengan validasi dan logika bisnis
    - Implementasi fungsi `validate_hp()` dengan regex pattern `^(\+62|08)\d{8,13}$`
    - Implementasi fungsi `validate_anak_data()` yang memvalidasi semua field wajib
    - _Requirements: 3.2, 3.3_

  - [ ] 5.2 Tulis property test untuk validasi nomor HP Indonesia (Property 5)
    - **Property 5: Validasi nomor HP Indonesia**
    - **Validates: Requirements 3.3**

  - [ ] 5.3 Tulis property test untuk validasi field wajib data anak (Property 6)
    - **Property 6: Validasi field wajib data anak**
    - **Validates: Requirements 3.2**

  - [x] 5.4 Buat `blueprints/anak/routes.py` dengan CRUD lengkap
    - Implementasi GET `/anak` dengan fitur pencarian (nama anak/nama ibu) dan pagination (10 per halaman)
    - Implementasi GET/POST `/anak/tambah` dengan form lengkap dan validasi server-side
    - Implementasi GET/POST `/anak/<id>/edit` untuk edit data anak
    - Implementasi GET `/anak/<id>` untuk detail anak beserta daftar imunisasi
    - Tampilkan umur anak (hari dan bulan) dan flag "Melewati periode 1000 HPK" jika berlaku
    - _Requirements: 3.1, 3.4, 3.5, 3.7, 3.8_

  - [ ] 5.5 Tulis unit tests CRUD anak di `tests/test_anak.py`
    - Test tambah anak berhasil, validasi gagal, edit data, pencarian, pagination
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 6. Implementasi jadwal imunisasi IDAI (Imunisasi Blueprint)
  - [x] 6.1 Buat `services/imunisasi_service.py` dengan konstanta dan logika jadwal IDAI
    - Definisikan konstanta `JADWAL_IDAI` dengan 13 vaksin dan offset hari sesuai desain
    - Implementasi fungsi `generate_jadwal_imunisasi(tanggal_lahir)` yang membuat 13 entri `Imunisasi`
    - Integrasikan pemanggilan `generate_jadwal_imunisasi()` ke dalam route tambah anak (task 5.4)
    - _Requirements: 3.6, 4.1, 4.2_

  - [ ] 6.2 Tulis property test untuk auto-generate jadwal IDAI (Property 7)
    - **Property 7: Auto-generate jadwal imunisasi IDAI sesuai tanggal lahir**
    - **Validates: Requirements 3.6, 4.1, 4.2**

  - [x] 6.3 Implementasi fungsi update status imunisasi di `services/imunisasi_service.py`
    - Implementasi fungsi `tandai_selesai(imunisasi_id, tanggal_realisasi, petugas_id)` yang mengubah status ke `selesai`
    - Implementasi fungsi `update_status_terlewat()` yang mengubah status `terjadwal` yang sudah lewat menjadi `terlewat`
    - Implementasi fungsi `get_imunisasi_mendatang(days=7)` yang mengembalikan imunisasi dalam 7 hari ke depan
    - _Requirements: 4.3, 4.4, 4.6_

  - [ ] 6.4 Tulis property test untuk state transition imunisasi selesai (Property 9)
    - **Property 9: State transition imunisasi — tandai selesai**
    - **Validates: Requirements 4.3**

  - [ ] 6.5 Tulis property test untuk state transition imunisasi terlewat (Property 10)
    - **Property 10: State transition imunisasi — otomatis terlewat**
    - **Validates: Requirements 4.4**

  - [ ] 6.6 Tulis property test untuk filter imunisasi mendatang (Property 11)
    - **Property 11: Filter imunisasi mendatang (7 hari)**
    - **Validates: Requirements 4.6, 7.1**

  - [x] 6.7 Buat `blueprints/imunisasi/routes.py`
    - Implementasi GET `/imunisasi` dengan filter status (terjadwal/selesai/terlewat)
    - Implementasi POST `/imunisasi/<id>/selesai` yang memanggil `tandai_selesai()`
    - Implementasi GET `/imunisasi/mendatang` yang memanggil `get_imunisasi_mendatang()`
    - Panggil `update_status_terlewat()` saat dashboard dibuka
    - _Requirements: 4.3, 4.4, 4.5, 4.6_

  - [ ] 6.8 Tulis unit tests imunisasi di `tests/test_imunisasi.py`
    - Test generate jadwal, tandai selesai, update terlewat, filter mendatang
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 7. Checkpoint — Pastikan semua tests lulus
  - Pastikan semua tests lulus, tanyakan kepada user jika ada pertanyaan.

- [ ] 8. Implementasi notifikasi WhatsApp (Notifikasi Blueprint)
  - [x] 8.1 Buat `services/wa_service.py` dengan interface WAService
    - Implementasi class `WAService` dengan method `kirim_pesan(no_tujuan, pesan) -> dict`
    - Implementasi fungsi `format_pesan_wa(nama_anak, nama_vaksin, tanggal, nama_fasilitas) -> str`
    - Implementasi dukungan dua provider: Fonnte (default) dan Twilio WhatsApp API, dikonfigurasi via `.env`
    - Tangani error API (timeout, 4xx, 5xx) dan catat ke `NotifikasiLog` dengan `status_kirim='gagal'`
    - _Requirements: 7.2, 7.3, 7.5, 7.7, 7.8_

  - [ ] 8.2 Tulis property test untuk format pesan WhatsApp (Property 12)
    - **Property 12: Format pesan WhatsApp mengandung semua komponen wajib**
    - **Validates: Requirements 7.3**

  - [ ] 8.3 Tulis property test untuk konsistensi log notifikasi (Property 13)
    - **Property 13: Log notifikasi selalu konsisten dengan hasil pengiriman**
    - **Validates: Requirements 7.5, 7.6**

  - [x] 8.4 Buat `blueprints/notifikasi/routes.py`
    - Implementasi GET `/notifikasi` yang menampilkan daftar anak dengan jadwal mendatang dan riwayat 20 log terakhir
    - Implementasi POST `/notifikasi/kirim/<anak_id>` untuk kirim ke satu anak
    - Implementasi POST `/notifikasi/kirim-semua` untuk kirim ke semua anak dengan jadwal 7 hari ke depan
    - Catat setiap pengiriman (berhasil/gagal) ke `NotifikasiLog`
    - _Requirements: 7.1, 7.2, 7.4, 7.6, 7.9_

  - [ ] 8.5 Tulis property test untuk riwayat notifikasi dibatasi 20 entri (Property 14)
    - **Property 14: Riwayat notifikasi dibatasi 20 entri terbaru**
    - **Validates: Requirements 7.9**

  - [ ] 8.6 Tulis unit tests notifikasi di `tests/test_notifikasi.py`
    - Test kirim satu, kirim semua, log berhasil, log gagal (mock WA API)
    - _Requirements: 7.1, 7.2, 7.4, 7.5, 7.6, 7.9_

- [ ] 9. Implementasi laporan dan ekspor (Laporan Blueprint)
  - [x] 9.1 Buat `services/laporan_service.py` dengan logika filter dan statistik
    - Implementasi fungsi `get_laporan(start_date, end_date)` yang memfilter imunisasi berdasarkan rentang tanggal
    - Implementasi fungsi `get_statistik()` yang menghitung total anak, selesai, terlewat, dan persentase cakupan
    - Implementasi fungsi `hitung_progress_anak(anak_id)` yang menghitung persentase vaksin selesai per anak
    - _Requirements: 8.2, 8.6_

  - [ ] 9.2 Tulis property test untuk filter laporan berdasarkan rentang tanggal (Property 15)
    - **Property 15: Filter laporan berdasarkan rentang tanggal**
    - **Validates: Requirements 8.2**

  - [ ] 9.3 Tulis property test untuk statistik laporan akurat (Property 17)
    - **Property 17: Statistik laporan akurat**
    - **Validates: Requirements 8.6**

  - [ ] 9.4 Tulis property test untuk persentase progress imunisasi per anak (Property 18)
    - **Property 18: Persentase progress imunisasi per anak akurat**
    - **Validates: Requirements 6.3**

  - [x] 9.5 Buat `blueprints/laporan/routes.py` dengan ekspor PDF dan Excel
    - Implementasi GET `/laporan` (Admin only) dengan form filter tanggal dan tabel rekap
    - Implementasi GET `/laporan/export/pdf` yang menghasilkan file PDF menggunakan WeasyPrint/ReportLab
    - Implementasi GET `/laporan/export/excel` yang menghasilkan file `.xlsx` menggunakan openpyxl
    - Pastikan laporan mengandung semua kolom: nama anak, tanggal lahir, umur (bulan), nama vaksin, tanggal jadwal, tanggal realisasi, status, nama petugas
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 9.6 Tulis property test untuk kolom laporan lengkap (Property 16)
    - **Property 16: Laporan mengandung semua kolom yang diperlukan**
    - **Validates: Requirements 8.5**

  - [ ] 9.7 Tulis unit tests laporan di `tests/test_laporan.py`
    - Test filter tanggal, statistik, ekspor PDF, ekspor Excel
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 10. Checkpoint — Pastikan semua tests lulus
  - Pastikan semua tests lulus, tanyakan kepada user jika ada pertanyaan.

- [x] 11. Implementasi template HTML dengan Bootstrap 5
  - [x] 11.1 Buat `templates/base.html` sebagai layout utama
    - Implementasi sidebar responsif Bootstrap 5.3 dengan menu: Dashboard, Data Anak, Jadwal Imunisasi, Notifikasi, Edukasi, Laporan (khusus Admin)
    - Implementasi flash message sebagai toast/alert Bootstrap
    - Sertakan CDN Bootstrap 5.3 dan Chart.js 4.x
    - _Requirements: 5.1, 5.2, 5.7_

  - [x] 11.2 Buat template halaman autentikasi di `templates/auth/`
    - Buat `login.html` dengan form username dan password
    - Buat `users.html` untuk daftar user (Admin)
    - Buat `user_form.html` untuk tambah/edit user (Admin)
    - _Requirements: 2.1, 2.9_

  - [x] 11.3 Buat template dashboard di `templates/anak/dashboard.html`
    - Implementasi 4 summary cards: total anak, imunisasi hari ini, imunisasi mendatang (7 hari), imunisasi terlewat
    - Sertakan placeholder canvas untuk donut chart dan bar chart Chart.js
    - Tampilkan daftar imunisasi mendatang 7 hari ke depan
    - _Requirements: 5.3, 5.4, 6.1, 6.2_

  - [x] 11.4 Buat template halaman data anak di `templates/anak/`
    - Buat `list.html` dengan tabel, search bar, dan pagination (10 per halaman)
    - Buat `form.html` untuk tambah/edit anak dengan semua field dan validasi HTML5
    - Buat `detail.html` untuk detail anak dengan tabel imunisasi berwarna (biru/hijau/merah)
    - _Requirements: 3.1, 4.5, 5.5, 5.6_

  - [x] 11.5 Buat template halaman imunisasi, notifikasi, laporan, dan edukasi
    - Buat `templates/imunisasi/list.html` dengan filter status dan warna badge
    - Buat `templates/notifikasi/index.html` dengan daftar anak mendatang dan riwayat log
    - Buat `templates/laporan/index.html` dengan form filter tanggal, tabel rekap, tombol ekspor, dan statistik
    - Buat `templates/edukasi/index.html` dengan konten terstruktur (5 kategori), timeline visual 1000 HPK, iframe YouTube responsif, dan tabel jadwal IDAI
    - Buat `templates/errors/403.html`, `404.html`, `500.html`
    - _Requirements: 4.5, 7.1, 7.9, 8.1, 8.2, 8.5, 8.6, 9.1, 9.2, 9.3, 9.4_

- [ ] 12. Implementasi visualisasi Chart.js
  - [x] 12.1 Buat `static/js/charts.js` dengan semua chart dashboard
    - Implementasi donut chart status imunisasi (selesai/terjadwal/terlewat) menggunakan data dari endpoint JSON
    - Implementasi bar chart imunisasi per bulan (6 bulan terakhir) menggunakan data dari endpoint JSON
    - Gunakan warna konsisten: hijau (#28a745) selesai, kuning (#ffc107) mendatang, merah (#dc3545) terlewat, biru (#007bff) informasi
    - _Requirements: 5.4, 6.1, 6.2, 6.5, 6.6_

  - [x] 12.2 Tambahkan endpoint JSON untuk data chart di blueprint yang sesuai
    - Tambahkan GET `/api/chart/status` yang mengembalikan data donut chart
    - Tambahkan GET `/api/chart/bulanan` yang mengembalikan data bar chart 6 bulan
    - Tambahkan GET `/api/chart/progress/<anak_id>` yang mengembalikan persentase progress per anak
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 12.3 Tambahkan chart cakupan per vaksin di halaman Laporan
    - Implementasi bar chart cakupan imunisasi per jenis vaksin (persentase anak yang sudah mendapat vaksin tertentu)
    - _Requirements: 6.4_

  - [ ] 12.4 Tulis unit tests untuk endpoint JSON chart
    - Verifikasi format response dan akurasi data
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 13. Implementasi CSRF protection dan keamanan
  - [x] 13.1 Aktifkan CSRF protection pada semua form
    - Pastikan `Flask-WTF` CSRF token disertakan di semua form HTML (`{{ form.hidden_tag() }}` atau `{{ csrf_token() }}`)
    - Verifikasi `WTF_CSRF_ENABLED = True` di config
    - _Requirements: 10.2_

  - [ ] 13.2 Tulis property test untuk CSRF protection (Property 19)
    - **Property 19: CSRF protection pada semua route POST**
    - **Validates: Requirements 10.2**

  - [ ] 13.3 Tulis unit tests keamanan di `tests/test_smoke.py`
    - Test SECRET_KEY terbaca dari .env, session timeout, MAX_CONTENT_LENGTH
    - _Requirements: 10.1, 10.3, 10.6_

- [x] 14. Setup testing framework dan `conftest.py`
  - Buat `tests/conftest.py` dengan fixture `app` (SQLite in-memory) dan `client`
  - Buat `tests/test_properties.py` sebagai file utama untuk semua 19 property-based tests (Hypothesis)
  - Buat `tests/integration/` dengan `test_db_connection.py` dan `test_wa_gateway.py`
  - Buat `requirements-test.txt` dengan pytest, hypothesis, pytest-flask, coverage
  - _Requirements: (semua requirements — testing coverage)_

- [ ] 15. Integrasi akhir dan wiring semua komponen
  - [x] 15.1 Pastikan semua Blueprint terdaftar di `create_app()` dengan prefix URL yang benar
    - Daftarkan: `auth_bp`, `anak_bp`, `imunisasi_bp`, `notifikasi_bp`, `laporan_bp`, `edukasi_bp`
    - Pastikan `login_manager.user_loader` terhubung ke model `User`
    - _Requirements: 1.1, 2.5_

  - [x] 15.2 Hubungkan `update_status_terlewat()` ke route dashboard
    - Panggil fungsi update status terlewat setiap kali halaman dashboard dibuka
    - Pastikan summary cards di dashboard menggunakan data real dari database
    - _Requirements: 4.4, 5.3_

  - [x] 15.3 Hubungkan Chart.js dengan endpoint JSON yang sudah dibuat
    - Pastikan `charts.js` memanggil endpoint yang benar dan merender chart saat halaman dimuat
    - _Requirements: 6.1, 6.2, 6.5_

  - [x] 15.4 Verifikasi alur end-to-end melalui automated tests
    - Tulis test smoke end-to-end: login → tambah anak → cek jadwal terbuat → tandai selesai → cek log
    - _Requirements: 3.6, 4.2, 4.3_

  - [ ] 15.5 Tulis integration tests di `tests/integration/`
    - Test koneksi MySQL nyata dan test WA Gateway dengan nomor test
    - _Requirements: 1.1, 7.2, 7.8_

- [x] 16. Checkpoint akhir — Pastikan semua tests lulus
  - Jalankan `pytest tests/ --ignore=tests/integration -v` dan pastikan semua tests lulus.
  - Tanyakan kepada user jika ada pertanyaan sebelum dianggap selesai.

---

## Notes

- Task bertanda `*` bersifat opsional dan dapat dilewati untuk MVP yang lebih cepat
- Setiap task mereferensikan requirements spesifik untuk keterlacakan
- Property-based tests menggunakan **Hypothesis** dengan minimal 100 iterasi per property
- Unit tests menggunakan SQLite in-memory; integration tests memerlukan MySQL nyata
- Semua 19 Correctness Properties dari design.md dicakup oleh sub-task property test
- Jalankan tests dengan: `pytest tests/ --ignore=tests/integration --cov=. --cov-report=html`
- Target coverage: services ≥ 90%, models ≥ 85%, blueprints ≥ 80%, overall ≥ 80%
