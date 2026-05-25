# Implementation Plan: Parent Portal — Portal Web untuk Ibu/Orang Tua Anak

## Overview

Implementasi dilakukan secara inkremental dalam 7 tahap: (1) fondasi model & migrasi, (2) service layer, (3) blueprint & decorator, (4) registrasi & guard petugas, (5) templates HTML, (6) tests, dan (7) checkpoint akhir. Setiap tahap menghasilkan kode yang dapat dijalankan dan diverifikasi sebelum melanjutkan ke tahap berikutnya.

Stack: Python 3.10+, Flask 3.x, SQLAlchemy 2.x, MySQL 8.x, Bootstrap 5.3, Hypothesis, pytest.

## Tasks

- [x] 1. Perluasan Model User dan Script Migrasi Database
  - [x] 1.1 Perluas model `User` di `models/user.py`
    - Tambahkan kolom `email = db.Column(db.String(100), unique=True, nullable=True)`
    - Tambahkan kolom `no_whatsapp = db.Column(db.String(20), nullable=True)`
    - Ubah enum `role` dari `("admin", "petugas")` menjadi `("admin", "petugas", "user")`
    - Pastikan docstring diperbarui untuk mencerminkan kolom baru
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Buat script migrasi SQL `migration_portal_ibu.sql` di root project
    - `ALTER TABLE users ADD COLUMN email VARCHAR(100) NULL`
    - `ALTER TABLE users ADD UNIQUE INDEX uq_users_email (email)`
    - `ALTER TABLE users ADD COLUMN no_whatsapp VARCHAR(20) NULL`
    - `ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'petugas', 'user') NOT NULL`
    - Tambahkan komentar instruksi eksekusi di bagian atas file
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Service Layer: `services/portal_service.py`
  - [x] 2.1 Buat file `services/portal_service.py` dengan fungsi-fungsi helper murni (pure functions)
    - Implementasikan `mask_nomor(no_hp: str) -> str` — tampilkan hanya 4 digit terakhir, format `****XXXX`
    - Implementasikan `validate_email_format(email: str) -> bool` — validasi regex RFC 5322 sederhana (tepat satu `@`, karakter non-kosong di kiri, domain valid dengan `.` di kanan)
    - Implementasikan `validate_password(password: str, konfirmasi: str) -> list[str]` — kembalikan list pesan error; kosong jika valid (cek panjang >= 8, cek kecocokan konfirmasi)
    - Implementasikan `validate_no_whatsapp(no_wa: str) -> bool` — valid jika diawali `08` atau `+62`, panjang 10–15 digit
    - Implementasikan `kelompokkan_jadwal(jadwal_list: list, today: date) -> dict` — pure function, kelompokkan ke `mendatang` (terjadwal, H <= T <= H+7), `terjadwal` (terjadwal, T > H+7), `riwayat` (selesai atau terlewat)
    - Implementasikan `hitung_persentase_imunisasi(anak_id: int) -> float` — query DB, kembalikan float dalam [0.0, 100.0], kembalikan 0.0 jika tidak ada jadwal
    - _Requirements: 2.3, 2.6, 2.9, 4.4, 6.4, 7.2_

  - [x] 2.2 Tambahkan fungsi-fungsi query database ke `services/portal_service.py`
    - Implementasikan `get_anak_by_ibu(user_id: int) -> list` — query `Anak.query.filter_by(created_by=user_id).order_by(Anak.nama).all()`, bungkus dalam try-except, kembalikan `[]` jika error
    - Implementasikan `get_anak_or_403(anak_id: int, user_id: int) -> Anak` — query dengan filter `id=anak_id, created_by=user_id`; jika tidak ditemukan panggil `abort(403)` (bukan 404)
    - Implementasikan `get_jadwal_anak(anak_id: int, user_id: int) -> dict` — validasi kepemilikan via `get_anak_or_403`, query semua imunisasi, kelompokkan via `kelompokkan_jadwal`, hitung statistik; kembalikan dict dengan kunci `anak`, `mendatang`, `terjadwal`, `riwayat`, `total`, `selesai`, `persen`
    - Implementasikan `get_notifikasi_ibu(user_id: int, limit: int = 20) -> list` — ambil notifikasi untuk semua anak milik `user_id`, urutkan `waktu_kirim DESC`, batasi `limit`
    - Implementasikan `get_dashboard_stats(user_id: int) -> dict` — hitung `total_anak`, `total_selesai`, `total_mendatang`, `total_terlewat`, `jadwal_mendatang`, `anak_progress`; kembalikan dict lengkap
    - _Requirements: 4.1, 4.2, 4.4, 4.6, 5.1, 6.1, 7.1, 7.3, 8.1_

