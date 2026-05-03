"""
extensions.py — Inisialisasi ekstensi Flask
Semua ekstensi dibuat di sini tanpa dikaitkan ke app instance tertentu.
Pengikatan ke app dilakukan di create_app() menggunakan pola init_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# ORM database
db = SQLAlchemy()

# Manajemen sesi login
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu."
login_manager.login_message_category = "warning"

# CSRF protection
csrf = CSRFProtect()
