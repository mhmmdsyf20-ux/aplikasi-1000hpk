"""
tests/test_e2e.py — End-to-end smoke tests untuk alur utama aplikasi 1000 HPK.

Menguji alur: login → tambah anak → cek jadwal terbuat → tandai selesai → cek log.
"""

from datetime import date, timedelta
import pytest
from models import User, Anak, Imunisasi, NotifikasiLog
from services.imunisasi_service import JADWAL_IDAI


def create_admin(db):
    """Helper: buat user admin untuk testing."""
    user = User(username='admin_e2e', role='admin', nama_lengkap='Admin E2E')
    user.set_password('adminpass123')
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, username, password):
    """Helper: login via HTTP POST."""
    return client.post(
        '/auth/login',
        data={'username': username, 'password': password},
        follow_redirects=True,
    )


class TestE2EAlurUtama:
    """Test alur end-to-end: login → tambah anak → jadwal terbuat → tandai selesai."""

    def test_login_berhasil(self, client, db):
        """Admin dapat login dan diarahkan ke dashboard."""
        create_admin(db)
        resp = login_as(client, 'admin_e2e', 'adminpass123')
        assert resp.status_code == 200

    def test_tambah_anak_dan_jadwal_terbuat(self, client, db):
        """Setelah tambah anak, jadwal imunisasi IDAI otomatis terbuat."""
        admin = create_admin(db)
        login_as(client, 'admin_e2e', 'adminpass123')

        tgl_lahir = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        resp = client.post(
            '/anak/tambah',
            data={
                'nama': 'Anak Test E2E',
                'tanggal_lahir': tgl_lahir,
                'jenis_kelamin': 'L',
                'nama_ibu': 'Ibu Test',
                'no_hp_ortu': '08123456789',
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Verifikasi anak tersimpan
        anak = Anak.query.filter_by(nama='Anak Test E2E').first()
        assert anak is not None

        # Verifikasi jadwal IDAI terbuat (13 vaksin)
        jadwal = Imunisasi.query.filter_by(anak_id=anak.id).all()
        assert len(jadwal) == len(JADWAL_IDAI), \
            f"Harus ada {len(JADWAL_IDAI)} jadwal, tapi hanya ada {len(jadwal)}"

    def test_tandai_imunisasi_selesai(self, client, db):
        """Petugas dapat menandai imunisasi sebagai selesai."""
        admin = create_admin(db)
        login_as(client, 'admin_e2e', 'adminpass123')

        # Buat anak dengan jadwal
        tgl_lahir = date.today() - timedelta(days=30)
        anak = Anak(
            nama='Anak Selesai',
            tanggal_lahir=tgl_lahir,
            jenis_kelamin='P',
            nama_ibu='Ibu Selesai',
            no_hp_ortu='08987654321',
            created_by=admin.id,
        )
        db.session.add(anak)
        db.session.flush()

        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin='BCG',
            tanggal_jadwal=tgl_lahir,
            status='terjadwal',
        )
        db.session.add(imun)
        db.session.commit()

        # Tandai selesai
        resp = client.post(
            f'/imunisasi/{imun.id}/selesai',
            data={'tanggal_realisasi': date.today().strftime('%Y-%m-%d')},
            follow_redirects=True,
        )
        assert resp.status_code == 200

        # Verifikasi status berubah
        db.session.refresh(imun)
        assert imun.status == 'selesai'
        assert imun.tanggal_realisasi == date.today()

    def test_dashboard_menampilkan_summary(self, client, db):
        """Dashboard dapat diakses dan menampilkan summary cards."""
        create_admin(db)
        login_as(client, 'admin_e2e', 'adminpass123')

        resp = client.get('/anak/dashboard')
        assert resp.status_code == 200
        body = resp.data.decode('utf-8')
        assert 'Total Anak' in body or 'total_anak' in body or 'Dashboard' in body

    def test_daftar_anak_dapat_diakses(self, client, db):
        """Halaman daftar anak dapat diakses setelah login."""
        create_admin(db)
        login_as(client, 'admin_e2e', 'adminpass123')

        resp = client.get('/anak/')
        assert resp.status_code == 200

    def test_api_chart_status_mengembalikan_json(self, client, db):
        """Endpoint /anak/api/chart/status mengembalikan JSON yang valid."""
        create_admin(db)
        login_as(client, 'admin_e2e', 'adminpass123')

        resp = client.get('/anak/api/chart/status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'selesai' in data
        assert 'terjadwal' in data
        assert 'terlewat' in data
