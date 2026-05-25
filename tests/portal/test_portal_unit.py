"""
Unit tests untuk Portal Ibu — services/portal_service.py dan blueprints/portal/routes.py.

Mencakup:
- Pure function tests: mask_nomor, validate_email_format, validate_password,
  validate_no_whatsapp, kelompokkan_jadwal
- Route tests: login, dashboard, detail anak, akses terlarang
"""

import types
from datetime import date, timedelta

import pytest

from services.portal_service import (
    kelompokkan_jadwal,
    mask_nomor,
    validate_email_format,
    validate_no_whatsapp,
    validate_password,
)


# ─────────────────────────────────────────────────────────────────────────────
# mask_nomor
# ─────────────────────────────────────────────────────────────────────────────

def test_mask_nomor_normal():
    """Nomor 11 digit — tampilkan 4 digit terakhir dengan prefix ****."""
    assert mask_nomor('08123456789') == '****6789'


def test_mask_nomor_pendek():
    """Nomor < 4 karakter — semua karakter diganti bintang."""
    assert mask_nomor('123') == '***'


def test_mask_nomor_kosong():
    """String kosong — kembalikan string kosong."""
    assert mask_nomor('') == ''


# ─────────────────────────────────────────────────────────────────────────────
# validate_email_format
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_email_valid():
    """Email standar dengan @ dan domain bertitik — valid."""
    assert validate_email_format('user@example.com') is True


def test_validate_email_tanpa_at():
    """Email tanpa karakter @ — tidak valid."""
    assert validate_email_format('userexample.com') is False


def test_validate_email_dua_at():
    """Email dengan dua karakter @@ — tidak valid."""
    assert validate_email_format('user@@example.com') is False


def test_validate_email_domain_tanpa_titik():
    """Email dengan domain tanpa titik — tidak valid."""
    assert validate_email_format('user@domain') is False


# ─────────────────────────────────────────────────────────────────────────────
# validate_password
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_password_valid():
    """Password >= 8 karakter dan cocok — tidak ada error."""
    assert validate_password('password123', 'password123') == []


def test_validate_password_terlalu_pendek():
    """Password < 8 karakter — error 'Password minimal 8 karakter.'."""
    errors = validate_password('short', 'short')
    assert 'Password minimal 8 karakter.' in errors


def test_validate_password_tidak_cocok():
    """Password dan konfirmasi berbeda — error 'Konfirmasi password tidak cocok.'."""
    errors = validate_password('password123', 'berbeda123')
    assert 'Konfirmasi password tidak cocok.' in errors


# ─────────────────────────────────────────────────────────────────────────────
# validate_no_whatsapp
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_no_wa_valid_08():
    """Nomor diawali 08 dengan panjang valid — valid."""
    assert validate_no_whatsapp('08123456789') is True


def test_validate_no_wa_valid_plus62():
    """Nomor diawali +62 dengan panjang valid — valid."""
    assert validate_no_whatsapp('+6281234567890') is True


def test_validate_no_wa_invalid_pendek():
    """Nomor terlalu pendek (< 10 digit) — tidak valid."""
    assert validate_no_whatsapp('12345') is False


def test_validate_no_wa_invalid_huruf():
    """Nomor mengandung huruf — tidak valid."""
    assert validate_no_whatsapp('abc') is False


# ─────────────────────────────────────────────────────────────────────────────
# kelompokkan_jadwal
# ─────────────────────────────────────────────────────────────────────────────

def _buat_jadwal(delta_hari: int, status: str):
    """Helper: buat objek jadwal sederhana menggunakan SimpleNamespace."""
    return types.SimpleNamespace(
        tanggal_jadwal=date.today() + timedelta(days=delta_hari),
        status=status,
    )


def test_kelompokkan_jadwal_mendatang():
    """Jadwal terjadwal H+3 (dalam 7 hari) masuk kategori mendatang."""
    today = date.today()
    jadwal = types.SimpleNamespace(
        tanggal_jadwal=today + timedelta(days=3),
        status='terjadwal',
    )
    result = kelompokkan_jadwal([jadwal], today)
    assert jadwal in result['mendatang']
    assert jadwal not in result['terjadwal']
    assert jadwal not in result['riwayat']


