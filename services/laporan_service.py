"""
services/laporan_service.py — Layanan logika laporan dan statistik imunisasi.
"""

from datetime import date

from extensions import db
from models import Anak, Imunisasi


def get_laporan(start_date: date, end_date: date) -> list:
    """
    Ambil data imunisasi berdasarkan rentang tanggal jadwal (inklusif).

    Args:
        start_date: Tanggal mulai filter.
        end_date  : Tanggal akhir filter.

    Returns:
        List of Imunisasi instances dengan relasi anak dan petugas.
    """
    return (
        Imunisasi.query
        .filter(
            Imunisasi.tanggal_jadwal >= start_date,
            Imunisasi.tanggal_jadwal <= end_date,
        )
        .order_by(Imunisasi.tanggal_jadwal.asc())
        .all()
    )


def get_statistik() -> dict:
    """
    Hitung statistik ringkasan imunisasi.

    Returns:
        dict dengan keys: total_anak, total_selesai, total_terlewat,
        total_terjadwal, total_imunisasi, persentase_cakupan.
    """
    total_anak = Anak.query.count()
    total_selesai = Imunisasi.query.filter_by(status='selesai').count()
    total_terlewat = Imunisasi.query.filter_by(status='terlewat').count()
    total_terjadwal = Imunisasi.query.filter_by(status='terjadwal').count()
    total_imunisasi = total_selesai + total_terlewat + total_terjadwal

    persentase_cakupan = 0.0
    if total_imunisasi > 0:
        persentase_cakupan = round((total_selesai / total_imunisasi) * 100, 1)

    return {
        "total_anak": total_anak,
        "total_selesai": total_selesai,
        "total_terlewat": total_terlewat,
        "total_terjadwal": total_terjadwal,
        "total_imunisasi": total_imunisasi,
        "persentase_cakupan": persentase_cakupan,
    }


def hitung_progress_anak(anak_id: int) -> float:
    """
    Hitung persentase vaksin selesai dari total vaksin yang dijadwalkan untuk satu anak.

    Args:
        anak_id: ID anak.

    Returns:
        Float persentase (0.0 - 100.0). Returns 0.0 jika tidak ada jadwal.
    """
    total = Imunisasi.query.filter_by(anak_id=anak_id).count()
    if total == 0:
        return 0.0
    selesai = Imunisasi.query.filter_by(anak_id=anak_id, status='selesai').count()
    return round((selesai / total) * 100, 1)


def get_cakupan_per_vaksin() -> list:
    """
    Hitung persentase cakupan per jenis vaksin (berapa % anak yang sudah mendapat vaksin tsb).

    Returns:
        List of dict: [{"nama_vaksin": str, "total": int, "selesai": int, "persentase": float}, ...]
    """
    from sqlalchemy import func

    total_anak = Anak.query.count()
    if total_anak == 0:
        return []

    # Ambil semua nama vaksin unik
    vaksin_list = db.session.query(Imunisasi.nama_vaksin).distinct().all()
    hasil = []

    for (nama_vaksin,) in vaksin_list:
        total = Imunisasi.query.filter_by(nama_vaksin=nama_vaksin).count()
        selesai = Imunisasi.query.filter_by(nama_vaksin=nama_vaksin, status='selesai').count()
        persentase = round((selesai / total * 100), 1) if total > 0 else 0.0
        hasil.append({
            "nama_vaksin": nama_vaksin,
            "total": total,
            "selesai": selesai,
            "persentase": persentase,
        })

    return sorted(hasil, key=lambda x: x['nama_vaksin'])
