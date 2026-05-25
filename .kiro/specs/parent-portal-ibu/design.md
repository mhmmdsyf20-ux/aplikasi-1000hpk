 q# Design Document

## Fitur: Parent Portal - Portal Web untuk Ibu/Orang Tua Anak

## Overview

Fitur ini menambahkan **Portal Web untuk Ibu/Orang Tua Anak** pada aplikasi 1000 HPK yang sudah berjalan. Aplikasi existing adalah sistem manajemen imunisasi berbasis Flask + MySQL yang digunakan oleh petugas kesehatan (bidan/puskesmas) dengan role admin dan petugas.

Portal ini memberikan akses **read-only** kepada ibu/orang tua untuk memantau jadwal imunisasi anak-anaknya secara mandiri melalui browser. Data anak dan jadwal imunisasi tetap diinput dan dikelola oleh petugas - ibu hanya dapat melihat.

Portal diimplementasikan sebagai **Flask Blueprint baru** (parent_portal) dengan prefix URL /portal, terpisah sepenuhnya dari sistem petugas. Autentikasi portal ibu menggunakan **email** (bukan username seperti sistem petugas), dan disimpan dalam tabel users yang sudah ada dengan penambahan kolom email dan perluasan enum role untuk mengakomodasi nilai user.

### Tujuan Desain

- **Isolasi penuh**: Blueprint, template, service, dan decorator terpisah dari sistem petugas
- **Zero breaking change**: Perubahan model User bersifat additive - kolom baru nullable, enum diperluas
- **Read-only untuk ibu**: Tidak ada form tambah/edit/hapus di portal
- **Keamanan berlapis**: Validasi kepemilikan data di setiap request, CSRF protection, role guard
- **Mobile-first**: Responsif untuk smartphone (layar minimal 320px)
- **Bahasa Indonesia**: Semua teks antarmuka, label, dan pesan dalam Bahasa Indonesia

## Architecture

Fitur ini mengikuti pola arsitektur yang sudah ada di aplikasi 1000 HPK: **Blueprint + Service + Template**. Semua komponen baru diisolasi dalam namespace `portal` agar tidak mengganggu sistem petugas yang sudah berjalan.

### Diagram Arsitektur

```
Browser (Ibu)
    |
    v
Flask App (create_app)
    |
    +-- Blueprint: parent_portal (prefix: /portal)
    |       |
    |       +-- routes.py (auth, dashboard, anak, jadwal, notifikasi)
    |       +-- decorators.py (@portal_login_required)
    |
    +-- Service: portal_service.py
    |       |
    |       +-- get_anak_by_ibu(user_id)
    |       +-- get_dashboard_stats(user_id)
    |       +-- get_jadwal_anak(anak_id, user_id)
    |       +-- get_notifikasi_ibu(user_id, limit=20)
    |       +-- hitung_persentase_imunisasi(anak_id)
    |       +-- kelompokkan_jadwal(jadwal_list, today)
    |
    +-- Model: User (diperluas)
    |       +-- kolom baru: email (VARCHAR 100, UNIQUE, nullable)
    |       +-- kolom baru: no_whatsapp (VARCHAR 20, nullable)
    |       +-- enum role diperluas: 'admin' | 'petugas' | 'user'
    |
    +-- Templates: templates/portal/
    |       +-- base.html (navbar ibu, flash messages)
    |       +-- auth/login.html
    |       +-- auth/register.html
    |       +-- dashboard.html
    |       +-- anak/list.html
    |       +-- anak/detail.html
    |       +-- anak/jadwal.html
    |       +-- notifikasi/index.html
    |
    +-- Database: MySQL (tabel existing, schema diperluas)
            +-- users (+ kolom email, no_whatsapp, + enum value 'user')
            +-- anak (tidak berubah)
            +-- imunisasi (tidak berubah)
            +-- notifikasi_log (tidak berubah)
```

### Alur Request Tipikal

