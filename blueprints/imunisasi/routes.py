"""
blueprints/imunisasi/routes.py — Route manajemen jadwal imunisasi.

Routes:
    GET  /imunisasi/                  — Daftar semua jadwal (filter status)
    POST /imunisasi/<id>/selesai      — Tandai imunisasi selesai
    GET  /imunisasi/mendatang         — Imunisasi 7 hari ke depan
"""

from datetime import datetime

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user

from blueprints.imunisasi import imunisasi_bp
from extensions import db
from models import Imunisasi, Anak
from services.master_service import master_only
from services.imunisasi_service import (
    tandai_selesai,
    get_imunisasi_mendatang,
    update_status_terlewat,
)


@imunisasi_bp.route("/")
@master_only
def list_imunisasi():
    """Daftar semua jadwal imunisasi dengan filter status, bulan, dan tahun."""
    from datetime import date
    from sqlalchemy import extract

    update_status_terlewat()

    status_filter = request.args.get("status", "").strip()
    bulan_filter = request.args.get("bulan", "", type=int) or None
    tahun_filter = request.args.get("tahun", "", type=int) or None

    query = (
        Imunisasi.query
        .join(Anak, Imunisasi.anak_id == Anak.id)
        .order_by(Imunisasi.tanggal_jadwal.asc())
    )

    # Filter status — "belum" = terjadwal + terlewat (belum terlaksana)
    if status_filter == "belum":
        query = query.filter(Imunisasi.status.in_(["terjadwal", "terlewat"]))
    elif status_filter in {"terjadwal", "selesai", "terlewat"}:
        query = query.filter(Imunisasi.status == status_filter)

    if bulan_filter:
        query = query.filter(extract('month', Imunisasi.tanggal_jadwal) == bulan_filter)
    if tahun_filter:
        query = query.filter(extract('year', Imunisasi.tanggal_jadwal) == tahun_filter)

    imunisasi_list = query.all()

    # Hitung summary
    from extensions import db as _db
    total_terjadwal = Imunisasi.query.filter_by(status='terjadwal').count()
    total_selesai   = Imunisasi.query.filter_by(status='selesai').count()
    total_terlewat  = Imunisasi.query.filter_by(status='terlewat').count()
    total_belum     = total_terjadwal + total_terlewat

    # Daftar tahun untuk dropdown — pakai extract agar kompatibel SQLite & PostgreSQL
    from sqlalchemy import extract as sa_extract
    tahun_rows = _db.session.query(
        sa_extract('year', Imunisasi.tanggal_jadwal)
    ).distinct().order_by(sa_extract('year', Imunisasi.tanggal_jadwal).desc()).all()
    tahun_list = [int(r[0]) for r in tahun_rows if r[0]]

    return render_template(
        "imunisasi/list.html",
        imunisasi_list=imunisasi_list,
        status_filter=status_filter,
        bulan_filter=bulan_filter,
        tahun_filter=tahun_filter,
        tahun_list=tahun_list,
        total_terjadwal=total_terjadwal,
        total_selesai=total_selesai,
        total_terlewat=total_terlewat,
        total_belum=total_belum,
    )


@imunisasi_bp.route("/<int:imunisasi_id>/selesai", methods=["POST"])
@master_only
def tandai_imunisasi_selesai(imunisasi_id):
    """Tandai imunisasi sebagai selesai dengan tanggal realisasi."""
    tanggal_str = request.form.get("tanggal_realisasi", "").strip()
    catatan = request.form.get("catatan", "").strip()

    if not tanggal_str:
        flash("Tanggal realisasi wajib diisi.", "danger")
        return redirect(request.referrer or url_for("imunisasi.list_imunisasi"))

    try:
        tanggal_realisasi = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Format tanggal realisasi tidak valid.", "danger")
        return redirect(request.referrer or url_for("imunisasi.list_imunisasi"))

    imunisasi = tandai_selesai(imunisasi_id, tanggal_realisasi, current_user.id)

    if catatan:
        imunisasi.catatan = catatan
        db.session.commit()

    flash(f"Imunisasi {imunisasi.nama_vaksin} berhasil ditandai selesai.", "success")
    return redirect(url_for("anak.detail_anak", anak_id=imunisasi.anak_id))


@imunisasi_bp.route("/mendatang")
@master_only
def imunisasi_mendatang():
    """Daftar imunisasi yang jatuh tempo dalam 7 hari ke depan."""
    update_status_terlewat()
    mendatang = get_imunisasi_mendatang(days=7)

    return render_template("imunisasi/mendatang.html", mendatang=mendatang)
