# Design Document — Upgrade Aplikasi 1000 HPK Skripsi

## Overview

Dokumen ini mendeskripsikan desain teknis untuk upgrade aplikasi web **1000 Hari Pertama Kehidupan (1000 HPK)** dari prototipe sederhana (Flask + SQLite, tanpa autentikasi) menjadi aplikasi skripsi lengkap yang siap produksi.

### Tujuan Upgrade

Aplikasi saat ini hanya memiliki tiga halaman statis (index, edukasi, tambah data) dengan satu tabel SQLite dan logika imunisasi yang sangat sederhana. Upgrade ini mentransformasi aplikasi menjadi sistem manajemen imunisasi anak berbasis peran (role-based) dengan fitur:

- **Database MySQL** via SQLAlchemy ORM (4 tabel relasional)
- **Autentikasi role-based** (Admin & Petugas) dengan session management
- **Manajemen data anak lengkap** dengan auto-generate jadwal IDAI
- **Jadwal imunisasi IDAI** dengan status otomatis dan visualisasi warna
- **UI modern Bootstrap 5** dengan sidebar responsif dan pagination
- **Visualisasi Chart.js** (donut, bar chart, progress per anak)
- **Notifikasi WhatsApp** via Fonnte/Twilio dengan log pengiriman
- **Laporan & ekspor** PDF/Excel (khusus Admin)
- **Halaman edukasi** 1000 HPK yang diperkaya konten
- **Keamanan dasar** (.env, CSRF, session timeout)

### Teknologi Stack

| Layer | Teknologi |
|---|---|
| Backend | Python 3.10+, Flask 3.x |
| ORM | SQLAlchemy 2.x + Flask-SQLAlchemy |
| Database | MySQL 8.x |
| Autentikasi | Flask-Login, Werkzeug Security |
| CSRF | Flask-WTF |
| Konfigurasi | python-dotenv |
| Frontend | Bootstrap 5.3, Chart.js 4.x, Jinja2 |
| Notifikasi | Fonnte API / Twilio WhatsApp API |
| Ekspor PDF | WeasyPrint atau ReportLab |
| Ekspor Excel | openpyxl |
| Env | `.env` + `.env.example` |

---

## Architecture

Aplikasi menggunakan arsitektur **MVC monolitik berbasis Flask** dengan Blueprint untuk pemisahan modul. Semua komponen berjalan dalam satu proses Flask, cocok untuk skala skripsi/puskesmas kecil.

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser / Client                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                     Flask Application                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  auth    │  │  anak    │  │imunisasi │  │ notifikasi │  │
│  │Blueprint │  │Blueprint │  │Blueprint │  │ Blueprint  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │              │              │               │         │
│  ┌────▼──────────────▼──────────────▼───────────────▼──────┐ │
│  │                  Service Layer                           │ │
│  │  auth_service  anak_service  imunisasi_service  wa_svc  │ │
│  └────────────────────────┬─────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────────┐ │
│  │              SQLAlchemy ORM (Models)                     │ │
│  │         User | Anak | Imunisasi | NotifikasiLog          │ │
│  └────────────────────────┬─────────────────────────────────┘ │
└───────────────────────────┼──────────────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │        MySQL 8.x           │
              └────────────────────────────┘
                            
              ┌─────────────────────────────┐
              │   WA_Gateway (Fonnte/Twilio) │
              │   (external HTTP API)        │
              └─────────────────────────────┘
```

### Struktur Direktori Proyek

```
1000hpk/
├── app.py                  # Entry point, factory function
├── config.py               # Konfigurasi dari .env
├── extensions.py           # Inisialisasi db, login_manager, csrf
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── anak.py
│   ├── imunisasi.py
│   └── notifikasi_log.py
├── blueprints/
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── anak/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── imunisasi/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── notifikasi/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── laporan/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── edukasi/
│       ├── __init__.py
│       └── routes.py
├── services/
│   ├── auth_service.py
│   ├── anak_service.py
│   ├── imunisasi_service.py
│   ├── wa_service.py
│   └── laporan_service.py
├── templates/
│   ├── base.html           # Layout utama dengan sidebar Bootstrap 5
│   ├── auth/
│   ├── anak/
│   ├── imunisasi/
│   ├── notifikasi/
│   ├── laporan/
│   └── edukasi/
├── static/
│   ├── css/
│   ├── js/
│   └── img/
├── .env                    # Tidak di-commit
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## Components and Interfaces