- [x] 3. Checkpoint — Verifikasi Service Layer
  - Pastikan semua fungsi di `portal_service.py` dapat diimpor tanpa error
  - Pastikan pure functions (`kelompokkan_jadwal`, `mask_nomor`, `validate_email_format`, `validate_password`, `validate_no_whatsapp`) dapat dipanggil tanpa app context
  - Tanyakan kepada user jika ada pertanyaan sebelum melanjutkan.

- [x] 4. Blueprint Portal: Decorator dan Routes
  - [x] 4.1 Buat `blueprints/portal/__init__.py` dengan definisi `portal_bp`
    - Definisikan `portal_bp = Blueprint('portal', __name__, url_prefix='/portal')`
    - Ekspor `portal_bp`
    - _Requirements: 1.4, 1.5, 3.1_

  - [x] 4.2 Buat `blueprints/portal/decorators.py` dengan decorator `@portal_login_required`
    - Implementasikan `portal_login_required(f)`: redirect ke `url_for('portal.portal_login')` jika belum autentikasi; `abort(403)` jika sudah login tapi `role != 'user'`
    - _Requirements: 1.4, 1.5, 3.5, 8.4, 8.6_

  - [x] 4.3 Buat `blueprints/portal/routes.py` — route autentikasi (login, register, logout)
    - Implementasikan `GET/POST /portal/login` (`portal_login`): tampilkan form login; proses POST dengan query `User.query.filter_by(email=email, is_active=True).first()`, validasi role `user`, panggil `login_user()`; flash message sesuai kondisi; redirect ke dashboard jika berhasil
    - Implementasikan `GET/POST /portal/register` (`portal_register`): tampilkan form registrasi; proses POST dengan validasi via `validate_email_format`, `validate_password`, `validate_no_whatsapp`; cek duplikasi email; buat `User` baru dengan `role='user'`, `username` di-generate dari email+suffix unik; simpan ke DB; redirect ke login dengan flash sukses
    - Implementasikan `GET /portal/logout` (`portal_logout`): panggil `logout_user()`, flash pesan logout, redirect ke `/portal/login`
    - Tambahkan logging untuk login berhasil, login gagal, registrasi berhasil
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.1, 3.2, 3.3, 3.4, 3.6, 3.7_

  - [x] 4.4 Tambahkan route-route yang dilindungi ke `blueprints/portal/routes.py`
    - Implementasikan `GET /portal/dashboard` (`portal_dashboard`): dekorasi dengan `@portal_login_required`; panggil `get_dashboard_stats(current_user.id)`; render `portal/dashboard.html`
    - Implementasikan `GET /portal/anak` (`portal_list_anak`): dekorasi dengan `@portal_login_required`; panggil `get_anak_by_ibu(current_user.id)`; hitung persentase per anak; render `portal/anak/list.html`
    - Implementasikan `GET /portal/anak/<int:anak_id>` (`portal_detail_anak`): dekorasi dengan `@portal_login_required`; panggil `get_anak_or_403(anak_id, current_user.id)`; render `portal/anak/detail.html`
    - Implementasikan `GET /portal/anak/<int:anak_id>/jadwal` (`portal_jadwal_anak`): dekorasi dengan `@portal_login_required`; panggil `get_jadwal_anak(anak_id, current_user.id)`; render `portal/anak/jadwal.html`
    - Implementasikan `GET /portal/notifikasi` (`portal_notifikasi`): dekorasi dengan `@portal_login_required`; panggil `get_notifikasi_ibu(current_user.id)`; render `portal/notifikasi/index.html` dengan nomor ter-mask
    - _Requirements: 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2_

