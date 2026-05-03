"""
app.py — Application factory untuk aplikasi 1000 HPK Skripsi
Gunakan create_app() untuk membuat instance Flask.

Contoh penggunaan:
    from app import create_app
    app = create_app()
    app.run(debug=True)
"""

import sys
import logging
from flask import Flask, render_template, redirect, url_for

from config import Config, config_map
from extensions import db, login_manager, csrf


def create_app(config=None):
    """
    Application factory.

    Args:
        config: dict override config, nama config string ('testing'),
                atau None untuk menggunakan Config default.

    Returns:
        Flask app instance yang sudah dikonfigurasi.
    """
    app = Flask(__name__)

    # ── Load konfigurasi ───────────────────────────────────────────────────────
    if config is None:
        app.config.from_object(Config)
    elif isinstance(config, str):
        app.config.from_object(config_map.get(config, Config))
    elif isinstance(config, dict):
        app.config.from_object(Config)
        app.config.update(config)
    else:
        app.config.from_object(config)

    # ── Inisialisasi ekstensi ──────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # ── Registrasi Blueprint ───────────────────────────────────────────────────
    # Blueprint akan diaktifkan satu per satu seiring implementasi task berikutnya.
    # Uncomment setiap baris setelah Blueprint yang bersangkutan selesai dibuat.

    from blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from blueprints.anak import anak_bp
    app.register_blueprint(anak_bp)

    from blueprints.imunisasi import imunisasi_bp
    app.register_blueprint(imunisasi_bp)

    from blueprints.notifikasi import notifikasi_bp
    app.register_blueprint(notifikasi_bp)

    from blueprints.laporan import laporan_bp
    app.register_blueprint(laporan_bp)

    from blueprints.edukasi import edukasi_bp
    app.register_blueprint(edukasi_bp)

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return render_template("errors/500.html"), 500

    # ── Import models agar metadata tabel terdaftar ke SQLAlchemy ─────────────
    # Import harus dilakukan di dalam create_app() setelah db.init_app(app)
    # agar tidak terjadi circular import.
    import models  # noqa: F401 — side-effect import untuk registrasi tabel

    # ── User loader untuk Flask-Login ──────────────────────────────────────────
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Route utama: redirect / ke dashboard ──────────────────────────────────
    @app.route('/')
    def index():
        return redirect(url_for('anak.dashboard'))

    # ── Buat tabel database ────────────────────────────────────────────────────
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created/verified successfully.")
        except Exception as e:
            _handle_db_error(e)

    return app


def _handle_db_error(e: Exception):
    """
    Menangani error koneksi database dengan pesan yang deskriptif.
    Menghentikan aplikasi jika bukan dalam mode testing.
    """
    error_msg = str(e)
    logging.error("=" * 60)
    logging.error("GAGAL TERHUBUNG KE DATABASE")
    logging.error("=" * 60)

    if "Access denied" in error_msg:
        logging.error(
            "Error: Username atau password MySQL salah.\n"
            "Periksa DB_USER dan DB_PASSWORD di file .env"
        )
    elif "Unknown database" in error_msg:
        logging.error(
            "Error: Database tidak ditemukan.\n"
            "Pastikan database sudah dibuat dan DB_NAME di .env sudah benar.\n"
            "Jalankan: CREATE DATABASE hpk1000 CHARACTER SET utf8mb4;"
        )
    elif "Can't connect" in error_msg or "Connection refused" in error_msg:
        logging.error(
            "Error: Tidak dapat terhubung ke server MySQL.\n"
            "Pastikan MySQL server berjalan dan DB_HOST/DB_PORT di .env sudah benar."
        )
    else:
        logging.error(f"Error detail: {error_msg}")

    logging.error("=" * 60)
    logging.error("Periksa konfigurasi di file .env dan pastikan MySQL berjalan.")
    logging.error("=" * 60)

    # Hentikan aplikasi jika bukan mode testing
    import os
    if not os.environ.get("FLASK_TESTING"):
        sys.exit(1)


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