```
GET /portal/anak/5/jadwal
    |
    v
@portal_login_required
    -- cek: current_user.is_authenticated?  -> redirect /portal/login jika tidak
    -- cek: current_user.role == 'user'?    -> abort(403) jika bukan
    |
    v
portal_service.get_jadwal_anak(anak_id=5, user_id=current_user.id)
    -- query: Anak.query.filter_by(id=5, created_by=current_user.id).first_or_404()
    -- jika tidak ditemukan: abort(403)  [bukan 404, untuk tidak mengungkap keberadaan data]
    -- query: Imunisasi.query.filter_by(anak_id=5).order_by(tanggal_jadwal).all()
    -- kelompokkan: mendatang / terjadwal / riwayat
    |
    v
render_template('portal/anak/jadwal.html', ...)
```

### Keputusan Desain Utama

1. **Satu tabel `users` untuk semua role**: Menghindari duplikasi model dan menyederhanakan Flask-Login. Kolom `email` nullable agar akun petugas existing tidak terpengaruh.

2. **`created_by` sebagai kunci kepemilikan**: Anak terhubung ke ibu melalui `anak.created_by = users.id`. Petugas yang mendaftarkan anak harus mengisi `created_by` dengan `id` akun ibu yang sudah terdaftar, atau petugas dapat menghubungkan anak ke akun ibu setelah ibu mendaftar.

3. **Decorator `@portal_login_required` terpisah**: Tidak menggunakan `@login_required` bawaan Flask-Login karena perlu validasi tambahan `role == 'user'`. Decorator ini menggabungkan cek autentikasi dan cek role dalam satu dekorator.

4. **HTTP 403 (bukan 404) untuk akses data orang lain**: Mengembalikan 403 untuk semua akses ke data yang bukan milik ibu yang login, tanpa membedakan apakah data ada atau tidak. Ini mencegah enumeration attack.

5. **Masking nomor telepon**: Nomor tujuan notifikasi ditampilkan dengan format `****XXXX` (hanya 4 digit terakhir) untuk menjaga privasi.

6. **Migration manual via ALTER TABLE**: Karena aplikasi tidak menggunakan Alembic/Flask-Migrate, perubahan skema dilakukan via script SQL migration yang dijalankan sekali.

## Components and Interfaces

### 1. Blueprint: `parent_portal`

**File**: `blueprints/portal/__init__.py` dan `blueprints/portal/routes.py`

```python
# blueprints/portal/__init__.py
from flask import Blueprint

portal_bp = Blueprint(
    'portal',
    __name__,
    url_prefix='/portal',
    template_folder='../../templates/portal',
)
```

**Route Map**:

| Method | URL | Fungsi | Deskripsi |
|--------|-----|--------|-----------|
| GET | `/portal/login` | `portal_login` | Halaman login ibu |
| POST | `/portal/login` | `portal_login` | Proses login ibu |
| GET | `/portal/register` | `portal_register` | Halaman registrasi ibu |
| POST | `/portal/register` | `portal_register` | Proses registrasi ibu |
| GET | `/portal/logout` | `portal_logout` | Logout ibu |
| GET | `/portal/dashboard` | `portal_dashboard` | Dashboard utama |
| GET | `/portal/anak` | `portal_list_anak` | Daftar anak milik ibu |
| GET | `/portal/anak/<int:anak_id>` | `portal_detail_anak` | Detail anak |
| GET | `/portal/anak/<int:anak_id>/jadwal` | `portal_jadwal_anak` | Jadwal imunisasi anak |
| GET | `/portal/notifikasi` | `portal_notifikasi` | Riwayat notifikasi |

### 2. Decorator: `@portal_login_required`

**File**: `blueprints/portal/decorators.py`

```python
from functools import wraps
from flask import redirect, url_for, abort
from flask_login import current_user

def portal_login_required(f):
    """
    Decorator untuk route Portal Ibu.
    - Redirect ke /portal/login jika belum autentikasi
    - Abort 403 jika sudah login tapi role bukan 'user'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('portal.portal_login'))
        if current_user.role != 'user':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

### 3. Service: `portal_service.py`

**File**: `services/portal_service.py`

Interface fungsi-fungsi utama:

```python
def get_anak_by_ibu(user_id: int) -> list[Anak]:
    """Ambil semua anak milik ibu dengan user_id. Hanya anak dengan created_by == user_id."""

