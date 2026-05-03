"""
models/imunisasi.py — Model jadwal dan realisasi imunisasi anak.

Setiap entri merepresentasikan satu jadwal vaksin untuk satu anak,
mengikuti jadwal IDAI yang di-generate otomatis saat anak didaftarkan.
"""

from extensions import db


class Imunisasi(db.Model):
    """
    Model jadwal imunisasi anak sesuai rekomendasi IDAI.

    Attributes:
        id                : Primary key.
        anak_id           : FK ke anak.id — anak pemilik jadwal ini.
        nama_vaksin       : Nama vaksin (misal: 'Hepatitis B', 'BCG').
        tanggal_jadwal    : Tanggal jadwal pemberian vaksin.
        tanggal_realisasi : Tanggal aktual pemberian vaksin (diisi saat selesai).
        status            : Status jadwal ('terjadwal', 'selesai', 'terlewat').
        catatan           : Catatan tambahan dari petugas (opsional).
        petugas_id        : FK ke users.id — petugas yang menandai selesai.
    """

    __tablename__ = "imunisasi"

    id                = db.Column(db.Integer, primary_key=True)
    anak_id           = db.Column(db.Integer, db.ForeignKey("anak.id"), nullable=False)
    nama_vaksin       = db.Column(db.String(100), nullable=False)
    tanggal_jadwal    = db.Column(db.Date, nullable=False)
    tanggal_realisasi = db.Column(db.Date)
    status            = db.Column(
        db.Enum("terjadwal", "selesai", "terlewat"),
        nullable=False,
        default="terjadwal",
    )
    catatan           = db.Column(db.Text)
    petugas_id        = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self) -> str:
        return (
            f"<Imunisasi anak_id={self.anak_id} vaksin={self.nama_vaksin!r} "
            f"jadwal={self.tanggal_jadwal} status={self.status!r}>"
        )