### 1. Auth Blueprint (`blueprints/auth/`)

Menangani semua alur autentikasi.

**Routes:**
| Method | Path | Deskripsi |
|---|---|---|
| GET/POST | `/login` | Form login |
| GET | `/logout` | Hapus sesi, redirect ke login |
| GET/POST | `/admin/users` | Daftar & tambah user (Admin only) |
| GET/POST | `/admin/users/<id>/edit` | Edit user (Admin only) |

**Decorator keamanan:**
```python
# Digunakan di semua route yang dilindungi
@login_required          # dari Flask-Login
@role_required('admin')  # custom decorator
```

**Session timeout:** Diimplementasikan via `PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)` di config Flask.

---

### 2. Anak Blueprint (`blueprints/anak/`)

Menangani CRUD data anak.

**Routes:**
| Method | Path | Deskripsi |
|---|---|---|
| GET | `/anak` | Daftar anak (dengan search & pagination) |
| GET/POST | `/anak/tambah` | Form tambah anak baru |
| GET/POST | `/anak/<id>/edit` | Form edit data anak |
| GET | `/anak/<id>` | Detail anak + daftar imunisasi |

**Validasi nomor HP Indonesia:**
```python
import re
HP_PATTERN = re.compile(r'^(\+62|08)\d{8,13}$')

def validate_hp(no_hp: str) -> bool:
    return bool(HP_PATTERN.match(no_hp.strip()))
```

---

### 3. Imunisasi Blueprint (`blueprints/imunisasi/`)

Menangani jadwal dan pencatatan imunisasi.

**Routes:**
| Method | Path | Deskripsi |
|---|---|---|
| GET | `/imunisasi` | Daftar semua jadwal (filter status) |
| POST | `/imunisasi/<id>/selesai` | Tandai imunisasi selesai |
| GET | `/imunisasi/mendatang` | Imunisasi 7 hari ke depan |

**Jadwal IDAI (konstanta):**
```python
JADWAL_IDAI = [
    {"nama_vaksin": "Hepatitis B",    "offset_hari": 0},
    {"nama_vaksin": "BCG",            "offset_hari": 0},
    {"nama_vaksin": "Polio 0",        "offset_hari": 0},
    {"nama_vaksin": "DPT-HB-Hib 1",  "offset_hari": 60},
    {"nama_vaksin": "Polio 1",        "offset_hari": 60},
    {"nama_vaksin": "DPT-HB-Hib 2",  "offset_hari": 120},
    {"nama_vaksin": "Polio 2",        "offset_hari": 120},
    {"nama_vaksin": "DPT-HB-Hib 3",  "offset_hari": 180},
    {"nama_vaksin": "Polio 3",        "offset_hari": 180},
    {"nama_vaksin": "Campak/MR",      "offset_hari": 270},
    {"nama_vaksin": "Polio 4",        "offset_hari": 270},
    {"nama_vaksin": "Booster DPT",    "offset_hari": 540},
    {"nama_vaksin": "Booster Campak", "offset_hari": 540},
]
```

---

### 4. Notifikasi Blueprint (`blueprints/notifikasi/`)

Menangani pengiriman WhatsApp dan log.

**Routes:**
| Method | Path | Deskripsi |
|---|---|---|
| GET | `/notifikasi` | Daftar anak dengan jadwal mendatang + riwayat log |
| POST | `/notifikasi/kirim/<anak_id>` | Kirim ke satu anak |
| POST | `/notifikasi/kirim-semua` | Kirim ke semua anak dengan jadwal 7 hari |

