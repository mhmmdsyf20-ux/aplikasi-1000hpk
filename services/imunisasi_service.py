"""
services/imunisasi_service.py — Layanan logika bisnis jadwal imunisasi IDAI.
"""

from datetime import date, timedelta

from extensions import db
from models import Imunisasi


JADWAL_IDAI = [
    {"nama_vaksin": "Hepatitis B",    "offset_hari": 0},
    {"nama_vaksin": "BCG",            "offset_hari": 0},
    {"nama_vaksin": "Polio 0",        "offset_hari": 0},
    {"nama_vaksin": "DPT-HB-Hib 1",  "offset_hari": 60},
    {"nama_vaksin": "Polio 1",        "offset_hari": 60},
    {"nama_vaksin": "DPT-HB-Hib 2",  "offset_hari": 90},
    {"nama_vaksin": "Polio 2",        "offset_hari": 90},
    {"nama_vaksin": "DPT-HB-Hib 3",  "offset_hari": 120},
    {"nama_vaksin": "Polio 3",        "offset_hari": 120},
    {"nama_vaksin": "Campak/MR",      "offset_hari": 270},
    {"nama_vaksin": "Polio 4",        "offset_hari": 270},
    {"nama_vaksin": "Booster DPT",    "offset_hari": 540},
    {"nama_vaksin": "Booster Campak", "offset_hari": 540},
    {"nama_vaksin": "Tifoid",         "offset_hari": 730},
]


def generate_jadwal_imunisasi(tanggal_lahir: date) -> list:
    """
    Generate daftar jadwal imunisasi IDAI berdasarkan tanggal lahir.
    Returns list of dict: [{"nama_vaksin": str, "tanggal_jadwal": date}, ...]
    Selalu mengembalikan tepat len(JADWAL_IDAI) entri.
    """
    return [
        {
            "nama_vaksin": item["nama_vaksin"],
            "tanggal_jadwal": tanggal_lahir + timedelta(days=item["offset_hari"]),
        }
        for item in JADWAL_IDAI
    ]


def tandai_selesai(imunisasi_id: int, tanggal_realisasi: date, petugas_id: int) -> Imunisasi:
    """Tandai imunisasi sebagai selesai dengan tanggal realisasi."""
    imunisasi = Imunisasi.query.get_or_404(imunisasi_id)
    imunisasi.status = "selesai"
    imunisasi.tanggal_realisasi = tanggal_realisasi
    imunisasi.petugas_id = petugas_id
    db.session.commit()
    return imunisasi


def update_status_terlewat() -> int:
    """
    Update semua imunisasi 'terjadwal' yang tanggal_jadwal-nya sudah lewat menjadi 'terlewat'.
    Returns jumlah record yang diupdate.
    """
    today = date.today()
    updated = (
        Imunisasi.query
        .filter(
            Imunisasi.tanggal_jadwal < today,
            Imunisasi.status == "terjadwal",
        )
        .all()
    )
    count = len(updated)
    for imun in updated:
        imun.status = "terlewat"
    if count > 0:
        db.session.commit()
    return count


def get_imunisasi_mendatang(days: int = 7) -> list:
    """
    Ambil semua imunisasi 'terjadwal' yang jatuh tempo antara hari ini dan hari ini + days.
    """
    today = date.today()
    batas = today + timedelta(days=days)
    return (
        Imunisasi.query
        .filter(
            Imunisasi.tanggal_jadwal >= today,
            Imunisasi.tanggal_jadwal <= batas,
            Imunisasi.status == "terjadwal",
        )
        .order_by(Imunisasi.tanggal_jadwal.asc())
        .all()
    )
