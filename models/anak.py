"""
models/anak.py — Model data anak dalam program 1000 HPK.

Menyimpan data identitas anak beserta relasi ke jadwal imunisasi.
Menyediakan properti kalkulasi umur dan flag 1000 HPK.
"""

from datetime import datetime, date

from extensions import db


class Anak(db.Model):
    """
    Model data anak peserta program 1000 HPK.

    Attributes:
        id            : Primary key.
        nama          : Nama lengkap anak.
        tanggal_lahir : Tanggal lahir anak.
        jenis_kelamin : Jenis kelamin ('L' = Laki-laki, 'P' = Perempuan).
        nama_ibu      : Nama ibu kandung.
        no_hp_ortu    : Nomor HP orang tua untuk notifikasi WhatsApp.
        alamat        : Alamat tempat tinggal (opsional).
        berat_lahir   : Berat lahir dalam gram (opsional).
        panjang_lahir : Panjang lahir dalam cm (opsional).
        created_by    : FK ke users.id — petugas yang mendaftarkan.
        created_at    : Waktu pendaftaran.
        imunisasi_list: Relasi ke daftar jadwal imunisasi anak ini.
    """

    __tablename__ = "anak"

    id            = db.Column(db.Integer, primary_key=True)
    nama          = db.Column(db.String(150), nullable=False)
    tanggal_lahir = db.Column(db.Date, nullable=False)
    jenis_kelamin = db.Column(db.Enum("L", "P"), nullable=False)
    nama_ibu      = db.Column(db.String(150), nullable=False)
    no_hp_ortu    = db.Column(db.String(20), nullable=False)
    alamat        = db.Column(db.Text)
    berat_lahir   = db.Column(db.Float)   # gram
    panjang_lahir = db.Column(db.Float)   # cm
    created_by    = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi ke jadwal imunisasi — cascade delete agar data imunisasi
    # ikut terhapus ketika data anak dihapus.
    imunisasi_list = db.relationship(
        "Imunisasi",
        backref="anak",
        lazy=True,
        cascade="all, delete-orphan",
    )

    # Relasi ke log notifikasi
    notifikasi_list = db.relationship(
        "NotifikasiLog",
        backref="anak",
        lazy=True,
        cascade="all, delete-orphan",
    )

    # ── Properti kalkulasi ─────────────────────────────────────────────────────

    @property
    def umur_hari(self) -> int:
        """Umur anak dalam hari dihitung dari tanggal lahir hingga hari ini."""
        return (date.today() - self.tanggal_lahir).days

    @property
    def umur_bulan(self) -> int:
        """Umur anak dalam bulan (pembulatan ke bawah, 1 bulan = 30 hari)."""
        return self.umur_hari // 30

    @property
    def melewati_1000hpk(self) -> bool:
        """True jika anak sudah melewati 1000 Hari Pertama Kehidupan (> 730 hari)."""
        return self.umur_hari > 730

    def __repr__(self) -> str:
        return f"<Anak {self.nama!r} lahir={self.tanggal_lahir}>"
