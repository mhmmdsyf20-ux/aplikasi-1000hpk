"""
models/user.py — Model User untuk autentikasi dan manajemen pengguna.

Mendukung tiga role: 'admin', 'petugas', dan 'user' (ibu/orang tua anak).
Menggunakan Flask-Login UserMixin untuk integrasi session management.

Kolom email dan no_whatsapp bersifat nullable agar akun petugas existing
yang tidak memiliki email tetap dapat berfungsi tanpa perubahan.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(db.Model, UserMixin):
    """
    Model pengguna aplikasi 1000 HPK.

    Attributes:
        id           : Primary key.
        username     : Username unik untuk login (wajib untuk petugas).
        password_hash: Hash password menggunakan Werkzeug.
        role         : Role pengguna ('admin', 'petugas', atau 'user').
                       'user' digunakan untuk akun ibu/orang tua anak di Portal Ibu.
        nama_lengkap : Nama lengkap pengguna.
        is_active    : Status aktif akun (digunakan Flask-Login).
        created_at   : Waktu pembuatan akun.
        email        : Alamat email (nullable). Digunakan sebagai kredensial login
                       untuk akun ibu (role='user'). Unique constraint hanya berlaku
                       untuk nilai non-NULL (MySQL tidak menganggap NULL sebagai duplikat).
        no_whatsapp  : Nomor WhatsApp (nullable). Disimpan untuk akun ibu agar dapat
                       dihubungkan dengan notifikasi imunisasi.
    """

    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.Enum("admin", "petugas", "user"), nullable=False)
    nama_lengkap  = db.Column(db.String(150), nullable=False)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    email         = db.Column(db.String(100), unique=True, nullable=True)
    no_whatsapp   = db.Column(db.String(20), nullable=True)

    def set_password(self, password: str) -> None:
        """Hash dan simpan password menggunakan Werkzeug PBKDF2."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifikasi password terhadap hash yang tersimpan."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username!r} role={self.role!r}>"
