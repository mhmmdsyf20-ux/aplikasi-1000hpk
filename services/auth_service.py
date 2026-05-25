"""
services/auth_service.py — Layanan autentikasi dan otorisasi.

Menyediakan fungsi verifikasi kredensial dan decorator role-based access control.
"""

from functools import wraps

from flask import abort
from flask_login import current_user

from models import User
from services.master_service import master_only as master_only


def authenticate_user(username: str, password: str):
    """
    Verifikasi username dan password.

    Hanya user dengan is_active=True yang dapat login.

    Args:
        username: Username yang dimasukkan pengguna.
        password: Password plaintext yang dimasukkan pengguna.

    Returns:
        User instance jika kredensial valid, None jika tidak.
    """
    user = User.query.filter_by(username=username, is_active=True).first()
    if user and user.check_password(password):
        return user
    return None


# Expose alias for backward compatibility
petugas_only = master_only


def role_required(*roles):
    """
    Decorator untuk membatasi akses berdasarkan role pengguna.

    Harus digunakan setelah @login_required agar current_user sudah terisi.

    Args:
        *roles: Satu atau lebih nama role yang diizinkan, misal 'admin'.

    Returns:
        Decorator function.

    Raises:
        401: Jika pengguna belum terautentikasi.
        403: Jika role pengguna tidak termasuk dalam roles yang diizinkan.

    Contoh:
        @login_required
        @role_required('admin')
        def halaman_admin():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
