"""
blueprints/notifikasi/routes.py — Route notifikasi WhatsApp.

Routes:
    GET  /notifikasi/              — Daftar anak dengan jadwal mendatang + riwayat log
    POST /notifikasi/kirim/<id>    — Kirim notifikasi ke satu anak
    POST /notifikasi/kirim-semua   — Kirim ke semua anak dengan jadwal 7 hari ke depan
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from blueprints.notifikasi import notifikasi_bp
from models import Anak, NotifikasiLog
from services.imunisasi_service import get_imunisasi_mendatang
from services.wa_service import format_pesan_wa, kirim_dan_log
from flask import current_app


@notifikasi_bp.route("/")
@login_required
def index():
    """Halaman notifikasi: daftar anak dengan jadwal mendatang + riwayat 20 log terakhir."""
    mendatang = get_imunisasi_mendatang(days=7)
    riwayat = (
        NotifikasiLog.query
        .order_by(NotifikasiLog.waktu_kirim.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "notifikasi/index.html",
        mendatang=mendatang,
        riwayat=riwayat,
    )


@notifikasi_bp.route("/kirim/<int:anak_id>", methods=["POST"])
@login_required
def kirim_notifikasi(anak_id):
    """Kirim notifikasi WhatsApp ke satu anak."""
    anak = Anak.query.get_or_404(anak_id)

    # Ambil imunisasi mendatang untuk anak ini
    mendatang = get_imunisasi_mendatang(days=7)
    imunisasi_anak = [i for i in mendatang if i.anak_id == anak_id]

    if not imunisasi_anak:
        flash(f"Tidak ada jadwal imunisasi mendatang untuk {anak.nama}.", "warning")
        return redirect(url_for("notifikasi.index"))

    nama_fasilitas = current_app.config.get("NAMA_FASILITAS", "Puskesmas")
    berhasil = 0
    gagal = 0

    for imun in imunisasi_anak:
        pesan = format_pesan_wa(anak.nama, imun.nama_vaksin, imun.tanggal_jadwal, nama_fasilitas)
        hasil = kirim_dan_log(anak.id, anak.no_hp_ortu, pesan)
        if hasil["success"]:
            berhasil += 1
        else:
            gagal += 1

    if berhasil > 0:
        flash(f"Notifikasi berhasil dikirim ke {anak.nama} ({berhasil} pesan).", "success")
    if gagal > 0:
        flash(f"{gagal} pesan gagal dikirim ke {anak.nama}. Cek riwayat untuk detail.", "danger")

    return redirect(url_for("notifikasi.index"))


@notifikasi_bp.route("/kirim-semua", methods=["POST"])
@login_required
def kirim_semua():
    """Kirim notifikasi WhatsApp ke semua anak dengan jadwal imunisasi dalam 7 hari ke depan."""
    mendatang = get_imunisasi_mendatang(days=7)

    if not mendatang:
        flash("Tidak ada jadwal imunisasi mendatang dalam 7 hari ke depan.", "info")
        return redirect(url_for("notifikasi.index"))

    nama_fasilitas = current_app.config.get("NAMA_FASILITAS", "Puskesmas")
    berhasil = 0
    gagal = 0

    for imun in mendatang:
        anak = imun.anak
        pesan = format_pesan_wa(anak.nama, imun.nama_vaksin, imun.tanggal_jadwal, nama_fasilitas)
        hasil = kirim_dan_log(anak.id, anak.no_hp_ortu, pesan)
        if hasil["success"]:
            berhasil += 1
        else:
            gagal += 1

    flash(
        f"Selesai kirim notifikasi: {berhasil} berhasil, {gagal} gagal dari {len(mendatang)} total.",
        "success" if gagal == 0 else "warning",
    )
    return redirect(url_for("notifikasi.index"))