**WA Service Interface:**
```python
class WAService:
    def kirim_pesan(self, no_tujuan: str, pesan: str) -> dict:
        """
        Returns: {"success": bool, "message": str, "provider": str}
        """
```

**Format pesan:**
```
Yth. Orang tua {nama_anak}, jadwal imunisasi {nama_vaksin} 
pada {tanggal} sudah mendekat. Harap datang ke {nama_fasilitas}. 
Info: 1000HPK App.
```

---

### 5. Laporan Blueprint (`blueprints/laporan/`)

Hanya dapat diakses Admin.

**Routes:**
| Method | Path | Deskripsi |
|---|---|---|
| GET | `/laporan` | Halaman laporan dengan filter tanggal |
| GET | `/laporan/export/pdf` | Download PDF |
| GET | `/laporan/export/excel` | Download Excel (.xlsx) |

---

### 6. Dashboard (bagian dari `blueprints/anak/` atau route utama)

**Data yang dikirim ke template:**
```python
{
    "total_anak": int,
    "imunisasi_hari_ini": int,
    "imunisasi_mendatang": int,   # 7 hari ke depan
    "imunisasi_terlewat": int,
    "chart_status_data": dict,    # untuk donut chart
    "chart_bulanan_data": dict,   # untuk bar chart 6 bulan
}
```

---

## Data Models

### ERD (Entity Relationship Diagram)

```
users
  id (PK)
  username (UNIQUE, NOT NULL)
  password_hash (NOT NULL)
  role (ENUM: 'admin','petugas', NOT NULL)
  nama_lengkap (NOT NULL)
  created_at

anak
  id (PK)
  nama (NOT NULL)
  tanggal_lahir (DATE, NOT NULL)
  jenis_kelamin (ENUM: 'L','P', NOT NULL)
  nama_ibu (NOT NULL)
  no_hp_ortu (NOT NULL)
  alamat
  berat_lahir (FLOAT)        -- gram
  panjang_lahir (FLOAT)      -- cm
  created_by (FK → users.id)
  created_at

imunisasi
  id (PK)
  anak_id (FK → anak.id, NOT NULL)
  nama_vaksin (NOT NULL)
  tanggal_jadwal (DATE, NOT NULL)
  tanggal_realisasi (DATE)
  status (ENUM: 'terjadwal','selesai','terlewat', NOT NULL, DEFAULT 'terjadwal')
  catatan (TEXT)
  petugas_id (FK → users.id)

notifikasi_log
  id (PK)
  anak_id (FK → anak.id, NOT NULL)
  pesan (TEXT, NOT NULL)
  no_tujuan (NOT NULL)
  status_kirim (ENUM: 'terkirim','gagal', NOT NULL)
  waktu_kirim (DATETIME, NOT NULL)
  error_message (TEXT)       -- diisi jika gagal
```

### SQLAlchemy Models

