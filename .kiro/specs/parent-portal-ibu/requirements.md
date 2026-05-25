# Requirements Document

## Fitur: Parent Portal — Portal Web untuk Ibu/Orang Tua Anak

## Introduction

Fitur ini menambahkan **Portal Web untuk Ibu/Orang Tua Anak** pada aplikasi 1000 HPK yang sudah ada. Aplikasi existing adalah sistem manajemen imunisasi berbasis Flask + MySQL yang digunakan oleh petugas kesehatan (bidan/puskesmas) dengan role `admin` dan `petugas`.

Portal ini memberikan akses **read-only** kepada ibu/orang tua untuk memantau jadwal imunisasi anak-anaknya secara mandiri melalui browser, tanpa perlu menghubungi petugas. Data anak dan jadwal imunisasi tetap diinput dan dikelola oleh petugas — ibu hanya dapat melihat.

Portal diimplementasikan sebagai **Flask Blueprint baru** (`parent_portal`) yang terpisah dari sistem petugas, menggunakan prefix URL `/portal`. Autentikasi portal ibu menggunakan **email** (bukan username seperti sistem petugas), dan disimpan dalam tabel `users` yang sudah ada dengan penambahan kolom `email` dan perubahan enum `role` untuk mengakomodasi role `user`.

> **Catatan Implementasi**: Model `User` existing menggunakan `username` dan role `admin`/`petugas`. Fitur ini memerlukan perluasan model dengan menambahkan kolom `email` (nullable, unique) dan menambahkan nilai `user` ke enum `role`, tanpa mengubah data atau fungsionalitas sistem petugas yang sudah ada.

---

## Glossary

- **Portal_Ibu**: Blueprint Flask baru (`parent_portal`) dengan prefix URL `/portal` yang melayani antarmuka web untuk ibu/orang tua
- **Ibu**: Pengguna dengan role `user` di tabel `users` — ibu atau orang tua anak yang terdaftar di sistem
- **Petugas**: Pengguna dengan role `admin` atau `petugas` — bidan/staf puskesmas yang mengelola data (sistem existing, tidak berubah)
- **Anak**: Entitas data anak dalam tabel `anak` yang terhubung ke akun Ibu melalui `created_by` (FK ke `users.id`)
- **Jadwal**: Entri jadwal imunisasi dalam tabel `imunisasi` yang terhubung ke Anak
- **Notifikasi**: Log pengiriman notifikasi WhatsApp dalam tabel `notifikasi_log` yang terhubung ke Anak
- **Auth_Portal**: Sub-modul autentikasi khusus Portal_Ibu yang menangani login/logout dengan email
- **Dashboard_Portal**: Halaman utama Portal_Ibu yang menampilkan ringkasan status imunisasi semua anak milik Ibu yang sedang login
- **Status_Imunisasi**: Status jadwal imunisasi — `terjadwal` (belum dilakukan), `selesai` (sudah dilakukan), `terlewat` (tanggal sudah lewat, belum dilakukan)
- **Imunisasi_Mendatang**: Jadwal imunisasi dengan status `terjadwal` dan tanggal jadwal dalam rentang hari ini hingga 7 hari ke depan
- **Sesi_Portal**: Sesi Flask-Login khusus untuk Ibu yang terpisah dari sesi Petugas
- **IDAI**: Ikatan Dokter Anak Indonesia — standar jadwal imunisasi nasional yang digunakan sebagai acuan

---

## Requirements

### Requirement 1: Perluasan Model User untuk Akun Ibu

**User Story:** Sebagai pengembang sistem, saya ingin model User yang sudah ada dapat mengakomodasi akun ibu/orang tua agar tidak perlu membuat tabel baru dan tetap konsisten dengan arsitektur existing.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menggunakan tabel `users` yang sudah ada untuk menyimpan akun Ibu, dengan penambahan kolom `email` (VARCHAR 100, UNIQUE, nullable) dan nilai `user` pada enum `role`.
2. THE Portal_Ibu SHALL memastikan kolom `email` bersifat opsional (nullable) agar akun Petugas yang sudah ada (yang tidak memiliki email) tidak terpengaruh.
3. WHEN kolom `email` ditambahkan ke tabel `users`, THE Portal_Ibu SHALL memastikan constraint UNIQUE hanya berlaku untuk nilai non-NULL agar beberapa akun Petugas tanpa email dapat coexist.
4. THE Portal_Ibu SHALL memastikan akun dengan role `user` tidak dapat mengakses route sistem Petugas (`/auth/`, `/anak/`, `/imunisasi/`, `/notifikasi/`, `/laporan/`).
5. THE Portal_Ibu SHALL memastikan akun dengan role `admin` atau `petugas` tidak dapat mengakses route Portal_Ibu (`/portal/`).