- [x] 5. Registrasi Blueprint dan Guard Petugas
  - [x] 5.1 Daftarkan `portal_bp` di `app.py` dalam fungsi `create_app()`
    - Tambahkan `from blueprints.portal import portal_bp` dan `app.register_blueprint(portal_bp)` setelah blueprint existing
    - _Requirements: 1.4_

  - [x] 5.2 Tambahkan decorator `petugas_only` di `services/auth_service.py`
    - Implementasikan `petugas_only(f)`: `abort(401)` jika belum autentikasi; `abort(403)` jika `role not in ('admin', 'petugas')`
    - Terapkan `@petugas_only` pada semua route handler di `blueprints/auth/routes.py`, `blueprints/anak/routes.py`, `blueprints/imunisasi/routes.py`, `blueprints/notifikasi/routes.py`, `blueprints/laporan/routes.py` yang saat ini menggunakan `@login_required` atau `@role_required`
    - _Requirements: 1.4, 1.5, 8.6_

- [x] 6. Checkpoint — Verifikasi Blueprint dan Routing
  - Pastikan `flask routes` menampilkan semua 10 route portal dengan prefix `/portal`
  - Pastikan akses ke `/portal/dashboard` tanpa login menghasilkan redirect ke `/portal/login`
  - Tanyakan kepada user jika ada pertanyaan sebelum melanjutkan.

- [x] 7. Templates HTML Bootstrap 5
  - [x] 7.1 Buat `templates/portal/base.html` — layout utama portal ibu
    - Struktur HTML5 dengan `<meta charset>`, `<meta viewport>`, Bootstrap 5.3 CDN
    - Navbar dengan brand "Portal Ibu", menu: Dashboard, Anak Saya, Notifikasi, tombol Logout
    - Tampilkan `current_user.nama_lengkap` di navbar/header
    - Block `{% block content %}` untuk konten halaman
    - Render flash messages sebagai Bootstrap alert (success/danger/info/warning)
    - Footer sederhana
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 7.2 Buat `templates/portal/auth/login.html` — halaman login ibu
    - Extends `portal/base.html`
    - Form POST ke `/portal/login` dengan CSRF token (`{{ form.hidden_tag() }}` atau `{{ csrf_token() }}`)
    - Field: email (type="email"), password (type="password")
    - Tombol submit "Masuk"
    - Link ke halaman registrasi
    - _Requirements: 3.1, 8.3, 9.6_

  - [x] 7.3 Buat `templates/portal/auth/register.html` — halaman registrasi ibu
    - Extends `portal/base.html`
    - Form POST ke `/portal/register` dengan CSRF token
    - Field: nama lengkap, email, nomor WhatsApp (opsional), password, konfirmasi password
    - Tampilkan pesan error per field jika ada
    - Tombol submit "Daftar"
    - Link ke halaman login
    - _Requirements: 2.1, 8.3, 9.6_

  - [x] 7.4 Buat `templates/portal/dashboard.html` — dashboard utama
    - Extends `portal/base.html`
    - 4 summary cards Bootstrap: Total Anak, Imunisasi Selesai, Mendatang (7 hari), Terlewat
    - Tabel/list jadwal mendatang diurutkan tanggal terdekat; tampilkan pesan kosong jika tidak ada
    - Daftar anak dengan progress bar persentase imunisasi per anak
    - Pesan "Belum ada data anak..." jika `total_anak == 0`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 9.1, 9.4, 9.6_

  - [x] 7.5 Buat `templates/portal/anak/list.html` — daftar anak
    - Extends `portal/base.html`
    - Tabel/card responsif: nama anak, tanggal lahir, umur (bulan), jenis kelamin, persentase imunisasi
    - Link ke halaman detail dan jadwal per anak
    - _Requirements: 5.1, 5.6, 9.4, 9.6_

  - [x] 7.6 Buat `templates/portal/anak/detail.html` — detail anak
    - Extends `portal/base.html`
    - Tampilkan semua atribut anak: nama, tanggal lahir, jenis kelamin, umur dalam format "X bulan Y hari"
    - Tampilkan badge/label "Melewati Periode 1000 HPK" jika `anak.melewati_1000hpk == True`
    - Link ke halaman jadwal anak
    - _Requirements: 5.2, 5.4, 5.5, 9.6_

  - [x] 7.7 Buat `templates/portal/anak/jadwal.html` — jadwal imunisasi anak
    - Extends `portal/base.html`
    - Header: nama anak, total jadwal, jumlah selesai, persentase (progress bar)
    - Tiga seksi terpisah: "Mendatang", "Terjadwal", "Riwayat"
    - Setiap baris jadwal: nama vaksin, tanggal jadwal, status dengan warna (biru=terjadwal, hijau=selesai, merah=terlewat), tanggal realisasi jika ada
    - Urutkan jadwal berdasarkan `tanggal_jadwal` ASC
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.6, 6.7, 9.6_

  - [x] 7.8 Buat `templates/portal/notifikasi/index.html` — riwayat notifikasi
    - Extends `portal/base.html`
    - Tabel: nama anak, isi pesan (truncate jika panjang), nomor tujuan ter-mask (`****XXXX`), waktu kirim, status (badge terkirim/gagal)
    - Tampilkan pesan "Belum ada notifikasi yang dikirim." jika list kosong
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.6_

