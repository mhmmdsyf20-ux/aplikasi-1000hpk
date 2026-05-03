"""
blueprints/auth/routes.py — Route autentikasi dan manajemen user.

Routes:
    GET/POST /auth/login          — Form login
    GET      /auth/logout         — Logout dan redirect ke login
    GET/POST /auth/admin/users    — Daftar & tambah user (Admin only)
    GET/POST /auth/admin/users/<id>/edit — Edit user (Admin only)
"""

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session,
)
from flask_login import login_user, logout_user, login_required, current_user

from blueprints.auth import auth_bp
from extensions import db
from models import User
from services.auth_service import authenticate_user, role_required


# ─────────────────────────────────────────────────────────────────────────────
# Login / Logout
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Halaman login.

    GET  — Tampilkan form login.
    POST — Validasi kredensial; jika valid login dan redirect ke dashboard,
           jika tidak tampilkan pesan error.
    """
    # Jika sudah login, langsung ke dashboard
    if current_user.is_authenticated:
        return redirect(url_for('anak.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = authenticate_user(username, password)
        if user:
            # Aktifkan session permanent agar PERMANENT_SESSION_LIFETIME berlaku
            session.permanent = True
            login_user(user)
            # Redirect ke halaman yang diminta sebelumnya (jika ada), atau dashboard
            next_page = request.args.get('next')
            try:
                dashboard_url = url_for('anak.dashboard')
            except Exception:
                # Blueprint anak belum diregistrasi (misal saat testing parsial)
                dashboard_url = url_for('auth.admin_users')
            return redirect(next_page or dashboard_url)
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Hapus sesi login dan redirect ke halaman login."""
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('auth.login'))


# ─────────────────────────────────────────────────────────────────────────────
# Manajemen User (Admin only)
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route('/admin/users', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_users():
    """
    Daftar semua user dan form tambah user baru.

    GET  — Tampilkan daftar user.
    POST — Buat user baru dari data form.
    """
    if request.method == 'POST':
        username     = request.form.get('username', '').strip()
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        role         = request.form.get('role', '').strip()
        password     = request.form.get('password', '')

        # Validasi field wajib
        errors = []
        if not username:
            errors.append('Username wajib diisi.')
        if not nama_lengkap:
            errors.append('Nama lengkap wajib diisi.')
        if role not in ('admin', 'petugas'):
            errors.append('Role harus admin atau petugas.')
        if not password:
            errors.append('Password wajib diisi.')

        # Cek duplikat username
        if username and User.query.filter_by(username=username).first():
            errors.append(f'Username "{username}" sudah digunakan.')

        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            new_user = User(
                username=username,
                nama_lengkap=nama_lengkap,
                role=role,
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f'User "{username}" berhasil ditambahkan.', 'success')
            return redirect(url_for('auth.admin_users'))

    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/users.html', users=users)


@auth_bp.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_user(user_id):
    """
    Edit data user yang sudah ada.

    GET  — Tampilkan form edit dengan data user saat ini.
    POST — Simpan perubahan nama_lengkap, role, is_active, dan password (opsional).
    """
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        role         = request.form.get('role', '').strip()
        is_active    = request.form.get('is_active') == '1'
        password     = request.form.get('password', '')

        # Validasi
        errors = []
        if not nama_lengkap:
            errors.append('Nama lengkap wajib diisi.')
        if role not in ('admin', 'petugas'):
            errors.append('Role harus admin atau petugas.')

        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            user.nama_lengkap = nama_lengkap
            user.role         = role
            user.is_active    = is_active

            # Update password hanya jika field diisi
            if password:
                user.set_password(password)

            db.session.commit()
            flash(f'User "{user.username}" berhasil diperbarui.', 'success')
            return redirect(url_for('auth.admin_users'))

    return render_template('auth/user_form.html', user=user)