---

### Requirement 2: Registrasi Akun Ibu

**User Story:** Sebagai ibu/orang tua anak, saya ingin mendaftar akun sendiri menggunakan email agar dapat mengakses portal untuk memantau jadwal imunisasi anak saya.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menyediakan halaman registrasi di `/portal/register` dengan form yang memuat field: nama lengkap, email, nomor WhatsApp, password, dan konfirmasi password.
2. WHEN ibu mengisi form registrasi, THE Auth_Portal SHALL memvalidasi bahwa semua field wajib (nama lengkap, email, password, konfirmasi password) terisi sebelum memproses pendaftaran.
3. WHEN ibu memasukkan email, THE Auth_Portal SHALL memvalidasi format email menggunakan pola standar RFC 5322 (mengandung `@` dan domain valid).
4. IF email yang dimasukkan sudah terdaftar di tabel `users`, THEN THE Auth_Portal SHALL menampilkan pesan "Email sudah terdaftar. Silakan gunakan email lain atau login."
5. IF password dan konfirmasi password tidak sama, THEN THE Auth_Portal SHALL menampilkan pesan "Konfirmasi password tidak cocok."
6. IF password memiliki panjang kurang dari 8 karakter, THEN THE Auth_Portal SHALL menampilkan pesan "Password minimal 8 karakter."
7. WHEN registrasi berhasil, THE Auth_Portal SHALL menyimpan akun baru dengan role `user`, password dalam bentuk hash menggunakan `werkzeug.security`, dan mengarahkan ibu ke halaman login dengan pesan "Registrasi berhasil. Silakan login."
8. THE Auth_Portal SHALL menyimpan nomor WhatsApp ibu di kolom `no_whatsapp` (VARCHAR 20) pada tabel `users` jika kolom tersebut tersedia, atau di kolom yang sesuai.
9. IF nomor WhatsApp diisi dan tidak sesuai format Indonesia (diawali `08` atau `+62`, panjang 10–15 digit), THEN THE Auth_Portal SHALL menampilkan pesan "Format nomor WhatsApp tidak valid."

---

### Requirement 3: Login dan Logout Ibu

**User Story:** Sebagai ibu/orang tua anak, saya ingin login menggunakan email dan password agar dapat mengakses portal secara aman.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menyediakan halaman login khusus di `/portal/login` yang terpisah dari halaman login Petugas (`/auth/login`).
2. WHEN ibu memasukkan email dan password yang valid, THE Auth_Portal SHALL membuat sesi login dan mengarahkan ibu ke Dashboard_Portal (`/portal/dashboard`).
3. IF ibu memasukkan email atau password yang salah, THEN THE Auth_Portal SHALL menampilkan pesan "Email atau password salah." tanpa mengungkap informasi mana yang salah.
4. IF akun ibu tidak ditemukan atau role bukan `user`, THEN THE Auth_Portal SHALL menampilkan pesan "Email atau password salah." (tidak membedakan antara akun tidak ada vs role salah).
5. WHILE ibu belum login, THE Portal_Ibu SHALL mengarahkan semua akses ke halaman yang dilindungi menuju `/portal/login`.
6. WHEN ibu menekan tombol logout, THE Auth_Portal SHALL menghapus sesi dan mengarahkan ke `/portal/login` dengan pesan "Anda telah berhasil logout."
7. THE Auth_Portal SHALL menggunakan mekanisme sesi Flask-Login yang sama dengan sistem Petugas, namun memvalidasi bahwa user yang login memiliki role `user`.
8. IF sesi ibu tidak aktif selama lebih dari 60 menit, THEN THE Auth_Portal SHALL secara otomatis menghapus sesi dan mengarahkan ke `/portal/login`.

