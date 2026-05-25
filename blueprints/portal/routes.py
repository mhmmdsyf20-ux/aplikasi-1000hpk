"""
blueprints/portal/routes.py — Route Portal Ibu/Orang Tua.

Routes autentikasi:
    GET/POST /portal/login                      — Form login ibu (portal_login)
    GET/POST /portal/register                   — Form registrasi ibu (portal_register)
    GET      /portal/logout                     — Logout ibu (portal_logout)

Routes terproteksi (memerlukan login sebagai role 'user'):
    GET      /portal/dashboard                  — Dashboard utama ibu (portal_dashboard)
    GET      /portal/anak                       — Daftar anak milik ibu (portal_list_anak)
    GET      /portal/anak/<int:anak_id>         — Detail anak (portal_detail_anak)
    GET      /portal/anak/<int:anak_id>/jadwal  — Jadwal imunisasi anak (portal_jadwal_anak)
    GET      /portal/notifikasi                 — Riwayat notifikasi (portal_notifikasi)
"""

import random

from flask import flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_user, logout_user

from blueprints.portal import portal_bp
from blueprints.portal.decorators import portal_login_required
from extensions import db
from models import User
from services.portal_service import (
    validate_email_format,
    validate_no_whatsapp,
    validate_password,
    get_dashboard_stats,
    get_anak_by_ibu,
    get_anak_or_403,
    get_jadwal_anak,
    get_notifikasi_ibu,
    hitung_persentase_imunisasi,
    mask_nomor,
)


