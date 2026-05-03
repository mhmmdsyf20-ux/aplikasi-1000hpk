"""
blueprints/anak/routes.py — Route CRUD data anak dan dashboard utama.

Routes:
    GET      /anak/dashboard          — Dashboard utama dengan summary cards
    GET      /anak/                   — Daftar anak dengan search & pagination
    GET/POST /anak/tambah             — Form tambah anak baru
    GET/POST /anak/<id>/edit          — Form edit data anak
    GET      /anak/<id>               — Detail anak + daftar imunisasi
"""

from datetime import date, timedelta, datetime

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from blueprints.anak import anak_bp
from extensions import db
from models import Anak, Imunisasi
from services.anak_service import validate_anak_data
from services.imunisasi_service import generate_jadwal_imunisasi, update_status_terlewat
_HAS_IMUNISASI_SERVICE = True


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@anak_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard utama aplikasi 1000 HPK."""
    # Update status imunisasi terlewat setiap kali dashboard dibuka
    update_status_terlewat()

    today = date.today()
    next_7 = today + timedelta(days=7)

    total_anak = Anak.query.count()

    imunisasi_hari_ini = Imunisasi.query.filter(
        Imunisasi.tanggal_jadwal == today,
        Imunisasi.status == 'terjadwal',
    ).count()

    imunisasi_mendatang = Imunisasi.query.filter(
        Imunisasi.tanggal_jadwal > today,
        Imunisasi.tanggal_jadwal <= next_7,
        Imunisasi.status == 'terjadwal',
    ).count()

    imunisasi_terlewat = Imunisasi.query.filter(
        Imunisasi.status == 'terlewat',
    ).count()

    jadwal_mendatang = (
        Imunisasi.query
        .filter(
            Imunisasi.tanggal_jadwal >= today,
            Imunisasi.tanggal_jadwal <= next_7,
            Imunisasi.status == 'terjadwal',
        )
        .order_by(Imunisasi.tanggal_jadwal.asc())
        .all()
    )

    return render_template(
        'anak/dashboard.html',
        total_anak=total_anak,
        imunisasi_hari_ini=imunisasi_hari_ini,
        imunisasi_mendatang=imunisasi_mendatang,
        imunisasi_terlewat=imunisasi_terlewat,
        jadwal_mendatang=jadwal_mendatang,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Daftar Anak
# ─────────────────────────────────────────────────────────────────────────────

@anak_bp.route('/')
@login_required
def list_anak():
    """Daftar semua anak dengan fitur pencarian dan pagination."""
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Anak.query

    if q:
        like_q = f'%{q}%'
        query = query.filter(
            db.or_(
                Anak.nama.ilike(like_q),
                Anak.nama_ibu.ilike(like_q),
            )
        )

    pagination = query.order_by(Anak.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        'anak/list.html',
        anak_list=pagination.items,
        pagination=pagination,
        q=q,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tambah Anak
# ─────────────────────────────────────────────────────────────────────────────

@anak_bp.route('/tambah', methods=['GET', 'POST'])
@login_required
def tambah_anak():
    """Form tambah anak baru."""
    if request.method == 'POST':
        data = {
            'nama': request.form.get('nama', '').strip(),
            'tanggal_lahir': request.form.get('tanggal_lahir', '').strip(),
            'jenis_kelamin': request.form.get('jenis_kelamin', '').strip(),
            'nama_ibu': request.form.get('nama_ibu', '').strip(),
            'no_hp_ortu': request.form.get('no_hp_ortu', '').strip(),
            'alamat': request.form.get('alamat', '').strip(),
            'berat_lahir': request.form.get('berat_lahir', '').strip(),
            'panjang_lahir': request.form.get('panjang_lahir', '').strip(),
        }

        errors = validate_anak_data(data)

        tanggal_lahir = None
        if data['tanggal_lahir']:
            try:
                tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
            except ValueError:
                errors.append('Format tanggal lahir tidak valid.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('anak/form.html', data=data, mode='tambah')

        anak = Anak(
            nama=data['nama'],
            tanggal_lahir=tanggal_lahir,
            jenis_kelamin=data['jenis_kelamin'],
            nama_ibu=data['nama_ibu'],
            no_hp_ortu=data['no_hp_ortu'],
            alamat=data['alamat'] or None,
            berat_lahir=float(data['berat_lahir']) if data['berat_lahir'] else None,
            panjang_lahir=float(data['panjang_lahir']) if data['panjang_lahir'] else None,
            created_by=current_user.id,
        )
        db.session.add(anak)
        db.session.flush()

        try:
            jadwal_list = generate_jadwal_imunisasi(tanggal_lahir)
            for jadwal in jadwal_list:
                imun = Imunisasi(
                    anak_id=anak.id,
                    nama_vaksin=jadwal['nama_vaksin'],
                    tanggal_jadwal=jadwal['tanggal_jadwal'],
                    status='terjadwal',
                )
                db.session.add(imun)
        except Exception as e:
            flash(f'Peringatan: Gagal membuat jadwal imunisasi otomatis. {e}', 'warning')

        db.session.commit()
        flash(f'Data anak "{anak.nama}" berhasil disimpan.', 'success')
        return redirect(url_for('anak.detail_anak', anak_id=anak.id))

    return render_template('anak/form.html', data={}, mode='tambah')


# ─────────────────────────────────────────────────────────────────────────────
# Edit Anak
# ─────────────────────────────────────────────────────────────────────────────

@anak_bp.route('/<int:anak_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_anak(anak_id):
    """Form edit data anak yang sudah ada."""
    anak = Anak.query.get_or_404(anak_id)

    if request.method == 'POST':
        data = {
            'nama': request.form.get('nama', '').strip(),
            'tanggal_lahir': request.form.get('tanggal_lahir', '').strip(),
            'jenis_kelamin': request.form.get('jenis_kelamin', '').strip(),
            'nama_ibu': request.form.get('nama_ibu', '').strip(),
            'no_hp_ortu': request.form.get('no_hp_ortu', '').strip(),
            'alamat': request.form.get('alamat', '').strip(),
            'berat_lahir': request.form.get('berat_lahir', '').strip(),
            'panjang_lahir': request.form.get('panjang_lahir', '').strip(),
        }

        errors = validate_anak_data(data)

        tanggal_lahir = None
        if data['tanggal_lahir']:
            try:
                tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
            except ValueError:
                errors.append('Format tanggal lahir tidak valid.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('anak/form.html', data=data, anak=anak, mode='edit')

        anak.nama = data['nama']
        anak.tanggal_lahir = tanggal_lahir
        anak.jenis_kelamin = data['jenis_kelamin']
        anak.nama_ibu = data['nama_ibu']
        anak.no_hp_ortu = data['no_hp_ortu']
        anak.alamat = data['alamat'] or None
        anak.berat_lahir = float(data['berat_lahir']) if data['berat_lahir'] else None
        anak.panjang_lahir = float(data['panjang_lahir']) if data['panjang_lahir'] else None

        db.session.commit()
        flash(f'Data anak "{anak.nama}" berhasil diperbarui.', 'success')
        return redirect(url_for('anak.detail_anak', anak_id=anak.id))

    data = {
        'nama': anak.nama,
        'tanggal_lahir': anak.tanggal_lahir.strftime('%Y-%m-%d') if anak.tanggal_lahir else '',
        'jenis_kelamin': anak.jenis_kelamin,
        'nama_ibu': anak.nama_ibu,
        'no_hp_ortu': anak.no_hp_ortu,
        'alamat': anak.alamat or '',
        'berat_lahir': str(anak.berat_lahir) if anak.berat_lahir else '',
        'panjang_lahir': str(anak.panjang_lahir) if anak.panjang_lahir else '',
    }

    return render_template('anak/form.html', data=data, anak=anak, mode='edit')


# ─────────────────────────────────────────────────────────────────────────────
# Detail Anak
# ─────────────────────────────────────────────────────────────────────────────

@anak_bp.route('/<int:anak_id>')
@login_required
def detail_anak(anak_id):
    """Halaman detail anak beserta daftar imunisasi."""
    anak = Anak.query.get_or_404(anak_id)
    imunisasi_list = (
        Imunisasi.query
        .filter_by(anak_id=anak_id)
        .order_by(Imunisasi.tanggal_jadwal.asc())
        .all()
    )

    return render_template(
        'anak/detail.html',
        anak=anak,
        imunisasi_list=imunisasi_list,
    )


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints untuk Chart.js
# ─────────────────────────────────────────────────────────────────────────────

from flask import jsonify
from datetime import date as _date
from calendar import month_abbr


@anak_bp.route('/api/chart/status')
@login_required
def api_chart_status():
    """Endpoint JSON untuk donut chart status imunisasi."""
    selesai = Imunisasi.query.filter_by(status='selesai').count()
    terjadwal = Imunisasi.query.filter_by(status='terjadwal').count()
    terlewat = Imunisasi.query.filter_by(status='terlewat').count()
    return jsonify({"selesai": selesai, "terjadwal": terjadwal, "terlewat": terlewat})


@anak_bp.route('/api/chart/bulanan')
@login_required
def api_chart_bulanan():
    """Endpoint JSON untuk bar chart imunisasi selesai per bulan (6 bulan terakhir)."""
    from datetime import timedelta
    today = _date.today()
    labels = []
    values = []

    for i in range(5, -1, -1):
        # Hitung bulan ke-i yang lalu
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        label = f"{month_abbr[month]} {year}"
        labels.append(label)

        # Hitung imunisasi selesai di bulan tersebut
        count = Imunisasi.query.filter(
            db.extract('year', Imunisasi.tanggal_realisasi) == year,
            db.extract('month', Imunisasi.tanggal_realisasi) == month,
            Imunisasi.status == 'selesai',
        ).count()
        values.append(count)

    return jsonify({"labels": labels, "values": values})


@anak_bp.route('/api/chart/progress/<int:anak_id>')
@login_required
def api_chart_progress(anak_id):
    """Endpoint JSON untuk progress imunisasi per anak."""
    from services.laporan_service import hitung_progress_anak
    progress = hitung_progress_anak(anak_id)
    total = Imunisasi.query.filter_by(anak_id=anak_id).count()
    selesai = Imunisasi.query.filter_by(anak_id=anak_id, status='selesai').count()
    return jsonify({"progress": progress, "selesai": selesai, "total": total})
