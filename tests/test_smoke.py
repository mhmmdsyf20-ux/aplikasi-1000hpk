"""
tests/test_smoke.py — Unit tests untuk semua model aplikasi 1000 HPK.

Memverifikasi skema tabel, relasi FK, nilai default, dan logika bisnis
pada model User, Anak, Imunisasi, dan NotifikasiLog.
"""

from datetime import date, timedelta

import pytest

from models import User, Anak, Imunisasi, NotifikasiLog


# ─────────────────────────────────────────────────────────────────────────────
# Helper factories
# ─────────────────────────────────────────────────────────────────────────────

def make_user(db, username="petugas1", role="petugas", password="rahasia123"):
    """Buat dan simpan User ke database, kembalikan instance-nya."""
    user = User(
        username=username,
        role=role,
        nama_lengkap="Petugas Satu",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def make_anak(db, nama="Budi", tanggal_lahir=None, created_by=None):
    """Buat dan simpan Anak ke database, kembalikan instance-nya."""
    if tanggal_lahir is None:
        tanggal_lahir = date.today() - timedelta(days=100)
    anak = Anak(
        nama=nama,
        tanggal_lahir=tanggal_lahir,
        jenis_kelamin="L",
        nama_ibu="Ibu Budi",
        no_hp_ortu="08123456789",
        created_by=created_by,
    )
    db.session.add(anak)
    db.session.commit()
    return anak


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Model User
# ─────────────────────────────────────────────────────────────────────────────

class TestUser:
    def test_buat_user_berhasil(self, db):
        """User dapat dibuat dan disimpan ke database."""
        user = make_user(db)
        assert user.id is not None
        assert user.username == "petugas1"

    def test_set_password_menghasilkan_hash(self, db):
        """set_password() menyimpan hash, bukan plaintext."""
        user = make_user(db, password="rahasia123")
        assert user.password_hash != "rahasia123"
        assert user.password_hash is not None

    def test_check_password_benar(self, db):
        """check_password() mengembalikan True untuk password yang benar."""
        user = make_user(db, password="rahasia123")
        assert user.check_password("rahasia123") is True

    def test_check_password_salah(self, db):
        """check_password() mengembalikan False untuk password yang salah."""
        user = make_user(db, password="rahasia123")
        assert user.check_password("salah") is False

    def test_is_active_default_true(self, db):
        """is_active default bernilai True saat user baru dibuat."""
        user = make_user(db)
        assert user.is_active is True

    def test_role_petugas(self, db):
        """User dapat dibuat dengan role 'petugas'."""
        user = make_user(db, role="petugas")
        assert user.role == "petugas"

    def test_role_admin(self, db):
        """User dapat dibuat dengan role 'admin'."""
        user = make_user(db, username="admin1", role="admin")
        assert user.role == "admin"

    def test_username_unik(self, db):
        """Dua user dengan username yang sama tidak dapat disimpan."""
        from sqlalchemy.exc import IntegrityError
        make_user(db, username="duplikat")
        with pytest.raises(IntegrityError):
            make_user(db, username="duplikat")

    def test_repr(self, db):
        """__repr__ mengandung username dan role."""
        user = make_user(db)
        r = repr(user)
        assert "petugas1" in r
        assert "petugas" in r


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Model Anak
# ─────────────────────────────────────────────────────────────────────────────

class TestAnak:
    def test_buat_anak_berhasil(self, db):
        """Anak dapat dibuat dan disimpan ke database."""
        anak = make_anak(db)
        assert anak.id is not None
        assert anak.nama == "Budi"

    def test_umur_hari(self, db):
        """umur_hari mengembalikan selisih hari dari tanggal lahir ke hari ini."""
        tgl_lahir = date.today() - timedelta(days=200)
        anak = make_anak(db, tanggal_lahir=tgl_lahir)
        assert anak.umur_hari == 200

    def test_umur_bulan(self, db):
        """umur_bulan adalah umur_hari // 30."""
        tgl_lahir = date.today() - timedelta(days=90)
        anak = make_anak(db, tanggal_lahir=tgl_lahir)
        assert anak.umur_bulan == 3  # 90 // 30

    def test_melewati_1000hpk_false_jika_kurang_730_hari(self, db):
        """melewati_1000hpk False jika umur anak ≤ 730 hari."""
        tgl_lahir = date.today() - timedelta(days=730)
        anak = make_anak(db, tanggal_lahir=tgl_lahir)
        assert anak.melewati_1000hpk is False

    def test_melewati_1000hpk_true_jika_lebih_730_hari(self, db):
        """melewati_1000hpk True jika umur anak > 730 hari."""
        tgl_lahir = date.today() - timedelta(days=731)
        anak = make_anak(db, tanggal_lahir=tgl_lahir)
        assert anak.melewati_1000hpk is True

    def test_melewati_1000hpk_tepat_731_hari(self, db):
        """melewati_1000hpk True tepat di 731 hari."""
        tgl_lahir = date.today() - timedelta(days=731)
        anak = make_anak(db, tanggal_lahir=tgl_lahir)
        assert anak.melewati_1000hpk is True

    def test_imunisasi_list_kosong_awal(self, db):
        """Anak baru tidak memiliki imunisasi."""
        anak = make_anak(db)
        assert anak.imunisasi_list == []

    def test_repr(self, db):
        """__repr__ mengandung nama anak."""
        anak = make_anak(db, nama="Siti")
        assert "Siti" in repr(anak)


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Model Imunisasi
# ─────────────────────────────────────────────────────────────────────────────

class TestImunisasi:
    def test_buat_imunisasi_berhasil(self, db):
        """Imunisasi dapat dibuat dan disimpan ke database."""
        anak = make_anak(db)
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="Hepatitis B",
            tanggal_jadwal=date.today() + timedelta(days=7),
        )
        db.session.add(imun)
        db.session.commit()
        assert imun.id is not None

    def test_status_default_terjadwal(self, db):
        """Status imunisasi default adalah 'terjadwal'."""
        anak = make_anak(db)
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="BCG",
            tanggal_jadwal=date.today(),
        )
        db.session.add(imun)
        db.session.commit()
        assert imun.status == "terjadwal"

    def test_fk_ke_anak(self, db):
        """Imunisasi memiliki FK yang valid ke anak."""
        anak = make_anak(db)
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="Polio",
            tanggal_jadwal=date.today(),
        )
        db.session.add(imun)
        db.session.commit()
        assert imun.anak_id == anak.id

    def test_status_dapat_diubah_ke_selesai(self, db):
        """Status imunisasi dapat diubah ke 'selesai'."""
        anak = make_anak(db)
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="DPT",
            tanggal_jadwal=date.today(),
        )
        db.session.add(imun)
        db.session.commit()

        imun.status = "selesai"
        imun.tanggal_realisasi = date.today()
        db.session.commit()
        assert imun.status == "selesai"

    def test_status_dapat_diubah_ke_terlewat(self, db):
        """Status imunisasi dapat diubah ke 'terlewat'."""
        anak = make_anak(db)
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="Campak",
            tanggal_jadwal=date.today() - timedelta(days=10),
        )
        db.session.add(imun)
        db.session.commit()

        imun.status = "terlewat"
        db.session.commit()
        assert imun.status == "terlewat"

    def test_repr(self, db):
        """__repr__ mengandung nama vaksin dan status."""
        anak = make_anak(db)
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="Rotavirus",
            tanggal_jadwal=date.today(),
        )
        db.session.add(imun)
        db.session.commit()
        r = repr(imun)
        assert "Rotavirus" in r
        assert "terjadwal" in r


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Model NotifikasiLog
# ─────────────────────────────────────────────────────────────────────────────