# ─────────────────────────────────────────────────────────────────────────────
# Index — redirect /portal ke /portal/login
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/')
def portal_index():
    """Redirect /portal ke halaman login portal ibu."""
    return redirect(url_for('portal.portal_login'))


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/login', methods=['GET', 'POST'])
def portal_login():
    """
    Halaman login Portal Ibu.

    GET  — Tampilkan form login. Redirect ke dashboard jika sudah login sebagai 'user'.
    POST — Validasi email dan password; jika valid login dan redirect ke dashboard,
           jika tidak tampilkan pesan error.
    """
    # Jika sudah login sebagai ibu, langsung ke dashboard
    if current_user.is_authenticated and current_user.role == 'user':
        return redirect(url_for('portal.portal_dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email, is_active=True).first()

        if user and user.role == 'user' and user.check_password(password):
            login_user(user)
            current_app.logger.info(
                f"Portal login berhasil: user_id={user.id} email={user.email}"
            )
            flash(f"Selamat datang, {user.nama_lengkap}!", 'success')
            return redirect(url_for('portal.portal_dashboard'))
        else:
            current_app.logger.warning(
                f"Portal login gagal: email={email} ip={request.remote_addr}"
            )
            flash('Email atau password salah.', 'danger')

    return render_template('portal/auth/login.html')


# ─────────────────────────────────────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/register', methods=['GET', 'POST'])
def portal_register():
    """
    Halaman registrasi Portal Ibu.

    GET  — Tampilkan form registrasi.
    POST — Validasi data, buat akun baru, redirect ke halaman login.
    """
    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        email        = request.form.get('email', '').strip()
        no_whatsapp  = request.form.get('no_whatsapp', '').strip()
        password     = request.form.get('password', '')
        konfirmasi   = request.form.get('konfirmasi', '')

        errors = []

        # Validasi field wajib
        if not nama_lengkap:
            errors.append('Nama lengkap wajib diisi.')
        if not email:
            errors.append('Email wajib diisi.')
        if not password:
            errors.append('Password wajib diisi.')
        if not konfirmasi:
            errors.append('Konfirmasi password wajib diisi.')

        # Validasi format email
        if email and not validate_email_format(email):
            errors.append('Format email tidak valid.')

        # Validasi password (hanya jika keduanya diisi)
        if password and konfirmasi:
            pw_errors = validate_password(password, konfirmasi)
            errors.extend(pw_errors)

        # Validasi nomor WhatsApp (opsional, hanya jika diisi)
        if no_whatsapp and not validate_no_whatsapp(no_whatsapp):
            errors.append('Format nomor WhatsApp tidak valid.')

        # Cek duplikasi email
        if email and not errors:
            existing = User.query.filter_by(email=email).first()
            if existing:
                errors.append('Email sudah terdaftar. Silakan gunakan email lain atau login.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('portal/auth/register.html')

        # Generate username unik dari bagian sebelum '@' pada email
        base_username = email.split('@')[0]
        username = base_username
        if User.query.filter_by(username=username).first():
            # Tambahkan suffix 4 digit acak jika username sudah ada
            suffix = random.randint(1000, 9999)
            username = f"{base_username}{suffix}"
            # Pastikan benar-benar unik (loop jika masih bentrok)
            while User.query.filter_by(username=username).first():
                suffix = random.randint(1000, 9999)
                username = f"{base_username}{suffix}"

        # Buat user baru
        new_user = User(
            username=username,
            nama_lengkap=nama_lengkap,
            email=email,
            no_whatsapp=no_whatsapp if no_whatsapp else None,
            role='user',
            is_active=True,
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(
            f"Portal registrasi berhasil: user_id={new_user.id} email={new_user.email}"
        )
        flash('Registrasi berhasil. Silakan login.', 'success')
        return redirect(url_for('portal.portal_login'))

    return render_template('portal/auth/register.html')


# ─────────────────────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/logout')
def portal_logout():
    """Hapus sesi login ibu dan redirect ke halaman login portal."""
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('portal.portal_login'))


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/dashboard')
@portal_login_required
def portal_dashboard():
    """
    Dashboard utama Portal Ibu.

    Menampilkan statistik ringkasan: total anak, jadwal mendatang,
    jadwal selesai, jadwal terlewat, dan progress imunisasi per anak.
    """
    stats = get_dashboard_stats(current_user.id)
    return render_template('portal/dashboard.html', stats=stats)


# ─────────────────────────────────────────────────────────────────────────────
# Daftar Anak
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/anak')
@portal_login_required
def portal_list_anak():
    """
    Halaman daftar anak milik ibu yang sedang login.

    Menampilkan semua anak beserta persentase kelengkapan imunisasi masing-masing.
    """
    anak_list = get_anak_by_ibu(current_user.id)
    anak_progress = [
        {'anak': anak, 'persen': hitung_persentase_imunisasi(anak.id)}
        for anak in anak_list
    ]
    return render_template(
        'portal/anak/list.html',
        anak_list=anak_list,
        anak_progress=anak_progress,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Detail Anak
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/anak/<int:anak_id>')
@portal_login_required
def portal_detail_anak(anak_id):
    """
    Halaman detail anak.

    Menampilkan informasi lengkap anak. Mengembalikan 403 jika anak
    tidak ditemukan atau bukan milik ibu yang sedang login.
    """
    anak = get_anak_or_403(anak_id, current_user.id)
    return render_template('portal/anak/detail.html', anak=anak)


# ─────────────────────────────────────────────────────────────────────────────
# Jadwal Imunisasi Anak
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/anak/<int:anak_id>/jadwal')
@portal_login_required
def portal_jadwal_anak(anak_id):
    """
    Halaman jadwal imunisasi anak.

    Menampilkan jadwal imunisasi yang dikelompokkan ke dalam tiga kategori:
    mendatang (7 hari ke depan), terjadwal (lebih dari 7 hari), dan riwayat.
    Mengembalikan 403 jika anak bukan milik ibu yang sedang login.
    """
    data = get_jadwal_anak(anak_id, current_user.id)
    return render_template('portal/anak/jadwal.html', **data)


# ─────────────────────────────────────────────────────────────────────────────
# Notifikasi
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/notifikasi')
@portal_login_required
def portal_notifikasi():
    """
    Halaman riwayat notifikasi ibu.

    Menampilkan notifikasi WhatsApp yang telah dikirim untuk semua anak
    milik ibu yang sedang login, diurutkan dari yang terbaru.
    Nomor tujuan ditampilkan dalam format masking (****XXXX).
    """
    notifikasi_list = get_notifikasi_ibu(current_user.id)
    return render_template(
        'portal/notifikasi/index.html',
        notifikasi_list=notifikasi_list,
        mask_nomor=mask_nomor,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Profil Ibu
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/profil', methods=['GET', 'POST'])
@portal_login_required
def portal_profil():
    """Halaman lengkapi/edit profil ibu."""
    if request.method == 'POST':
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        no_whatsapp  = request.form.get('no_whatsapp', '').strip()

        errors = []
        if not nama_lengkap:
            errors.append('Nama lengkap wajib diisi.')
        if no_whatsapp and not validate_no_whatsapp(no_whatsapp):
            errors.append('Format nomor WhatsApp tidak valid (contoh: 08123456789).')

        if errors:
            for err in errors:
                flash(err, 'danger')
        else:
            current_user.nama_lengkap = nama_lengkap
            current_user.no_whatsapp  = no_whatsapp if no_whatsapp else current_user.no_whatsapp
            db.session.commit()
            flash('Profil berhasil diperbarui.', 'success')
            return redirect(url_for('portal.portal_dashboard'))

    return render_template('portal/profil.html')


# ─────────────────────────────────────────────────────────────────────────────
# Tambah Anak (oleh ibu sendiri)
# ─────────────────────────────────────────────────────────────────────────────

@portal_bp.route('/anak/tambah', methods=['GET', 'POST'])
@portal_login_required
def portal_tambah_anak():
    """Form tambah anak baru oleh ibu."""
    from datetime import datetime, date as _date
    from models import Anak, Imunisasi
    from services.imunisasi_service import generate_jadwal_imunisasi

    if request.method == 'POST':
        nama           = request.form.get('nama', '').strip()
        tanggal_lahir_str = request.form.get('tanggal_lahir', '').strip()
        jenis_kelamin  = request.form.get('jenis_kelamin', '').strip()
        no_hp_ortu     = request.form.get('no_hp_ortu', '').strip()
        alamat         = request.form.get('alamat', '').strip()
        berat_lahir    = request.form.get('berat_lahir', '').strip()
        panjang_lahir  = request.form.get('panjang_lahir', '').strip()

        errors = []
        if not nama:
            errors.append('Nama anak wajib diisi.')
        if not tanggal_lahir_str:
            errors.append('Tanggal lahir wajib diisi.')
        if jenis_kelamin not in ('L', 'P'):
            errors.append('Jenis kelamin wajib dipilih.')
        if not no_hp_ortu:
            errors.append('Nomor HP orang tua wajib diisi.')

        tanggal_lahir = None
        if tanggal_lahir_str:
            try:
                tanggal_lahir = datetime.strptime(tanggal_lahir_str, '%Y-%m-%d').date()
                umur_hari = (_date.today() - tanggal_lahir).days
                if umur_hari < 0:
                    errors.append('Tanggal lahir tidak boleh di masa depan.')
                elif umur_hari > 730:
                    errors.append('Aplikasi hanya untuk anak usia 0–2 tahun.')
            except ValueError:
                errors.append('Format tanggal lahir tidak valid.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('portal/anak/tambah.html',
                                   today=_date.today().strftime('%Y-%m-%d'),
                                   min_date=(_date.today() - __import__('datetime').timedelta(days=730)).strftime('%Y-%m-%d'))

        anak = Anak(
            nama=nama,
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=jenis_kelamin,
            nama_ibu=current_user.nama_lengkap,
            no_hp_ortu=no_hp_ortu,
            alamat=alamat or None,
            berat_lahir=float(berat_lahir) if berat_lahir else None,
            panjang_lahir=float(panjang_lahir) if panjang_lahir else None,
            created_by=current_user.id,
        )
        db.session.add(anak)
        db.session.flush()

        jadwal_list = generate_jadwal_imunisasi(tanggal_lahir)
        for jadwal in jadwal_list:
            imun = Imunisasi(
                anak_id=anak.id,
                nama_vaksin=jadwal['nama_vaksin'],
                tanggal_jadwal=jadwal['tanggal_jadwal'],
                status='terjadwal',
            )
            db.session.add(imun)

        db.session.commit()
        flash(f'Data anak "{anak.nama}" berhasil didaftarkan. Jadwal imunisasi otomatis dibuat.', 'success')
        return redirect(url_for('portal.portal_jadwal_anak', anak_id=anak.id))

    from datetime import timedelta, date as _date
    return render_template('portal/anak/tambah.html',
                           today=_date.today().strftime('%Y-%m-%d'),
                           min_date=(_date.today() - timedelta(days=730)).strftime('%Y-%m-%d'))