def test_kelompokkan_jadwal_terjadwal():
    """Jadwal terjadwal H+10 (lebih dari 7 hari) masuk kategori terjadwal."""
    today = date.today()
    jadwal = types.SimpleNamespace(
        tanggal_jadwal=today + timedelta(days=10),
        status='terjadwal',
    )
    result = kelompokkan_jadwal([jadwal], today)
    assert jadwal in result['terjadwal']
    assert jadwal not in result['mendatang']
    assert jadwal not in result['riwayat']


def test_kelompokkan_jadwal_selesai_ke_riwayat():
    """Jadwal dengan status selesai masuk kategori riwayat."""
    today = date.today()
    jadwal = types.SimpleNamespace(
        tanggal_jadwal=today - timedelta(days=5),
        status='selesai',
    )
    result = kelompokkan_jadwal([jadwal], today)
    assert jadwal in result['riwayat']
    assert jadwal not in result['mendatang']
    assert jadwal not in result['terjadwal']


def test_kelompokkan_jadwal_terlewat_ke_riwayat():
    """Jadwal dengan status terlewat masuk kategori riwayat."""
    today = date.today()
    jadwal = types.SimpleNamespace(
        tanggal_jadwal=today - timedelta(days=2),
        status='terlewat',
    )
    result = kelompokkan_jadwal([jadwal], today)
    assert jadwal in result['riwayat']
    assert jadwal not in result['mendatang']
    assert jadwal not in result['terjadwal']


def test_kelompokkan_jadwal_lewat_ke_riwayat():
    """Jadwal terjadwal H-1 (tanggal sudah lewat) masuk kategori riwayat."""
    today = date.today()
    jadwal = types.SimpleNamespace(
        tanggal_jadwal=today - timedelta(days=1),
        status='terjadwal',
    )
    result = kelompokkan_jadwal([jadwal], today)
    assert jadwal in result['riwayat']
    assert jadwal not in result['mendatang']
    assert jadwal not in result['terjadwal']


# ─────────────────────────────────────────────────────────────────────────────
# Route tests
# ─────────────────────────────────────────────────────────────────────────────

def test_get_portal_login(client):
    """GET /portal/login mengembalikan status 200."""
    response = client.get('/portal/login')
    assert response.status_code == 200


def test_post_portal_login_sukses(client, ibu_user):
    """POST /portal/login dengan kredensial valid redirect ke /portal/dashboard."""
    response = client.post(
        '/portal/login',
        data={'email': ibu_user.email, 'password': 'password123'},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert '/portal/dashboard' in response.headers['Location']


def test_post_portal_login_gagal(client, ibu_user):
    """POST /portal/login dengan password salah mengembalikan 200 dan pesan error."""
    response = client.post(
        '/portal/login',
        data={'email': ibu_user.email, 'password': 'salah_password'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'Email atau password salah.' in response.data.decode('utf-8')


def test_dashboard_tanpa_login(client):
    """GET /portal/dashboard tanpa login redirect ke /portal/login."""
    response = client.get('/portal/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/portal/login' in response.headers['Location']


def test_anak_detail_bukan_milik_ibu(portal_client):
    """Akses /portal/anak/99999 (bukan milik ibu) mengembalikan 403."""
    response = portal_client.get('/portal/anak/99999')
    assert response.status_code == 403


def test_portal_login_required_role_petugas(client, db):
    """Petugas yang sudah login mencoba akses /portal/dashboard mengembalikan 403."""
    from models import User

    # Buat akun petugas
    petugas = User(
        username='petugas_test',
        nama_lengkap='Petugas Test',
        email='petugas@test.com',
        role='petugas',
        is_active=True,
    )
    petugas.set_password('password123')
    db.session.add(petugas)
    db.session.commit()

    # Login sebagai petugas melalui route auth utama (menggunakan username)
    client.post(
        '/auth/login',
        data={'username': 'petugas_test', 'password': 'password123'},
        follow_redirects=True,
    )

    # Akses dashboard portal — harus 403 karena role bukan 'user'
    response = client.get('/portal/dashboard')
    assert response.status_code == 403
