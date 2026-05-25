"""
tests/test_auth.py — Unit tests untuk autentikasi dan manajemen user.

Mencakup:
- Login berhasil / gagal (password salah, username tidak ada, user nonaktif)
- Logout
- Proteksi route dengan @login_required
- Akses route admin berdasarkan role
- Tambah user baru oleh admin (berhasil & duplikat username)
"""

import pytest
from models import User


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def create_user(db, username, role, password, nama_lengkap=None, is_active=True):
    """
    Buat dan simpan User ke database untuk keperluan testing.

    Args:
        db          : SQLAlchemy db fixture.
        username    : Username unik.
        role        : 'admin' atau 'petugas'.
        password    : Password plaintext.
        nama_lengkap: Nama lengkap (opsional, default dari username).
        is_active   : Status aktif akun (default True).

    Returns:
        User instance yang sudah tersimpan.
    """
    user = User(
        username=username,
        role=role,
        nama_lengkap=nama_lengkap or f"User {username}",
        is_active=is_active,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username, password):
    """Helper untuk melakukan POST ke /auth/login."""
    return client.post(
        '/auth/login',
        data={'username': username, 'password': password},
        follow_redirects=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Login
# ─────────────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_berhasil_redirect_ke_dashboard(self, client, db):
        """Login dengan kredensial valid → redirect 302 (bukan ke halaman login)."""
        create_user(db, username='petugas1', role='petugas', password='rahasia123')

        resp = login(client, 'petugas1', 'rahasia123')

        assert resp.status_code == 302
        # Setelah login berhasil, redirect ke mana saja kecuali halaman login itu sendiri
        assert '/auth/login' not in resp.location

    def test_login_gagal_password_salah(self, client, db):
        """Login dengan password salah → flash error, status 200."""
        create_user(db, username='petugas2', role='petugas', password='benar123')

        resp = client.post(
            '/auth/login',
            data={'username': 'petugas2', 'password': 'salah999'},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        assert 'Username atau password salah' in resp.data.decode('utf-8')

    def test_login_gagal_username_tidak_ada(self, client, db):
        """Login dengan username yang tidak terdaftar → flash error, status 200."""
        resp = client.post(
            '/auth/login',
            data={'username': 'tidakada', 'password': 'apapun'},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        assert 'Username atau password salah' in resp.data.decode('utf-8')

    def test_login_gagal_user_nonaktif(self, client, db):
        """Login dengan user is_active=False → flash error."""
        create_user(db, username='nonaktif', role='petugas', password='rahasia123', is_active=False)

        resp = client.post(
            '/auth/login',
            data={'username': 'nonaktif', 'password': 'rahasia123'},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        assert 'Username atau password salah' in resp.data.decode('utf-8')


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Logout
# ─────────────────────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_berhasil_redirect_ke_login(self, client, db):
        """Logout setelah login → redirect 302 ke halaman login."""
        create_user(db, username='petugas3', role='petugas', password='rahasia123')
        login(client, 'petugas3', 'rahasia123')

        resp = client.get('/auth/logout', follow_redirects=False)

        assert resp.status_code == 302
        assert '/auth/login' in resp.location


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Proteksi route (login_required)
# ─────────────────────────────────────────────────────────────────────────────

class TestProteksiRoute:
    def test_akses_route_admin_tanpa_login_redirect_ke_login(self, client, db):
        """Akses /auth/admin/users tanpa login → 401 (petugas_only decorator)."""
        resp = client.get('/auth/admin/users', follow_redirects=False)

        # petugas_only mengembalikan 401 untuk pengguna yang belum autentikasi
        assert resp.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Role-based access control
# ─────────────────────────────────────────────────────────────────────────────

class TestRoleAccess:
    def test_akses_route_admin_dengan_role_petugas_forbidden(self, client, db):
        """Petugas mengakses /auth/admin/users → status 403."""
        create_user(db, username='petugas4', role='petugas', password='rahasia123')
        login(client, 'petugas4', 'rahasia123')

        resp = client.get('/auth/admin/users', follow_redirects=False)

        assert resp.status_code == 403

    def test_akses_route_admin_dengan_role_admin_berhasil(self, client, db):
        """Admin mengakses /auth/admin/users → status 200."""
        create_user(db, username='admin1', role='admin', password='adminpass')
        login(client, 'admin1', 'adminpass')

        resp = client.get('/auth/admin/users', follow_redirects=False)

        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Manajemen User (Admin)
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminUsers:
    def _login_as_admin(self, client, db):
        """Helper: buat admin dan login."""
        create_user(db, username='admintest', role='admin', password='adminpass')
        login(client, 'admintest', 'adminpass')

    def test_tambah_user_baru_berhasil(self, client, db):
        """Admin menambah user baru → berhasil, user tersimpan di DB."""
        self._login_as_admin(client, db)

        resp = client.post(
            '/auth/admin/users',
            data={
                'username': 'userbaru',
                'nama_lengkap': 'User Baru',
                'role': 'petugas',
                'password': 'password123',
            },
            follow_redirects=True,
        )

        assert resp.status_code == 200
        # Verifikasi user tersimpan di database
        user = User.query.filter_by(username='userbaru').first()
        assert user is not None
        assert user.role == 'petugas'
        assert user.nama_lengkap == 'User Baru'

    def test_tambah_user_duplikat_username_flash_error(self, client, db):
        """Admin menambah user dengan username yang sudah ada → flash error."""
        self._login_as_admin(client, db)
        # Buat user yang sudah ada terlebih dahulu
        create_user(db, username='duplikat', role='petugas', password='pass123')

        resp = client.post(
            '/auth/admin/users',
            data={
                'username': 'duplikat',
                'nama_lengkap': 'User Duplikat',
                'role': 'petugas',
                'password': 'password123',
            },
            follow_redirects=True,
        )

        assert resp.status_code == 200
        body = resp.data.decode('utf-8')
        # Flash error berisi pesan duplikat username
        assert 'sudah digunakan' in body or 'duplikat' in body.lower()