```python
# models/user.py
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.Enum('admin', 'petugas'), nullable=False)
    nama_lengkap  = db.Column(db.String(150), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

# models/anak.py
class Anak(db.Model):
    __tablename__ = 'anak'
    id             = db.Column(db.Integer, primary_key=True)
    nama           = db.Column(db.String(150), nullable=False)
    tanggal_lahir  = db.Column(db.Date, nullable=False)
    jenis_kelamin  = db.Column(db.Enum('L', 'P'), nullable=False)
    nama_ibu       = db.Column(db.String(150), nullable=False)
    no_hp_ortu     = db.Column(db.String(20), nullable=False)
    alamat         = db.Column(db.Text)
    berat_lahir    = db.Column(db.Float)
    panjang_lahir  = db.Column(db.Float)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    imunisasi_list = db.relationship('Imunisasi', backref='anak', lazy=True,
                                     cascade='all, delete-orphan')

    @property
    def umur_hari(self) -> int:
        return (date.today() - self.tanggal_lahir).days

    @property
    def umur_bulan(self) -> int:
        return self.umur_hari // 30

    @property
    def melewati_1000hpk(self) -> bool:
        return self.umur_hari > 730

# models/imunisasi.py
class Imunisasi(db.Model):
    __tablename__ = 'imunisasi'
    id                 = db.Column(db.Integer, primary_key=True)
    anak_id            = db.Column(db.Integer, db.ForeignKey('anak.id'), nullable=False)
    nama_vaksin        = db.Column(db.String(100), nullable=False)
    tanggal_jadwal     = db.Column(db.Date, nullable=False)
    tanggal_realisasi  = db.Column(db.Date)
    status             = db.Column(db.Enum('terjadwal', 'selesai', 'terlewat'),
                                   nullable=False, default='terjadwal')
    catatan            = db.Column(db.Text)
    petugas_id         = db.Column(db.Integer, db.ForeignKey('users.id'))

# models/notifikasi_log.py
class NotifikasiLog(db.Model):
    __tablename__ = 'notifikasi_log'
    id            = db.Column(db.Integer, primary_key=True)
    anak_id       = db.Column(db.Integer, db.ForeignKey('anak.id'), nullable=False)
    pesan         = db.Column(db.Text, nullable=False)
    no_tujuan     = db.Column(db.String(20), nullable=False)
    status_kirim  = db.Column(db.Enum('terkirim', 'gagal'), nullable=False)
    waktu_kirim   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    error_message = db.Column(db.Text)
```

### Konfigurasi Database (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ.get('DB_PORT', '3306')}"
        f"/{os.environ['DB_NAME']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME     = timedelta(minutes=60)
    WTF_CSRF_ENABLED               = True
    MAX_CONTENT_LENGTH             = 5 * 1024 * 1024  # 5 MB
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Fitur ini melibatkan logika bisnis murni (validasi input, kalkulasi tanggal, transformasi data, state machine imunisasi, format pesan, filter query) yang sangat cocok untuk property-based testing. Library yang digunakan: **Hypothesis** (Python).

---

### Property 1: Password hashing adalah round-trip yang aman

*For any* string password yang valid, menyimpannya sebagai hash menggunakan `generate_password_hash` dan kemudian memverifikasinya dengan `check_password_hash` harus selalu mengembalikan `True`. Selain itu, hash yang dihasilkan tidak boleh sama dengan plaintext password.

**Validates: Requirements 2.4**

---

### Property 2: Kredensial yang salah selalu ditolak

*For any* kombinasi username dan password yang tidak cocok dengan data user yang tersimpan di database, proses autentikasi harus selalu mengembalikan kegagalan dan menampilkan pesan "Username atau password salah".

**Validates: Requirements 2.3**

---

### Property 3: Semua route yang dilindungi mengarahkan ke login jika belum autentikasi

*For any* route yang memerlukan autentikasi (ditandai `@login_required`), request HTTP tanpa sesi yang valid harus selalu menghasilkan redirect ke `/login` dengan status code 302.

**Validates: Requirements 2.5**

---

### Property 4: Akses kontrol role — Petugas tidak dapat mengakses route Admin

*For any* route yang memerlukan role Admin (ditandai `@role_required('admin')`), request dari pengguna dengan role Petugas yang sudah login harus selalu menghasilkan response dengan status code 403.

**Validates: Requirements 2.7, 2.8**

---

### Property 5: Validasi nomor HP Indonesia

*For any* string nomor HP, fungsi `validate_hp()` harus mengembalikan `True` jika dan hanya jika string tersebut diawali dengan `08` atau `+62` dan memiliki total panjang antara 10 hingga 15 digit angka. Untuk semua string lain, harus mengembalikan `False`.

**Validates: Requirements 3.3**

---

### Property 6: Validasi field wajib data anak

*For any* kombinasi data anak di mana satu atau lebih field wajib (nama, tanggal_lahir, jenis_kelamin, nama_ibu, no_hp_ortu) bernilai kosong atau None, sistem harus selalu menolak penyimpanan dan tidak membuat entri baru di database.