def get_dashboard_stats(user_id: int) -> dict:
    """
    Hitung statistik dashboard untuk ibu.
    Returns: {
        'total_anak': int,
        'total_selesai': int,
        'total_mendatang': int,  # terjadwal dalam 7 hari ke depan
        'total_terlewat': int,
        'jadwal_mendatang': list[Imunisasi],
        'anak_progress': list[dict]  # [{anak, persen}, ...]
    }
    """

def get_anak_or_403(anak_id: int, user_id: int) -> Anak:
    """
    Ambil anak berdasarkan id. Abort 403 jika tidak ditemukan atau bukan milik user_id.
    Selalu abort(403) - tidak pernah abort(404) - untuk mencegah enumeration.
    """

def get_jadwal_anak(anak_id: int, user_id: int) -> dict:
    """
    Ambil dan kelompokkan jadwal imunisasi anak.
    Validasi kepemilikan via get_anak_or_403.
    Returns: {
        'anak': Anak,
        'mendatang': list[Imunisasi],   # terjadwal, H <= T <= H+7
        'terjadwal': list[Imunisasi],   # terjadwal, T > H+7
        'riwayat': list[Imunisasi],     # selesai atau terlewat
        'total': int,
        'selesai': int,
        'persen': float
    }
    """

def get_notifikasi_ibu(user_id: int, limit: int = 20) -> list[NotifikasiLog]:
    """
    Ambil notifikasi untuk semua anak milik ibu, maksimal `limit` terbaru.
    Diurutkan berdasarkan waktu_kirim DESC.
    """

def hitung_persentase_imunisasi(anak_id: int) -> float:
    """
    Hitung persentase kelengkapan imunisasi anak.
    Returns: float dalam range [0.0, 100.0].
    Returns 0.0 jika tidak ada jadwal.
    """

def kelompokkan_jadwal(jadwal_list: list, today: date) -> dict:
    """
    Kelompokkan daftar jadwal imunisasi ke dalam tiga kategori.
    Pure function - tidak mengakses database.
    Returns: {'mendatang': [...], 'terjadwal': [...], 'riwayat': [...]}
    """

def mask_nomor(no_hp: str) -> str:
    """
    Masking nomor HP - tampilkan hanya 4 digit terakhir.
    Contoh: '08123456789' -> '****6789'
    """

def validate_email_format(email: str) -> bool:
    """
    Validasi format email menggunakan regex RFC 5322 sederhana.
    Returns True jika format valid.
    """

def validate_password(password: str, konfirmasi: str) -> list[str]:
    """
    Validasi password dan konfirmasi.
    Returns list of error messages. Empty list = valid.
    """

def validate_no_whatsapp(no_wa: str) -> bool:
    """
    Validasi nomor WhatsApp format Indonesia.
    Valid: diawali 08 atau +62, panjang 10-15 digit.
    """
