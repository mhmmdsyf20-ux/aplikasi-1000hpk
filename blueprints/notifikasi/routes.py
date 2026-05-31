"""
blueprints/notifikasi/routes.py — Route notifikasi WhatsApp.

Routes:
    GET  /notifikasi/              — Daftar anak dengan jadwal mendatang + riwayat log
    POST /notifikasi/kirim/<id>    — Kirim notifikasi ke satu anak
    POST /notifikasi/kirim-semua   — Kirim ke semua anak dengan jadwal 30 hari ke depan
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user
from datetime import date

from blueprints.notifikasi import notifikasi_bp
from models import Anak, NotifikasiLog, Imunisasi
from services.master_service import master_only
from services.imunisasi_service import get_imunisasi_mendatang, update_status_terlewat
from services.wa_service import format_pesan_wa, kirim_dan_log


@notifikasi_bp.route("/")
@master_only
def index():
    """Halaman notifikasi: jadwal mendatang, imunisasi terlewat, dan riwayat log."""
    # Update status terlewat setiap kali halaman dibuka
    update_status_terlewat()

    mendatang = get_imunisasi_mendatang(days=30)

    # Ambil semua imunisasi terlewat
    terlewat = (
        Imunisasi.query
        .filter_by(status='terlewat')
        .order_by(Imunisasi.tanggal_jadwal.asc())
        .all()
    )

    riwayat = (
        NotifikasiLog.query
        .order_by(NotifikasiLog.waktu_kirim.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "notifikasi/index.html",
        mendatang=mendatang,
        terlewat=terlewat,
        riwayat=riwayat,
        today=date.today(),
    )


@notifikasi_bp.route("/kirim/<int:anak_id>", methods=["POST"])
@master_only
def kirim_notifikasi(anak_id):
    """Kirim notifikasi WhatsApp ke satu anak."""
    anak = Anak.query.get_or_404(anak_id)

    # Ambil imunisasi mendatang untuk anak ini
    mendatang = get_imunisasi_mendatang(days=30)
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
@master_only
def kirim_semua():
    """Kirim notifikasi WhatsApp ke semua anak dengan jadwal imunisasi dalam 30 hari ke depan."""
    mendatang = get_imunisasi_mendatang(days=30)

    if not mendatang:
        flash("Tidak ada jadwal imunisasi mendatang dalam 30 hari ke depan.", "info")
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


@notifikasi_bp.route("/kirim-terlewat/<int:anak_id>", methods=["POST"])
@master_only
def kirim_notifikasi_terlewat(anak_id):
    """Kirim pengingat WhatsApp untuk imunisasi terlewat ke satu anak."""
    anak = Anak.query.get_or_404(anak_id)

    imunisasi_terlewat = (
        Imunisasi.query
        .filter_by(anak_id=anak_id, status='terlewat')
        .order_by(Imunisasi.tanggal_jadwal.asc())
        .all()
    )

    if not imunisasi_terlewat:
        flash(f"Tidak ada imunisasi terlewat untuk {anak.nama}.", "warning")
        return redirect(url_for("notifikasi.index"))

    nama_fasilitas = current_app.config.get("NAMA_FASILITAS", "Puskesmas")
    berhasil = 0
    gagal = 0

    for imun in imunisasi_terlewat:
        pesan = (
            f"Yth. Orang tua {anak.nama}, imunisasi {imun.nama_vaksin} "
            f"yang dijadwalkan pada {imun.tanggal_jadwal.strftime('%d %B %Y')} "
            f"belum terlaksana. Segera datang ke {nama_fasilitas}. "
            f"Info: 1000HPK App."
        )
        hasil = kirim_dan_log(anak.id, anak.no_hp_ortu, pesan)
        if hasil["success"]:
            berhasil += 1
        else:
            gagal += 1

    if berhasil > 0:
        flash(f"Pengingat berhasil dikirim ke {anak.nama} ({berhasil} pesan).", "success")
    if gagal > 0:
        flash(f"{gagal} pesan gagal dikirim ke {anak.nama}.", "danger")

    return redirect(url_for("notifikasi.index"))


@notifikasi_bp.route("/kirim-semua-terlewat", methods=["POST"])
@master_only
def kirim_semua_terlewat():
    """Kirim pengingat ke semua anak dengan imunisasi terlewat."""
    terlewat = (
        Imunisasi.query
        .filter_by(status='terlewat')
        .all()
    )

    if not terlewat:
        flash("Tidak ada imunisasi terlewat.", "info")
        return redirect(url_for("notifikasi.index"))

    nama_fasilitas = current_app.config.get("NAMA_FASILITAS", "Puskesmas")
    berhasil = 0
    gagal = 0
    anak_terkirim = set()

    for imun in terlewat:
        anak = imun.anak
        # Kirim satu pesan per anak (gabungkan semua vaksin terlewat)
        if anak.id in anak_terkirim:
            continue
        anak_terkirim.add(anak.id)

        vaksin_terlewat = [
            i.nama_vaksin for i in terlewat if i.anak_id == anak.id
        ]
        pesan = (
            f"Yth. Orang tua {anak.nama}, terdapat {len(vaksin_terlewat)} imunisasi "
            f"yang belum terlaksana: {', '.join(vaksin_terlewat)}. "
            f"Segera datang ke {nama_fasilitas}. Info: 1000HPK App."
        )
        hasil = kirim_dan_log(anak.id, anak.no_hp_ortu, pesan)
        if hasil["success"]:
            berhasil += 1
        else:
            gagal += 1

    flash(
        f"Pengingat terlewat: {berhasil} anak berhasil, {gagal} gagal.",
        "success" if gagal == 0 else "warning",
    )
    return redirect(url_for("notifikasi.index"))