**Validates: Requirements 3.2**

---

### Property 7: Auto-generate jadwal imunisasi IDAI sesuai tanggal lahir

*For any* tanggal lahir yang valid, ketika data anak baru disimpan, sistem harus membuat tepat `len(JADWAL_IDAI)` entri imunisasi di mana setiap entri memiliki `tanggal_jadwal = tanggal_lahir + timedelta(days=offset)` sesuai dengan konstanta `JADWAL_IDAI`.

**Validates: Requirements 3.6, 4.1, 4.2**

---

### Property 8: Kalkulasi umur anak dan flag 1000 HPK

*For any* tanggal lahir yang valid, properti `umur_hari` harus sama dengan `(date.today() - tanggal_lahir).days`, properti `umur_bulan` harus sama dengan `umur_hari // 30`, dan properti `melewati_1000hpk` harus bernilai `True` jika dan hanya jika `umur_hari > 730`.

**Validates: Requirements 3.7, 3.8**

---

### Property 9: State transition imunisasi — tandai selesai

*For any* entri imunisasi dengan status `terjadwal`, setelah ditandai selesai dengan tanggal realisasi tertentu, status harus berubah menjadi `selesai` dan `tanggal_realisasi` harus tersimpan sama persis dengan tanggal yang diberikan.

**Validates: Requirements 4.3**

---

### Property 10: State transition imunisasi — otomatis terlewat

*For any* entri imunisasi dengan status `terjadwal` dan `tanggal_jadwal` yang sudah lewat dari hari ini, setelah fungsi update status dijalankan, status harus berubah menjadi `terlewat`. Imunisasi dengan `tanggal_jadwal` hari ini atau di masa depan tidak boleh berubah statusnya.

**Validates: Requirements 4.4**

---

### Property 11: Filter imunisasi mendatang (7 hari)

*For any* daftar imunisasi dengan berbagai tanggal jadwal, fungsi `get_imunisasi_mendatang()` harus mengembalikan hanya imunisasi yang memiliki `tanggal_jadwal` antara `date.today()` (inklusif) dan `date.today() + timedelta(days=7)` (inklusif), dengan status `terjadwal`.

**Validates: Requirements 4.6, 7.1**

---

### Property 12: Format pesan WhatsApp mengandung semua komponen wajib

*For any* kombinasi nama anak, nama vaksin, tanggal jadwal, dan nama fasilitas, fungsi `format_pesan_wa()` harus menghasilkan string yang mengandung: nama anak, nama vaksin, representasi tanggal, dan nama fasilitas.

**Validates: Requirements 7.3**

---

### Property 13: Log notifikasi selalu konsisten dengan hasil pengiriman

*For any* percobaan pengiriman notifikasi WhatsApp (berhasil atau gagal), sistem harus selalu membuat satu entri `NotifikasiLog` dengan `status_kirim = 'terkirim'` jika pengiriman berhasil, atau `status_kirim = 'gagal'` beserta `error_message` yang tidak kosong jika pengiriman gagal.

**Validates: Requirements 7.5, 7.6**

---

### Property 14: Riwayat notifikasi dibatasi 20 entri terbaru

*For any* jumlah entri `NotifikasiLog` yang ada di database (termasuk lebih dari 20), halaman Notifikasi harus selalu menampilkan maksimal 20 entri, diurutkan dari yang paling baru.

**Validates: Requirements 7.9**

---

### Property 15: Filter laporan berdasarkan rentang tanggal

*For any* rentang tanggal `[start_date, end_date]` dan dataset imunisasi, fungsi generate laporan harus mengembalikan hanya entri imunisasi yang memiliki `tanggal_jadwal` atau `tanggal_realisasi` dalam rentang tersebut (inklusif). Tidak ada entri di luar rentang yang boleh muncul.

**Validates: Requirements 8.2**

---

### Property 16: Laporan mengandung semua kolom yang diperlukan