class TestNotifikasiLog:
    def test_buat_log_berhasil(self, db):
        """NotifikasiLog dapat dibuat dan disimpan ke database."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Jadwal imunisasi BCG besok.",
            no_tujuan="08123456789",
            status_kirim="terkirim",
        )
        db.session.add(log)
        db.session.commit()
        assert log.id is not None

    def test_status_kirim_terkirim(self, db):
        """status_kirim dapat bernilai 'terkirim'."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Pesan test.",
            no_tujuan="08111111111",
            status_kirim="terkirim",
        )
        db.session.add(log)
        db.session.commit()
        assert log.status_kirim == "terkirim"

    def test_status_kirim_gagal(self, db):
        """status_kirim dapat bernilai 'gagal'."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Pesan test.",
            no_tujuan="08222222222",
            status_kirim="gagal",
            error_message="Timeout dari gateway.",
        )
        db.session.add(log)
        db.session.commit()
        assert log.status_kirim == "gagal"

    def test_error_message_nullable(self, db):
        """error_message boleh None (nullable)."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Pesan berhasil.",
            no_tujuan="08333333333",
            status_kirim="terkirim",
        )
        db.session.add(log)
        db.session.commit()
        assert log.error_message is None

    def test_error_message_terisi_saat_gagal(self, db):
        """error_message terisi dengan pesan error saat pengiriman gagal."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Pesan gagal.",
            no_tujuan="08444444444",
            status_kirim="gagal",
            error_message="HTTP 503 Service Unavailable",
        )
        db.session.add(log)
        db.session.commit()
        assert log.error_message == "HTTP 503 Service Unavailable"

    def test_waktu_kirim_terisi_otomatis(self, db):
        """waktu_kirim terisi otomatis saat log dibuat."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Pesan test.",
            no_tujuan="08555555555",
            status_kirim="terkirim",
        )
        db.session.add(log)
        db.session.commit()
        assert log.waktu_kirim is not None

    def test_repr(self, db):
        """__repr__ mengandung anak_id dan status."""
        anak = make_anak(db)
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Test repr.",
            no_tujuan="08666666666",
            status_kirim="terkirim",
        )
        db.session.add(log)
        db.session.commit()
        r = repr(log)
        assert str(anak.id) in r
        assert "terkirim" in r


