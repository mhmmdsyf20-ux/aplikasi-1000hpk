"""
blueprints/imunisasi/routes.py — Route manajemen jadwal imunisasi.

Routes:
    GET  /imunisasi/                  — Daftar semua jadwal (filter status)
    POST /imunisasi/<id>/selesai      — Tandai imunisasi selesai
    GET  /imunisasi/mendatang         — Imunisasi 7 hari ke depan
"""

from datetime import datetime

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from blueprints.imunisasi import imunisasi_bp
from extensions import db
from models import Imunisasi, Anak
from services.imunisasi_service import (
    tandai_selesai,
    get_imunisasi_mendatang,
    update_status_terlewat,
)


@imunisasi_bp.route("/")
@login_required
def list_imunisasi():
    """Daftar semua jadwal imunisasi dengan filter opsional berdasarkan status."""
    update_status_terlewat()

    status_filter = request.args.get("status", "").strip()
    valid_statuses = {"terjadwal", "selesai", "terlewat"}

    query = (
        Imunisasi.query
        .join(Anak, Imunisasi.anak_id == Anak.id)
        .order_by(Imunisasi.tanggal_jadwal.asc())
    )

    if status_filter and status_filter in valid_statuses:
        query = query.filter(Imunisasi.status == status_filter)

    imunisasi_list = query.all()

    return render_template(
        "imunisasi/list.html",
        imunisasi_list=imunisasi_list,
        status_filter=status_filter,
    )


@imunisasi_bp.route("/<int:imunisasi_id>/selesai", methods=["POST"])
@login_required
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
@login_required
def imunisasi_mendatang():
    """Daftar imunisasi yang jatuh tempo dalam 7 hari ke depan."""
    update_status_terlewat()
    mendatang = get_imunisasi_mendatang(days=7)

    return render_template("imunisasi/mendatang.html", mendatang=mendatang)
