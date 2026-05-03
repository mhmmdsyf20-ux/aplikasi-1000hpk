"""
models/notifikasi_log.py — Model log pengiriman notifikasi WhatsApp.

Setiap percobaan pengiriman pesan WhatsApp (berhasil maupun gagal)
dicatat sebagai satu entri di tabel ini untuk keperluan audit dan
monitoring.
"""

from datetime import datetime

from extensions import db


class NotifikasiLog(db.Model):
    """
    Model log pengiriman notifikasi WhatsApp ke orang tua anak.

    Attributes:
        id            : Primary key.
        anak_id       : FK ke anak.id — anak yang dinotifikasi.
        pesan         : Isi pesan yang dikirimkan.
        no_tujuan     : Nomor HP tujuan pengiriman.
        status_kirim  : Hasil pengiriman ('terkirim' atau 'gagal').
        waktu_kirim   : Waktu percobaan pengiriman.
        error_message : Pesan error dari gateway jika pengiriman gagal.
    """

    __tablename__ = "notifikasi_log"

    id            = db.Column(db.Integer, primary_key=True)
    anak_id       = db.Column(db.Integer, db.ForeignKey("anak.id"), nullable=False)
    pesan         = db.Column(db.Text, nullable=False)
    no_tujuan     = db.Column(db.String(20), nullable=False)
    status_kirim  = db.Column(
        db.Enum("terkirim", "gagal"),
        nullable=False,
    )
    waktu_kirim   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    error_message = db.Column(db.Text)   # diisi jika status_kirim = 'gagal'

    def __repr__(self) -> str:
        return (
            f"<NotifikasiLog anak_id={self.anak_id} "
            f"status={self.status_kirim!r} waktu={self.waktu_kirim}>"
        )
