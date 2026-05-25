"""
config.py — Konfigurasi aplikasi 1000 HPK
Membaca semua variabel dari file .env menggunakan python-dotenv.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Keamanan ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-ganti-di-production")

    # ── Database — Railway otomatis set DATABASE_URL ──────────────────────────
    # Railway MySQL: MYSQL_URL atau DATABASE_URL
    # Railway PostgreSQL: DATABASE_URL
    _db_url = os.environ.get("DATABASE_URL") or os.environ.get("MYSQL_URL", "")

    # Fix format Railway: "mysql://" → "mysql+pymysql://"
    if _db_url.startswith("mysql://"):
        _db_url = _db_url.replace("mysql://", "mysql+pymysql://", 1)
    # Fix format Railway: "postgres://" → "postgresql+psycopg2://"
    elif _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql+psycopg2://", 1)

    # Fallback ke manual config jika DATABASE_URL tidak ada
    if not _db_url:
        DB_TYPE = os.environ.get("DB_TYPE", "mysql")
        DB_HOST = os.environ.get("DB_HOST", "localhost")
        DB_PORT = os.environ.get("DB_PORT", "3306")
        DB_USER = os.environ.get("DB_USER", "root")
        DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
        DB_NAME = os.environ.get("DB_NAME", "defaultdb")
        DB_SSL = os.environ.get("DB_SSL", "false").lower() == "true"
        if DB_TYPE == "mysql":
            ssl_args = "?ssl_ca=/etc/ssl/certs/ca-certificates.crt" if DB_SSL else ""
            _db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}{ssl_args}"
        else:
            _db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session ────────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ── CSRF ───────────────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED = True

    # ── Upload ─────────────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    # ── WhatsApp Gateway ───────────────────────────────────────────────────────
    WA_GATEWAY = os.environ.get("WA_GATEWAY", "fonnte")   # "fonnte" atau "twilio"
    WA_API_KEY = os.environ.get("WA_API_KEY", "")
    WA_SENDER = os.environ.get("WA_SENDER", "")

    # ── Identitas Fasilitas ────────────────────────────────────────────────────
    NAMA_FASILITAS = os.environ.get("NAMA_FASILITAS", "Puskesmas Terdekat")


class TestingConfig(Config):
    """Konfigurasi khusus untuk testing — menggunakan SQLite in-memory."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


# Mapping nama config ke class
config_map = {
    "default": Config,
    "testing": TestingConfig,
}