*For any* dataset imunisasi yang valid, laporan yang dihasilkan (baik PDF maupun Excel) harus selalu mengandung semua kolom yang diperlukan: nama anak, tanggal lahir, umur (bulan), nama vaksin, tanggal jadwal, tanggal realisasi, status, nama petugas.

**Validates: Requirements 8.5**

---

### Property 17: Statistik laporan akurat

*For any* dataset imunisasi dengan jumlah selesai dan terlewat yang diketahui, ringkasan statistik di halaman Laporan harus menampilkan nilai yang tepat: total anak = jumlah unik anak_id, total selesai = jumlah entri dengan status 'selesai', total terlewat = jumlah entri dengan status 'terlewat', persentase cakupan = (selesai / total) * 100.

**Validates: Requirements 8.6**

---

### Property 18: Persentase progress imunisasi per anak akurat

*For any* anak dengan jumlah imunisasi selesai yang diketahui dari total imunisasi yang dijadwalkan, fungsi kalkulasi progress harus mengembalikan nilai yang tepat: `(jumlah_selesai / total_dijadwalkan) * 100`.

**Validates: Requirements 6.3**

---

### Property 19: CSRF protection pada semua route POST

*For any* route POST yang dilindungi autentikasi, request tanpa CSRF token yang valid harus selalu menghasilkan response dengan status code 400 Bad Request.

**Validates: Requirements 10.2**

---

## Error Handling

### Strategi Umum

Semua error ditangani secara terpusat menggunakan Flask error handlers dan flash messages. Tidak ada stack trace yang ditampilkan ke pengguna di mode produksi.

```python
# app.py — error handlers terpusat
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Server error: {e}")
    return render_template('errors/500.html'), 500
```

### Error per Komponen

| Komponen | Kondisi Error | Penanganan |
|---|---|---|
| DB_Module | Koneksi MySQL gagal saat startup | Log error deskriptif, hentikan aplikasi dengan `sys.exit(1)` |
| Auth_Module | Login gagal | Flash message "Username atau password salah", redirect ke login |
| Auth_Module | Akses tanpa login | Redirect ke `/login` dengan `next` parameter |
| Auth_Module | Akses role tidak cukup | Return 403 Forbidden |
| Anak | Validasi form gagal | Flash message per field, render ulang form dengan data yang sudah diisi |
| Anak | Nomor HP tidak valid | Flash message "Format nomor HP tidak valid" |
| WA_Gateway | API error (timeout, 4xx, 5xx) | Catat di `notifikasi_log` dengan status 'gagal' dan `error_message`, flash message ke user |
| WA_Gateway | Nomor tidak valid | Catat di `notifikasi_log` dengan status 'gagal', lanjutkan ke anak berikutnya (untuk kirim semua) |
| Laporan | Export gagal | Flash message "Gagal mengekspor laporan", log error di server |
| CSRF | Token tidak valid | Return 400 Bad Request |

### Validasi Input

Semua input dari form divalidasi di dua lapisan:
1. **Client-side**: HTML5 `required`, `pattern`, `min`/`max` attributes
2. **Server-side**: Validasi Python sebelum menyimpan ke database (tidak bergantung pada client-side)

```python
# services/anak_service.py
def validate_anak_data(data: dict) -> list[str]:
    """Returns list of error messages. Empty list = valid."""
    errors = []
    required = ['nama', 'tanggal_lahir', 'jenis_kelamin', 'nama_ibu', 'no_hp_ortu']
    for field in required:
        if not data.get(field, '').strip():
            errors.append(f"Field '{field}' wajib diisi.")
    if data.get('no_hp_ortu') and not validate_hp(data['no_hp_ortu']):
        errors.append("Format nomor HP tidak valid.")
    return errors
```

---

## Testing Strategy

### Pendekatan Dual Testing

Strategi pengujian menggunakan dua pendekatan yang saling melengkapi:

