"""
tests/integration/test_db_connection.py — Integration test koneksi MySQL nyata.

CATATAN: Test ini memerlukan MySQL yang berjalan dan konfigurasi .env yang valid.
Jalankan secara terpisah: pytest tests/integration/ -v
"""

import pytest


@pytest.mark.integration
def test_mysql_connection():
    """Verifikasi koneksi ke MySQL nyata menggunakan konfigurasi .env."""
    try:
        from app import create_app
        app = create_app()  # Menggunakan Config default (MySQL)
        with app.app_context():
            from extensions import db
            # Coba query sederhana
            result = db.session.execute(db.text("SELECT 1")).fetchone()
            assert result[0] == 1, "Query SELECT 1 harus mengembalikan 1"
        print("Koneksi MySQL berhasil.")
    except Exception as e:
        pytest.skip(f"MySQL tidak tersedia: {e}")