---

### Requirement 4: Dashboard Portal Ibu

**User Story:** Sebagai ibu/orang tua anak, saya ingin melihat ringkasan status imunisasi semua anak saya dalam satu halaman agar dapat memantau kondisi imunisasi secara cepat.

#### Acceptance Criteria

1. THE Dashboard_Portal SHALL menampilkan kartu ringkasan yang memuat: jumlah total anak terdaftar milik ibu yang login, jumlah total jadwal imunisasi selesai, jumlah Imunisasi_Mendatang (dalam 7 hari ke depan), dan jumlah jadwal imunisasi terlewat.
2. THE Dashboard_Portal SHALL menampilkan daftar Imunisasi_Mendatang (status `terjadwal`, tanggal jadwal antara hari ini dan 7 hari ke depan) untuk semua anak milik ibu yang login, diurutkan berdasarkan tanggal jadwal terdekat.
3. WHEN tidak ada Imunisasi_Mendatang, THE Dashboard_Portal SHALL menampilkan pesan "Tidak ada jadwal imunisasi dalam 7 hari ke depan."
4. THE Dashboard_Portal SHALL menampilkan daftar anak milik ibu yang login beserta persentase kelengkapan imunisasi masing-masing anak (jumlah jadwal selesai dibagi total jadwal dikali 100%).
5. WHEN ibu memiliki lebih dari satu anak, THE Dashboard_Portal SHALL menampilkan ringkasan untuk semua anak dalam satu tampilan.
6. THE Dashboard_Portal SHALL hanya menampilkan data anak yang terhubung ke akun ibu yang sedang login (berdasarkan `created_by` = `current_user.id`), tidak menampilkan data anak milik ibu lain.
7. IF ibu belum memiliki anak yang terdaftar (belum ada data anak dengan `created_by` = `current_user.id`), THEN THE Dashboard_Portal SHALL menampilkan pesan "Belum ada data anak. Hubungi petugas puskesmas untuk mendaftarkan anak Anda."

---

### Requirement 5: Melihat Daftar dan Detail Anak

**User Story:** Sebagai ibu/orang tua anak, saya ingin melihat data anak-anak saya yang terdaftar agar dapat memastikan informasi yang tersimpan sudah benar.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menyediakan halaman daftar anak di `/portal/anak` yang menampilkan semua anak milik ibu yang login dengan informasi: nama anak, tanggal lahir, umur (dalam bulan), jenis kelamin, dan persentase kelengkapan imunisasi.
2. THE Portal_Ibu SHALL menyediakan halaman detail anak di `/portal/anak/<id_anak>` yang menampilkan informasi lengkap anak: nama, tanggal lahir, jenis kelamin, umur dalam hari dan bulan.
3. IF ibu mencoba mengakses halaman detail anak yang bukan miliknya (id_anak tidak terhubung ke `current_user.id`), THEN THE Portal_Ibu SHALL mengembalikan respons HTTP 403 Forbidden.
4. THE Portal_Ibu SHALL menampilkan umur anak secara otomatis dalam format "X bulan Y hari" berdasarkan tanggal lahir dan tanggal hari ini.
5. IF anak sudah melewati 730 hari (periode 1000 HPK), THEN THE Portal_Ibu SHALL menampilkan label "Melewati Periode 1000 HPK" pada data anak tersebut.
6. THE Portal_Ibu SHALL menampilkan halaman daftar anak dalam tampilan yang responsif dan dapat diakses dari perangkat mobile (layar minimal 320px).

---

### Requirement 6: Melihat Jadwal Imunisasi Anak