- [x] 8. Tests: Unit Tests dan Property-Based Tests
  - [x] 8.1 Buat `tests/portal/__init__.py` (file kosong)
    - _Requirements: 10_

  - [x] 8.2 Perbarui `tests/conftest.py` — tambahkan fixture helper untuk portal
    - Tambahkan fixture `ibu_user` yang membuat `User` dengan `role='user'`, `email`, `no_whatsapp`
    - Tambahkan fixture `anak_ibu` yang membuat `Anak` dengan `created_by=ibu_user.id`
    - Tambahkan fixture `portal_client` yang sudah login sebagai `ibu_user`
    - _Requirements: 10_

  - [x] 8.3 Buat `tests/portal/test_portal_unit.py` — unit tests untuk service dan routes
    - Test `mask_nomor`: input `'08123456789'` → `'****6789'`; input pendek (< 4 digit) → semua bintang
    - Test `validate_email_format`: email valid diterima; string tanpa `@` ditolak; string dengan dua `@` ditolak; domain tanpa `.` ditolak
    - Test `validate_password`: password < 8 karakter → error; konfirmasi tidak cocok → error; keduanya valid → list kosong
    - Test `validate_no_whatsapp`: `'08123456789'` valid; `'+6281234567890'` valid; `'12345'` tidak valid; `'abc'` tidak valid
    - Test `kelompokkan_jadwal`: jadwal terjadwal H+3 masuk `mendatang`; jadwal terjadwal H+10 masuk `terjadwal`; jadwal selesai masuk `riwayat`; jadwal terlewat masuk `riwayat`; jadwal terjadwal H-1 masuk `riwayat` (sudah lewat, bukan mendatang)
    - Test route `GET /portal/login`: status 200, form login tampil
    - Test route `POST /portal/login` sukses: redirect ke dashboard
    - Test route `POST /portal/login` gagal: flash "Email atau password salah."
    - Test route `GET /portal/dashboard` tanpa login: redirect ke `/portal/login`
    - Test route `GET /portal/anak/<id>` dengan anak bukan milik ibu: status 403
    - Test decorator `@portal_login_required` dengan role `petugas`: status 403
    - _Requirements: 2.3, 2.5, 2.6, 2.9, 3.2, 3.3, 3.5, 5.3, 6.5, 8.4, 8.6_

  - [ ]* 8.4 Tulis property test Property 1: Isolasi Data per Ibu
    - **Property 1: Isolasi Data per Ibu**
    - `@given(n_ibu=st.integers(min_value=2, max_value=5), n_anak_per_ibu=st.integers(min_value=1, max_value=4))`
    - Buat `n_ibu` akun ibu masing-masing dengan `n_anak_per_ibu` anak; verifikasi `get_anak_by_ibu(user_id)` hanya mengembalikan anak dengan `created_by == user_id`
    - `@settings(max_examples=100)`
    - **Validates: Requirements 4.6, 7.5, 10.1**

  - [ ]* 8.5 Tulis property test Property 2: Invariant Penjumlahan Statistik
    - **Property 2: Invariant Penjumlahan Statistik**
    - `@given(n_selesai=st.integers(min_value=0, max_value=13), n_terjadwal=st.integers(min_value=0, max_value=13), n_terlewat=st.integers(min_value=0, max_value=13))`
    - Buat jadwal dengan distribusi status sesuai parameter; verifikasi `selesai + terjadwal + terlewat == total`
    - `@settings(max_examples=100)`
    - **Validates: Requirements 4.1, 10.2**

  - [ ]* 8.6 Tulis property test Property 3: Filter Imunisasi Mendatang
    - **Property 3: Filter Imunisasi Mendatang**
    - `@given(offset_hari=st.integers(min_value=-30, max_value=30), status=st.sampled_from(['terjadwal', 'selesai', 'terlewat']))`
    - Buat jadwal dengan `tanggal_jadwal = today + timedelta(offset_hari)` dan status acak; verifikasi masuk `mendatang` jika dan hanya jika `0 <= offset_hari <= 7` AND `status == 'terjadwal'`
    - `@settings(max_examples=100)`
    - **Validates: Requirements 4.2, 6.4, 10.3**

  - [ ]* 8.7 Tulis property test Property 4: Round-Trip Hash Password
    - **Property 4: Round-Trip Hash Password**
    - `@given(password=st.text(min_size=8, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',))))`
    - Buat `User` instance, panggil `set_password(password)`, verifikasi `check_password(password) == True`; buat `password_lain` berbeda, verifikasi `check_password(password_lain) == False`
    - `@settings(max_examples=100)`
    - **Validates: Requirements 2.7, 10.4**

  - [ ]* 8.8 Tulis property test Property 5: Validasi Format Email
    - **Property 5: Validasi Format Email**
    - Sub-test A: `@given(email=st.emails())` — semua email dari `st.emails()` harus diterima `validate_email_format()`
    - Sub-test B: `@given(s=st.text(max_size=50).filter(lambda x: '@' not in x))` — semua string tanpa `@` harus ditolak
    - `@settings(max_examples=100)` pada keduanya
    - **Validates: Requirements 2.3, 10.5**

  - [ ]* 8.9 Tulis property test Property 6: Invariant Range Persentase
    - **Property 6: Invariant Range Persentase**
    - `@given(n_selesai=st.integers(min_value=0, max_value=20), n_total=st.integers(min_value=0, max_value=20))` dengan `assume(n_selesai <= n_total)`
    - Hitung persentase menggunakan logika `hitung_persentase_imunisasi` (atau fungsi helper yang diekstrak); verifikasi `0.0 <= persen <= 100.0`; verifikasi `n_total == 0` menghasilkan `0.0`
    - `@settings(max_examples=100)`
    - **Validates: Requirements 4.4, 6.6, 10.6**

  - [ ]* 8.10 Tulis property test Property 7: Penegakan Kepemilikan Data
    - **Property 7: Penegakan Kepemilikan Data (HTTP 403)**
    - `@given(n_ibu=st.integers(min_value=2, max_value=4))`
    - Buat `n_ibu` akun ibu masing-masing dengan minimal 1 anak; untuk setiap ibu, coba akses anak milik ibu lain via `get_anak_or_403(anak_id_ibu_lain, user_id_ibu_ini)`; verifikasi selalu raise `werkzeug.exceptions.Forbidden` (HTTP 403), tidak pernah mengembalikan data
    - `@settings(max_examples=100)`
    - **Validates: Requirements 5.3, 6.5, 8.2, 10.7**

- [x] 9. Checkpoint Akhir — Pastikan Semua Tests Lulus
  - Jalankan `pytest tests/portal/ -v` dan pastikan semua unit tests lulus
  - Jalankan `pytest tests/ -v` untuk memastikan tidak ada regresi pada tests existing
  - Tanyakan kepada user jika ada pertanyaan atau ada hal yang perlu disesuaikan.

## Notes

- Tasks bertanda `*` adalah opsional (property-based tests) dan dapat dilewati untuk MVP yang lebih cepat
- Setiap task mereferensikan requirements spesifik untuk keterlacakan
- Property tests menggunakan Hypothesis dengan `@settings(max_examples=100)`
- Semua konten template menggunakan Bahasa Indonesia
- Portal bersifat **read-only** — tidak ada form tambah/edit/hapus data anak atau jadwal
- HTTP 403 (bukan 404) untuk semua akses ke data yang bukan milik ibu yang login
- Kolom `email` nullable agar akun petugas existing tidak terpengaruh
- `username` untuk akun ibu di-generate otomatis dari email (bagian sebelum `@`) + suffix unik
