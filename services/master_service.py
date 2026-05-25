"""
services/master_service.py — Otorisasi untuk role master.

Master di sini adalah istilah gabungan untuk akun admin dan petugas.
Semua route khusus petugas/admin (master) harus menggunakan decorator ini.
"""

from functools import wraps

from flask import abort
from flask_login import current_user


def master_only(f):
    """Decorator: hanya izinkan akses untuk master (admin atau petugas)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ('admin', 'petugas'):
            abort(403)
        return f(*args, **kwargs)
    return decorated
