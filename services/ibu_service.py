"""
services/ibu_service.py — Otorisasi untuk Portal Ibu / orang tua.

Decorator ini khusus untuk route Portal Ibu dan dipisahkan dari
otorisasi master/admin/petugas.
"""

from functools import wraps

from flask import abort, redirect, url_for
from flask_login import current_user


def portal_login_required(f):
    """Decorator untuk melindungi route Portal Ibu dengan login dan role 'user'."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('portal.portal_login'))
        if current_user.role != 'user':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