**User Story:** Sebagai ibu/orang tua anak, saya ingin melihat jadwal imunisasi setiap anak beserta statusnya agar dapat mempersiapkan diri untuk membawa anak ke puskesmas.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menyediakan halaman jadwal imunisasi per anak di `/portal/anak/<id_anak>/jadwal` yang menampilkan semua jadwal imunisasi anak tersebut.
2. THE Portal_Ibu SHALL menampilkan setiap jadwal imunisasi dengan informasi: nama vaksin, tanggal jadwal, status (terjadwal/selesai/terlewat), dan tanggal realisasi (jika status selesai).
3. THE Portal_Ibu SHALL menampilkan status imunisasi dengan warna yang berbeda: biru untuk `terjadwal`, hijau untuk `selesai`, merah untuk `terlewat`.
4. THE Portal_Ibu SHALL mengelompokkan jadwal imunisasi dalam tiga bagian: "Mendatang" (terjadwal dalam 7 hari ke depan), "Terjadwal" (terjadwal lebih dari 7 hari ke depan), dan "Riwayat" (selesai atau terlewat).
5. IF ibu mencoba mengakses jadwal anak yang bukan miliknya, THEN THE Portal_Ibu SHALL mengembalikan respons HTTP 403 Forbidden.
6. THE Portal_Ibu SHALL menampilkan jumlah total jadwal, jumlah selesai, dan persentase kelengkapan imunisasi di bagian atas halaman jadwal.
7. WHEN jadwal imunisasi ditampilkan, THE Portal_Ibu SHALL mengurutkan jadwal berdasarkan tanggal jadwal dari yang terlama hingga terbaru.

---

### Requirement 7: Melihat Riwayat Notifikasi

**User Story:** Sebagai ibu/orang tua anak, saya ingin melihat notifikasi yang sudah dikirimkan untuk anak saya agar dapat mengetahui pengingat apa saja yang sudah diterima.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menyediakan halaman notifikasi di `/portal/notifikasi` yang menampilkan riwayat notifikasi WhatsApp yang pernah dikirim untuk semua anak milik ibu yang login.
2. THE Portal_Ibu SHALL menampilkan setiap notifikasi dengan informasi: nama anak, isi pesan, nomor tujuan (ditampilkan sebagian — 4 digit terakhir saja untuk privasi), waktu pengiriman, dan status pengiriman (terkirim/gagal).
3. THE Portal_Ibu SHALL menampilkan maksimal 20 notifikasi terbaru, diurutkan berdasarkan waktu pengiriman dari yang terbaru.
4. WHEN tidak ada riwayat notifikasi, THE Portal_Ibu SHALL menampilkan pesan "Belum ada notifikasi yang dikirim."
5. THE Portal_Ibu SHALL hanya menampilkan notifikasi untuk anak-anak yang terhubung ke akun ibu yang sedang login, tidak menampilkan notifikasi milik ibu lain.

---

### Requirement 8: Keamanan dan Isolasi Data

**User Story:** Sebagai ibu/orang tua anak, saya ingin data saya dan anak saya terlindungi agar tidak dapat diakses oleh ibu lain atau pihak yang tidak berwenang.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL memvalidasi kepemilikan data pada setiap request: setiap akses ke data anak, jadwal, atau notifikasi harus diverifikasi bahwa data tersebut milik `current_user.id` sebelum ditampilkan.
2. IF request mengandung `id_anak` yang tidak terhubung ke `current_user.id`, THEN THE Portal_Ibu SHALL mengembalikan HTTP 403 tanpa mengungkap apakah data tersebut ada atau tidak.
3. THE Portal_Ibu SHALL menggunakan CSRF protection (Flask-WTF) pada semua form di portal (form login, form registrasi).
4. THE Portal_Ibu SHALL memastikan semua route di prefix `/portal/` (kecuali `/portal/login` dan `/portal/register`) memerlukan autentikasi dengan role `user`.
5. THE Portal_Ibu SHALL mencatat aktivitas login dan logout ibu di tabel `log_aktivitas` (jika tabel tersebut tersedia) atau di application log Flask.
6. IF pengguna dengan role `admin` atau `petugas` mencoba mengakses URL `/portal/dashboard` atau halaman portal lainnya yang dilindungi, THEN THE Portal_Ibu SHALL mengembalikan HTTP 403 Forbidden.

---

### Requirement 9: Tampilan dan Antarmuka Portal

**User Story:** Sebagai ibu/orang tua anak, saya ingin portal memiliki tampilan yang mudah dipahami dan dapat diakses dari smartphone agar nyaman digunakan sehari-hari.

#### Acceptance Criteria