1. **Unit tests** — pytest: menguji contoh spesifik, edge case, dan kondisi error
2. **Property-based tests** — Hypothesis: menguji properti universal di atas (Properties 1–19)

### Setup Testing

```
# requirements-test.txt
pytest==8.x
hypothesis==6.x
pytest-flask==1.x
coverage==7.x
```

```python
# conftest.py
import pytest
from app import create_app
from extensions import db as _db

@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        _db.create_all()
        yield app

@pytest.fixture
def client(app):
    return app.test_client()
```

> **Catatan**: Property-based tests menggunakan SQLite in-memory sebagai pengganti MySQL untuk kecepatan dan isolasi. Integrasi dengan MySQL diuji secara terpisah di integration tests.

### Property-Based Tests (Hypothesis)

Setiap property di atas diimplementasikan sebagai satu test Hypothesis dengan minimal **100 iterasi**.

```python
# tests/test_properties.py
from hypothesis import given, settings
from hypothesis import strategies as st

# Property 5: Validasi nomor HP
@given(st.text())
@settings(max_examples=200)
def test_validate_hp_property(no_hp):
    """Feature: upgrade-1000hpk-skripsi, Property 5: Validasi nomor HP Indonesia"""
    result = validate_hp(no_hp)
    if result:
        assert no_hp.startswith('08') or no_hp.startswith('+62')
        digits = no_hp.replace('+', '').replace('-', '')
        assert 10 <= len(digits) <= 15

# Property 7: Auto-generate jadwal IDAI
@given(st.dates(min_value=date(2020, 1, 1), max_value=date.today()))
@settings(max_examples=100)
def test_auto_generate_jadwal_idai(tanggal_lahir):
    """Feature: upgrade-1000hpk-skripsi, Property 7: Auto-generate jadwal IDAI"""
    jadwal = generate_jadwal_imunisasi(tanggal_lahir)
    assert len(jadwal) == len(JADWAL_IDAI)
    for item, ref in zip(sorted(jadwal, key=lambda x: x['tanggal_jadwal']),
                         sorted(JADWAL_IDAI, key=lambda x: x['offset_hari'])):
        expected = tanggal_lahir + timedelta(days=ref['offset_hari'])
        assert item['tanggal_jadwal'] == expected
```

**Tag format untuk setiap test:**
```python
# Feature: upgrade-1000hpk-skripsi, Property {N}: {deskripsi singkat}
```

### Unit Tests

Unit tests fokus pada:
- Contoh spesifik untuk setiap route (GET/POST)
- Edge case yang tidak tercakup oleh property tests
- Integrasi antar komponen (service layer + model)
- Error handling (koneksi gagal, API error)

```
tests/
├── conftest.py
├── test_auth.py          # Login, logout, session, role access
├── test_anak.py          # CRUD anak, validasi form
├── test_imunisasi.py     # State transitions, filter mendatang
├── test_notifikasi.py    # WA service mock, log
├── test_laporan.py       # Filter tanggal, ekspor
├── test_properties.py    # Semua 19 property-based tests
└── test_smoke.py         # Konfigurasi, skema DB, env vars
```

### Integration Tests

Integration tests dijalankan secara terpisah (memerlukan MySQL dan koneksi internet untuk WA API):

```
tests/integration/
├── test_db_connection.py     # Koneksi MySQL nyata
└── test_wa_gateway.py        # Fonnte/Twilio API (dengan nomor test)
```

### Coverage Target

| Modul | Target Coverage |
|---|---|
| `services/` | ≥ 90% |
| `models/` | ≥ 85% |
| `blueprints/` | ≥ 80% |
| Overall | ≥ 80% |

### Menjalankan Tests

```bash
# Unit + property tests (tanpa integrasi)
pytest tests/ -v --ignore=tests/integration

# Dengan coverage report
pytest tests/ --ignore=tests/integration --cov=. --cov-report=html

# Hanya property tests
pytest tests/test_properties.py -v

# Hanya smoke tests
pytest tests/test_smoke.py -v
```