```

### 4. Registrasi Blueprint di `app.py`

Tambahkan di `create_app()` setelah blueprint existing:

```python
from blueprints.portal import portal_bp
app.register_blueprint(portal_bp)
```

### 5. Guard untuk Route Petugas

Tambahkan validasi di `services/auth_service.py` atau di setiap blueprint petugas untuk menolak akses dari role `user`:

```python
# Modifikasi role_required agar menolak role 'user' secara eksplisit
# Atau tambahkan decorator @petugas_only yang hanya mengizinkan 'admin' dan 'petugas'
def petugas_only(f):
    """Decorator: hanya izinkan role admin dan petugas. Tolak role user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ('admin', 'petugas'):
            abort(403)
        return f(*args, **kwargs)
    return decorated
```

## Data Models

### Perubahan Model `User`

Model `User` existing perlu diperluas dengan dua kolom baru dan perluasan enum `role`. Perubahan ini bersifat **additive** dan tidak merusak data existing.

#### Perubahan SQLAlchemy (models/user.py)

```python
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # DIUBAH: tambah nilai 'user' ke enum
    role          = db.Column(db.Enum("admin", "petugas", "user"), nullable=False)
    nama_lengkap  = db.Column(db.String(150), nullable=False)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    # BARU: kolom email untuk akun ibu
    email         = db.Column(db.String(100), unique=True, nullable=True)
    # BARU: kolom nomor WhatsApp untuk akun ibu
    no_whatsapp   = db.Column(db.String(20), nullable=True)
```

**Catatan penting**:
- `email` bersifat `nullable=True` agar akun petugas existing tidak terpengaruh
- `unique=True` pada `email` di MySQL hanya berlaku untuk nilai non-NULL (NULL tidak dianggap duplikat)
- `username` tetap wajib untuk akun petugas; untuk akun ibu, `username` diisi otomatis dari email (bagian sebelum `@`) dengan suffix unik jika diperlukan
- Akun ibu tidak memiliki `username` yang digunakan untuk login — login menggunakan `email`

#### Script Migration SQL

Karena aplikasi tidak menggunakan Alembic, perubahan skema dilakukan via script SQL:

```sql
-- migration_portal_ibu.sql
-- Jalankan sekali sebelum deploy fitur portal

-- 1. Tambah kolom email
ALTER TABLE users
    ADD COLUMN email VARCHAR(100) NULL,
    ADD UNIQUE INDEX uq_users_email (email);

-- 2. Tambah kolom no_whatsapp
ALTER TABLE users
    ADD COLUMN no_whatsapp VARCHAR(20) NULL;

-- 3. Perluas enum role (MySQL memerlukan MODIFY COLUMN)
ALTER TABLE users
    MODIFY COLUMN role ENUM('admin', 'petugas', 'user') NOT NULL;
```

**Urutan eksekusi**: Ketiga ALTER TABLE harus dijalankan dalam satu transaksi atau secara berurutan. Aman dijalankan pada database yang sudah berisi data karena semua perubahan bersifat additive.

### Model Existing (Tidak Berubah)

#### `Anak`

Kolom `created_by` (FK ke `users.id`) digunakan sebagai kunci kepemilikan. Ketika petugas mendaftarkan anak untuk ibu yang sudah memiliki akun portal, petugas mengisi `created_by` dengan `id` akun ibu tersebut.

```
anak.created_by  -->  users.id  (akun ibu dengan role='user')
```

#### `Imunisasi`

Tidak ada perubahan. Diakses via relasi `anak.imunisasi_list` atau query langsung dengan filter `anak_id`.

#### `NotifikasiLog`

Tidak ada perubahan. Diakses via relasi `anak.notifikasi_list` atau query langsung dengan filter `anak_id`.

### Diagram Relasi Data

```
users (role='user')
    id  <----+
    email    |
    nama_lengkap  |
    no_whatsapp   |
                  |
anak              |
    id            |
    nama          |
    created_by ---+  (FK ke users.id akun ibu)
    |
    +-- imunisasi
    |       anak_id (FK)
    |       nama_vaksin
    |       tanggal_jadwal
    |       status: terjadwal | selesai | terlewat
    |
    +-- notifikasi_log
            anak_id (FK)
            pesan
            no_tujuan
            status_kirim
            waktu_kirim
```

### Struktur Data Dashboard

```python
# Tipe data yang dikembalikan get_dashboard_stats()
{
    'total_anak': 2,
    'total_selesai': 8,
    'total_mendatang': 1,
    'total_terlewat': 2,
    'jadwal_mendatang': [<Imunisasi>, ...],  # maks 7 hari ke depan
    'anak_progress': [
        {
            'anak': <Anak>,
            'total': 13,
            'selesai': 8,
            'persen': 61.5
        },
        ...
    ]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Fitur ini menggunakan **Hypothesis** sebagai library property-based testing (Python). Setiap property dijalankan minimum 100 iterasi dengan input yang di-generate secara acak.

---

### Property 1: Isolasi Data per Ibu

*For any* user ID ibu yang valid, fungsi `get_anak_by_ibu(user_id)` SHALL hanya mengembalikan anak-anak yang memiliki `created_by == user_id` - tidak pernah mengembalikan anak milik user lain, bahkan ketika database berisi anak dari banyak ibu berbeda.

**Validates: Requirements 4.6, 7.5, 10.1**

---

### Property 2: Invariant Penjumlahan Statistik

*For any* anak dengan data jadwal imunisasi, jumlah jadwal berdasarkan status SHALL selalu memenuhi: `jumlah_selesai + jumlah_terjadwal + jumlah_terlewat == total_jadwal`. Invariant ini harus terpenuhi untuk setiap anak secara individual maupun secara agregat untuk semua anak milik satu ibu.

**Validates: Requirements 4.1, 10.2**

---

### Property 3: Filter Imunisasi Mendatang

*For any* daftar jadwal imunisasi dengan tanggal jadwal `T` dan hari referensi `H`, fungsi `kelompokkan_jadwal(jadwal_list, today=H)` SHALL memasukkan jadwal ke grup `mendatang` jika dan hanya jika `H <= T <= H + 7` DAN `status == 'terjadwal'`. Jadwal dengan status `selesai` atau `terlewat` tidak boleh masuk ke grup `mendatang` meskipun tanggalnya dalam rentang 7 hari.

**Validates: Requirements 4.2, 6.4, 10.3**

---

### Property 4: Round-Trip Hash Password

*For any* string password dengan panjang >= 8 karakter, memanggil `user.set_password(password)` kemudian `user.check_password(password)` SHALL mengembalikan `True`. Sebaliknya, untuk *any* string `password_lain` yang berbeda dari `password`, `user.check_password(password_lain)` SHALL mengembalikan `False`.

**Validates: Requirements 2.7, 10.4**

---

### Property 5: Validasi Format Email

*For any* string input `s`, fungsi `validate_email_format(s)` SHALL mengembalikan `False` untuk semua string yang tidak memenuhi kriteria: tepat satu karakter `@`, karakter non-kosong di sisi kiri `@`, dan setidaknya satu karakter `.` di sisi kanan `@` dengan karakter non-kosong di antara keduanya. String yang memenuhi semua kriteria tersebut SHALL mengembalikan `True`.

**Validates: Requirements 2.3, 10.5**

---

### Property 6: Invariant Range Persentase Kelengkapan

*For any* anak dengan jumlah jadwal imunisasi >= 0, fungsi `hitung_persentase_imunisasi(anak_id)` SHALL selalu menghasilkan nilai `p` dalam rentang `0.0 <= p <= 100.0`. Tidak pernah negatif, tidak pernah melebihi 100.0, dan jika tidak ada jadwal SHALL mengembalikan `0.0`.

**Validates: Requirements 4.4, 6.6, 10.6**

---

### Property 7: Penegakan Kepemilikan Data (HTTP 403)

*For any* kombinasi `(ibu_A, anak_milik_ibu_B)` di mana `anak.created_by != ibu_A.id`, fungsi `get_anak_or_403(anak_id, user_id=ibu_A.id)` SHALL selalu memanggil `abort(403)` - tidak pernah mengembalikan data anak, tidak pernah memanggil `abort(404)`. Ini berlaku untuk semua endpoint: detail anak, jadwal anak, maupun notifikasi.

**Validates: Requirements 5.3, 6.5, 8.2, 10.7**

## Error Handling

### Kategori Error dan Penanganannya

#### 1. Error Autentikasi

| Kondisi | Respons | Pesan ke User |
|---------|---------|---------------|
| Email tidak ditemukan | Redirect ke `/portal/login` | "Email atau password salah." |
| Password salah | Redirect ke `/portal/login` | "Email atau password salah." |
| Role bukan `user` | Redirect ke `/portal/login` | "Email atau password salah." |
| Akun tidak aktif | Redirect ke `/portal/login` | "Email atau password salah." |
| Sesi expired | Redirect ke `/portal/login` | (tidak ada pesan, redirect saja) |

**Prinsip**: Semua kegagalan login menghasilkan pesan yang identik untuk mencegah user enumeration.

#### 2. Error Registrasi

| Kondisi | Respons | Pesan ke User |
|---------|---------|---------------|
| Field wajib kosong | Re-render form | "Field X wajib diisi." |
| Format email tidak valid | Re-render form | "Format email tidak valid." |
| Email sudah terdaftar | Re-render form | "Email sudah terdaftar. Silakan gunakan email lain atau login." |
| Password < 8 karakter | Re-render form | "Password minimal 8 karakter." |
| Konfirmasi password tidak cocok | Re-render form | "Konfirmasi password tidak cocok." |
| Format nomor WA tidak valid | Re-render form | "Format nomor WhatsApp tidak valid." |

#### 3. Error Akses Data

| Kondisi | HTTP Status | Penanganan |
|---------|-------------|------------|
| Akses anak bukan milik ibu | 403 Forbidden | `abort(403)` - tidak mengungkap keberadaan data |
| Akses jadwal anak bukan milik ibu | 403 Forbidden | `abort(403)` |
| User dengan role `admin`/`petugas` akses portal | 403 Forbidden | `abort(403)` |
| Akses route portal tanpa login | Redirect | Redirect ke `/portal/login` |

#### 4. Error Database

Semua operasi database dibungkus dalam try-except di service layer:

```python
def get_anak_by_ibu(user_id: int) -> list:
    try:
        return Anak.query.filter_by(created_by=user_id).order_by(Anak.nama).all()
    except Exception as e:
        current_app.logger.error(f"Error get_anak_by_ibu user_id={user_id}: {e}")
        return []  # Kembalikan list kosong, bukan raise exception
```

#### 5. Error Handler Global

Error handler yang sudah ada di `app.py` (403, 404, 500) akan menangani error dari portal. Template error yang sudah ada (`templates/errors/403.html`, dll.) akan digunakan.

### Logging

Semua aktivitas penting dicatat ke application log Flask:

```python
# Login berhasil
app.logger.info(f"Portal login: user_id={user.id} email={user.email}")

# Login gagal
app.logger.warning(f"Portal login gagal: email={email} ip={request.remote_addr}")

# Akses tidak sah
app.logger.warning(f"Portal 403: user_id={current_user.id} mencoba akses anak_id={anak_id}")

# Registrasi berhasil
app.logger.info(f"Portal registrasi: user_id={user.id} email={user.email}")
```

## Testing Strategy

### Pendekatan Pengujian

Fitur Portal Ibu menggunakan **dual testing approach**:
1. **Unit tests** (pytest): Verifikasi contoh spesifik, edge case, dan kondisi error
2. **Property-based tests** (Hypothesis): Verifikasi properti universal di seluruh input

### Library dan Konfigurasi

```
# requirements-test.txt (tambahkan)
hypothesis==6.112.0
pytest==8.x
pytest-flask==1.3.0
```

Konfigurasi Hypothesis:

```python
from hypothesis import settings, HealthCheck

settings.register_profile("ci", max_examples=100, suppress_health_check=[HealthCheck.too_slow])
settings.load_profile("ci")
```

### Property-Based Tests (Hypothesis)

Setiap property test harus:
- Dijalankan minimum **100 iterasi** (default Hypothesis)
- Diberi tag komentar referensi ke property di design document
- Menggunakan `@given` decorator dari Hypothesis

#### Struktur File Test

```
tests/
    portal/
        __init__.py
        test_portal_properties.py   # 7 property tests
        test_portal_unit.py         # unit tests spesifik
        test_portal_integration.py  # integration tests
```

#### Contoh Implementasi Property Tests

```python
# tests/portal/test_portal_properties.py
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from datetime import date, timedelta

# Feature: parent-portal-ibu, Property 1: Isolasi Data per Ibu
@given(
    n_ibu=st.integers(min_value=2, max_value=5),
    n_anak_per_ibu=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=100)
def test_property1_isolasi_data(app, db, n_ibu, n_anak_per_ibu):
    # Buat beberapa ibu dengan anak masing-masing
    # Verifikasi get_anak_by_ibu(user_id) hanya mengembalikan anak milik ibu tersebut
    ...

# Feature: parent-portal-ibu, Property 2: Invariant Penjumlahan Statistik
@given(
    n_selesai=st.integers(min_value=0, max_value=13),
    n_terjadwal=st.integers(min_value=0, max_value=13),
    n_terlewat=st.integers(min_value=0, max_value=13),
)
@settings(max_examples=100)
def test_property2_statistik_invariant(app, db, n_selesai, n_terjadwal, n_terlewat):
    # Buat jadwal dengan distribusi status acak
    # Verifikasi selesai + terjadwal + terlewat == total
    ...

# Feature: parent-portal-ibu, Property 3: Filter Imunisasi Mendatang
@given(
    offset_hari=st.integers(min_value=-30, max_value=30),
    status=st.sampled_from(['terjadwal', 'selesai', 'terlewat']),
)
@settings(max_examples=100)
def test_property3_filter_mendatang(offset_hari, status):
    # Buat jadwal dengan tanggal = today + offset_hari dan status acak
    # Verifikasi masuk/tidak masuk ke grup mendatang sesuai kondisi
    ...

# Feature: parent-portal-ibu, Property 4: Round-Trip Hash Password
@given(password=st.text(min_size=8, max_size=50))
@settings(max_examples=100)
def test_property4_password_roundtrip(app, password):
    # set_password(p) kemudian check_password(p) harus True
    # check_password(p + 'x') harus False
    ...

# Feature: parent-portal-ibu, Property 5: Validasi Format Email
@given(email=st.emails())
@settings(max_examples=100)
def test_property5_email_valid_diterima(email):
    # Email yang di-generate st.emails() harus diterima validate_email_format()
    ...

@given(email=st.text(max_size=50).filter(lambda s: '@' not in s))
@settings(max_examples=100)
def test_property5_email_tanpa_at_ditolak(email):
    # String tanpa @ harus ditolak
    ...

# Feature: parent-portal-ibu, Property 6: Invariant Range Persentase
@given(
    n_selesai=st.integers(min_value=0, max_value=20),
    n_total=st.integers(min_value=0, max_value=20),
)
@settings(max_examples=100)
def test_property6_persentase_range(n_selesai, n_total):
    assume(n_selesai <= n_total)
    # hitung_persentase(selesai, total) harus dalam [0.0, 100.0]
    ...

# Feature: parent-portal-ibu, Property 7: Penegakan Kepemilikan Data
@given(n_ibu=st.integers(min_value=2, max_value=4))
@settings(max_examples=100)
def test_property7_ownership_enforcement(app, db, n_ibu):
    # Buat beberapa ibu dengan anak masing-masing
    # Verifikasi get_anak_or_403(anak_id_ibu_lain, user_id) selalu abort(403)
    ...
```

### Unit Tests

Unit tests fokus pada:
- Halaman login dan registrasi (GET/POST)
- Flash messages yang benar
- Redirect yang benar setelah login/logout
- Tampilan data yang benar di dashboard, daftar anak, jadwal, notifikasi
- Edge cases: ibu tanpa anak, jadwal kosong, notifikasi kosong

### Integration Tests

Integration tests memverifikasi alur end-to-end:
- Registrasi -> Login -> Dashboard -> Lihat Anak -> Lihat Jadwal
- Verifikasi isolasi data antar ibu dalam satu request cycle

### Cakupan Test yang Diharapkan

| Komponen | Unit Test | Property Test |
|----------|-----------|---------------|
| `validate_email_format()` | Format valid/invalid spesifik | Property 5 |
| `validate_password()` | Kasus edge (7 char, 8 char, tidak cocok) | Property 4 |
| `kelompokkan_jadwal()` | Kasus batas tanggal | Property 3 |
| `hitung_persentase_imunisasi()` | 0 jadwal, semua selesai, semua terlewat | Property 6 |
| `get_anak_by_ibu()` | Ibu tanpa anak, ibu dengan banyak anak | Property 1 |
| `get_anak_or_403()` | Anak milik sendiri, anak milik orang lain | Property 7 |
| `get_dashboard_stats()` | Statistik konsisten | Property 2 |
| Routes portal | Login, logout, register, semua halaman | - |
| Decorator `@portal_login_required` | Unauthenticated, role salah, role benar | - |