# ─────────────────────────────────────────────────────────────────────────────
# Tests: Relasi antar model
# ─────────────────────────────────────────────────────────────────────────────

class TestRelasi:
    def test_anak_imunisasi_list(self, db):
        """anak.imunisasi_list mengembalikan semua imunisasi milik anak tersebut."""
        anak = make_anak(db)
        for vaksin in ["BCG", "Hepatitis B", "Polio"]:
            imun = Imunisasi(
                anak_id=anak.id,
                nama_vaksin=vaksin,
                tanggal_jadwal=date.today(),
            )
            db.session.add(imun)
        db.session.commit()

        db.session.refresh(anak)
        assert len(anak.imunisasi_list) == 3
        nama_vaksin = [i.nama_vaksin for i in anak.imunisasi_list]
        assert "BCG" in nama_vaksin
        assert "Hepatitis B" in nama_vaksin
        assert "Polio" in nama_vaksin

    def test_cascade_delete_imunisasi(self, db):
        """Menghapus anak juga menghapus semua imunisasi terkait (cascade delete)."""
        anak = make_anak(db)
        anak_id = anak.id
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="DPT",
            tanggal_jadwal=date.today(),
        )
        db.session.add(imun)
        db.session.commit()

        db.session.delete(anak)
        db.session.commit()

        sisa = Imunisasi.query.filter_by(anak_id=anak_id).all()
        assert sisa == []

    def test_cascade_delete_notifikasi_log(self, db):
        """Menghapus anak juga menghapus semua NotifikasiLog terkait (cascade delete)."""
        anak = make_anak(db)
        anak_id = anak.id
        log = NotifikasiLog(
            anak_id=anak.id,
            pesan="Pesan test.",
            no_tujuan="08777777777",
            status_kirim="terkirim",
        )
        db.session.add(log)
        db.session.commit()

        db.session.delete(anak)
        db.session.commit()

        sisa = NotifikasiLog.query.filter_by(anak_id=anak_id).all()
        assert sisa == []

    def test_backref_anak_dari_imunisasi(self, db):
        """Imunisasi.anak (backref) mengembalikan objek Anak yang benar."""
        anak = make_anak(db, nama="Citra")
        imun = Imunisasi(
            anak_id=anak.id,
            nama_vaksin="Campak",
            tanggal_jadwal=date.today(),
        )
        db.session.add(imun)
        db.session.commit()

        assert imun.anak.nama == "Citra"

    def test_imunisasi_tidak_tercampur_antar_anak(self, db):
        """imunisasi_list hanya berisi imunisasi milik anak yang bersangkutan."""
        anak_a = make_anak(db, nama="Anak A")
        anak_b = make_anak(db, nama="Anak B")

        imun_a = Imunisasi(anak_id=anak_a.id, nama_vaksin="BCG", tanggal_jadwal=date.today())
        imun_b = Imunisasi(anak_id=anak_b.id, nama_vaksin="Polio", tanggal_jadwal=date.today())
        db.session.add_all([imun_a, imun_b])
        db.session.commit()

        db.session.refresh(anak_a)
        db.session.refresh(anak_b)

        assert len(anak_a.imunisasi_list) == 1
        assert anak_a.imunisasi_list[0].nama_vaksin == "BCG"
        assert len(anak_b.imunisasi_list) == 1
        assert anak_b.imunisasi_list[0].nama_vaksin == "Polio"
