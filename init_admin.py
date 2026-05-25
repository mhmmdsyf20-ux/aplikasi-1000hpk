"""
init_admin.py — Script untuk membuat user admin pertama.
Jalankan sekali saja: python init_admin.py
"""
from app import create_app
from extensions import db
from models import User

app = create_app()

with app.app_context():
    # Cek apakah admin sudah ada
    existing = User.query.filter_by(username='admin').first()
    if existing:
        print("User 'admin' sudah ada.")
    else:
        admin = User(
            username='admin',
            nama_lengkap='Administrator',
            role='admin',
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("User admin berhasil dibuat!")
        print("Username: admin")
        print("Password: admin123")
        print("SEGERA GANTI PASSWORD setelah login!")