1. THE Portal_Ibu SHALL menggunakan Bootstrap 5 sebagai framework CSS, konsisten dengan sistem existing.
2. THE Portal_Ibu SHALL menggunakan template base terpisah (`templates/portal/base.html`) yang berbeda dari template base sistem Petugas, dengan navigasi yang sesuai untuk ibu.
3. THE Portal_Ibu SHALL menyediakan navigasi yang memuat menu: Dashboard, Anak Saya, Notifikasi, dan tombol Logout.
4. THE Portal_Ibu SHALL berfungsi dengan baik pada layar dengan lebar minimal 320px (mobile) hingga 1920px (desktop).
5. THE Portal_Ibu SHALL menampilkan flash message (toast/alert Bootstrap) setelah operasi berhasil atau gagal (login berhasil, login gagal, logout).
6. THE Portal_Ibu SHALL menggunakan bahasa Indonesia untuk semua teks antarmuka, label, pesan error, dan pesan informasi.
7. THE Portal_Ibu SHALL menampilkan nama ibu yang sedang login di bagian navigasi atau header halaman.

---

### Requirement 10: Correctness Properties (Property-Based Testing)

**User Story:** Sebagai pengembang, saya ingin memastikan logika bisnis Portal_Ibu dapat diverifikasi secara otomatis agar bug dapat ditemukan lebih awal.

#### Acceptance Criteria

**Property 1 — Isolasi Data (Invariant Keamanan)**

1. FOR ALL kombinasi `user_id_ibu` dan `id_anak` yang valid, WHEN Portal_Ibu mengambil daftar anak untuk `user_id_ibu`, THE Portal_Ibu SHALL hanya mengembalikan anak-anak yang memiliki `created_by == user_id_ibu` — tidak pernah mengembalikan anak milik user lain.

**Property 2 — Konsistensi Statistik Dashboard (Invariant Penjumlahan)**

2. FOR ALL akun Ibu dengan data anak dan jadwal imunisasi, WHEN Dashboard_Portal menghitung statistik, THE Dashboard_Portal SHALL memastikan: `jumlah_selesai + jumlah_terjadwal + jumlah_terlewat == total_jadwal` untuk setiap anak.

**Property 3 — Kalkulasi Imunisasi Mendatang (Metamorphic Property)**

3. FOR ALL jadwal imunisasi dengan tanggal jadwal `T`, WHEN Portal_Ibu menghitung Imunisasi_Mendatang pada hari `H`, THE Portal_Ibu SHALL memasukkan jadwal tersebut ke daftar mendatang jika dan hanya jika `H <= T <= H + 7` dan status adalah `terjadwal`.

**Property 4 — Hash Password Round-Trip**

4. FOR ALL string password yang valid (panjang >= 8 karakter), WHEN Auth_Portal memanggil `set_password(password)` kemudian `check_password(password)`, THE Auth_Portal SHALL mengembalikan `True` — dan WHEN `check_password` dipanggil dengan password yang berbeda, THE Auth_Portal SHALL mengembalikan `False`.

**Property 5 — Validasi Format Email (Error Condition)**

5. FOR ALL string input email, WHEN Auth_Portal memvalidasi format email, THE Auth_Portal SHALL menolak (mengembalikan error) semua string yang tidak mengandung tepat satu karakter `@` dengan karakter non-kosong di kiri dan domain valid di kanan.

**Property 6 — Persentase Kelengkapan Imunisasi (Invariant Range)**

6. FOR ALL anak dengan data jadwal imunisasi, WHEN Portal_Ibu menghitung persentase kelengkapan imunisasi, THE Portal_Ibu SHALL menghasilkan nilai dalam rentang `0.0 <= persentase <= 100.0` — tidak pernah negatif atau melebihi 100%.

**Property 7 — Akses Terlarang Konsisten (Invariant Keamanan)**

7. FOR ALL request ke `/portal/anak/<id_anak>` atau `/portal/anak/<id_anak>/jadwal` dengan `id_anak` yang tidak terhubung ke `current_user.id`, THE Portal_Ibu SHALL selalu mengembalikan HTTP 403 — tidak pernah HTTP 200 atau HTTP 404 yang mengungkap keberadaan data.

