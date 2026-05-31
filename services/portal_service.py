"""
services/portal_service.py — Layanan logika bisnis Portal Ibu/Orang Tua.

Modul ini menyediakan dua kelompok fungsi:

1. **Pure functions** (tidak mengakses database):
   - mask_nomor(no_hp)              — masking nomor HP, tampilkan 4 digit terakhir
   - validate_email_format(email)   — validasi format email RFC 5322 sederhana
   - validate_password(password, konfirmasi) — validasi kekuatan & kecocokan password
   - validate_no_whatsapp(no_wa)    — validasi format nomor WhatsApp Indonesia
   - kelompokkan_jadwal(jadwal_list, today) — kelompokkan jadwal ke mendatang/terjadwal/riwayat

2. **DB-access functions** (mengakses database, ditambahkan di task 2.2):
   - get_anak_by_ibu, get_anak_or_403, get_dashboard_stats,
     get_jadwal_anak, get_notifikasi_ibu, hitung_persentase_imunisasi
"""

import re
from datetime import date, timedelta
from typing import Any


# ── Pure Functions ─────────────────────────────────────────────────────────────


def mask_nomor(no_hp: str) -> str:
    """
    Masking nomor HP — tampilkan hanya 4 digit terakhir.

    Format output: ``****XXXX`` di mana XXXX adalah 4 digit terakhir.
    Jika panjang string < 4 karakter, semua karakter diganti bintang.

    Args:
        no_hp: String nomor HP yang akan di-mask.

    Returns:
        String hasil masking, contoh: '08123456789' -> '****6789'.

    Examples:
        >>> mask_nomor('08123456789')
        '****6789'
        >>> mask_nomor('123')
        '***'
        >>> mask_nomor('')
        ''
    """
    if len(no_hp) < 4:
        return '*' * len(no_hp)
    return '****' + no_hp[-4:]


def validate_email_format(email: str) -> bool:
    """
    Validasi format email menggunakan regex RFC 5322 sederhana.

    Kriteria validasi:
    - Tepat satu karakter ``@``
    - Karakter non-kosong di sisi kiri ``@``
    - Domain valid: setidaknya satu karakter ``.`` di sisi kanan ``@``
      dengan karakter non-kosong di antara bagian-bagian domain

    Args:
        email: String email yang akan divalidasi.

    Returns:
        ``True`` jika format email valid, ``False`` jika tidak.

    Examples:
        >>> validate_email_format('user@example.com')
        True
        >>> validate_email_format('user.name@domain.co.id')
        True
        >>> validate_email_format('user')
        False
        >>> validate_email_format('user@')
        False
        >>> validate_email_format('@domain.com')
        False
        >>> validate_email_format('user@@domain.com')
        False
        >>> validate_email_format('user@domain')
        False
    """
    # Regex: bagian lokal non-kosong @ domain dengan minimal satu titik
    # dan label non-kosong di setiap sisi titik
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return bool(re.match(pattern, email))


def validate_password(password: str, konfirmasi: str) -> list[str]:
    """
    Validasi password dan konfirmasi password.

    Pemeriksaan yang dilakukan:
    1. Panjang password minimal 8 karakter
    2. Konfirmasi password harus cocok dengan password

    Args:
        password:   Password yang akan divalidasi.
        konfirmasi: Konfirmasi ulang password.

    Returns:
        List pesan error. List kosong berarti password valid.

    Examples:
        >>> validate_password('secret12', 'secret12')
        []
        >>> validate_password('short', 'short')
        ['Password minimal 8 karakter.']
        >>> validate_password('secret12', 'berbeda')
        ['Konfirmasi password tidak cocok.']
        >>> validate_password('ab', 'cd')
        ['Password minimal 8 karakter.', 'Konfirmasi password tidak cocok.']
    """
    errors: list[str] = []

    if len(password) < 8:
        errors.append("Password minimal 8 karakter.")

    if password != konfirmasi:
        errors.append("Konfirmasi password tidak cocok.")

    return errors


def validate_no_whatsapp(no_wa: str) -> bool:
    """
    Validasi nomor WhatsApp format Indonesia.

    Kriteria validasi:
    - Diawali dengan ``08`` atau ``+62``
    - Panjang 10–15 digit (digit saja, tidak termasuk karakter ``+``)

    Args:
        no_wa: String nomor WhatsApp yang akan divalidasi.

    Returns:
        ``True`` jika format nomor valid, ``False`` jika tidak.

    Examples:
        >>> validate_no_whatsapp('08123456789')
        True
        >>> validate_no_whatsapp('+6281234567890')
        True
        >>> validate_no_whatsapp('12345')
        False
        >>> validate_no_whatsapp('abc')
        False
        >>> validate_no_whatsapp('081')
        False
    """
    # Normalisasi: hapus karakter '+' di awal untuk menghitung digit
    if no_wa.startswith('+62'):
        digits = '62' + no_wa[3:]
    elif no_wa.startswith('08'):
        digits = no_wa
    else:
        return False

    # Pastikan semua karakter setelah normalisasi adalah digit
    if not digits.isdigit():
        return False

    # Validasi panjang: 10–15 digit
    return 10 <= len(digits) <= 15


def kelompokkan_jadwal(jadwal_list: list[Any], today: date) -> dict[str, list[Any]]:
    """
    Kelompokkan daftar jadwal imunisasi ke dalam tiga kategori.

    Pure function — tidak mengakses database.

    Kategori pengelompokan:
    - ``mendatang``: status == 'terjadwal' DAN ``today <= tanggal_jadwal <= today + 30 hari``
    - ``terjadwal``: status == 'terjadwal' DAN ``tanggal_jadwal > today + 30 hari``
    - ``riwayat``:   status == 'selesai' ATAU status == 'terlewat' ATAU
                     (status == 'terjadwal' DAN ``tanggal_jadwal < today``)

    Setiap item dalam ``jadwal_list`` harus memiliki atribut:
    - ``tanggal_jadwal`` (``date``)
    - ``status`` (``str``: 'terjadwal', 'selesai', atau 'terlewat')

    Args:
        jadwal_list: Daftar objek jadwal imunisasi (misalnya list of ``Imunisasi``).
        today:       Tanggal referensi hari ini.

    Returns:
        Dict dengan tiga kunci: ``mendatang``, ``terjadwal``, ``riwayat``,
        masing-masing berisi list jadwal yang sesuai kategori.

    Examples:
        >>> from datetime import date
        >>> from types import SimpleNamespace
        >>> today = date(2024, 1, 15)
        >>> j1 = SimpleNamespace(tanggal_jadwal=date(2024, 1, 18), status='terjadwal')
        >>> j2 = SimpleNamespace(tanggal_jadwal=date(2024, 2, 1), status='terjadwal')
        >>> j3 = SimpleNamespace(tanggal_jadwal=date(2024, 1, 10), status='selesai')
        >>> result = kelompokkan_jadwal([j1, j2, j3], today)
        >>> result['mendatang'] == [j1]
        True
        >>> result['terjadwal'] == [j2]
        True
        >>> result['riwayat'] == [j3]
        True
    """
    batas_mendatang = today + timedelta(days=30)

    mendatang: list[Any] = []
    terjadwal: list[Any] = []
    riwayat: list[Any] = []

    for jadwal in jadwal_list:
        status = jadwal.status
        tgl = jadwal.tanggal_jadwal

        if status in ('selesai', 'terlewat'):
            riwayat.append(jadwal)
        elif status == 'terjadwal':
            if tgl < today:
                # Jadwal terjadwal yang sudah lewat masuk riwayat
                riwayat.append(jadwal)
            elif today <= tgl <= batas_mendatang:
                mendatang.append(jadwal)
            else:
                # tgl > batas_mendatang
                terjadwal.append(jadwal)

    return {
        'mendatang': mendatang,
        'terjadwal': terjadwal,
        'riwayat': riwayat,
    }


def hitung_persentase_imunisasi(anak_id: int) -> float:
    """
    Hitung persentase kelengkapan imunisasi anak berdasarkan data di database.

    Mengakses database untuk mengambil data jadwal imunisasi anak.
    Formula: ``(jumlah_selesai / total) * 100.0``

    Args:
        anak_id: ID anak yang akan dihitung persentase imunisasinya.

    Returns:
        Float dalam rentang ``[0.0, 100.0]``.
        Mengembalikan ``0.0`` jika tidak ada jadwal imunisasi.

    Note:
        Fungsi ini mengakses database (bukan pure function).
        Harus dipanggil dalam konteks aplikasi Flask yang aktif.
    """
    from models import Imunisasi  # import lokal untuk menghindari circular import

    jadwal_list = (
        Imunisasi.query
        .filter_by(anak_id=anak_id)
        .all()
    )

    total = len(jadwal_list)
    if total == 0:
        return 0.0

    selesai = sum(1 for j in jadwal_list if j.status == 'selesai')
    return (selesai / total) * 100.0


# ── DB-Access Functions ────────────────────────────────────────────────────────


def get_anak_by_ibu(user_id: int) -> list:
    """
    Ambil semua anak milik ibu berdasarkan user_id.

    Hanya mengembalikan anak yang memiliki ``created_by == user_id``,
    diurutkan berdasarkan nama anak secara ascending.

    Args:
        user_id: ID user (ibu) yang datanya ingin diambil.

    Returns:
        List objek ``Anak`` milik user tersebut.
        Mengembalikan list kosong jika terjadi error database.

    Note:
        Harus dipanggil dalam konteks aplikasi Flask yang aktif.
    """
    from models import Anak  # import lokal untuk menghindari circular import
    from flask import current_app

    try:
        return Anak.query.filter_by(created_by=user_id).order_by(Anak.nama).all()
    except Exception as e:
        current_app.logger.error(f"Error get_anak_by_ibu user_id={user_id}: {e}")
        return []


def get_anak_or_403(anak_id: int, user_id: int):
    """
    Ambil anak berdasarkan id dan validasi kepemilikan.

    Selalu memanggil ``abort(403)`` jika anak tidak ditemukan atau
    ``created_by != user_id`` — tidak pernah ``abort(404)`` — untuk
    mencegah enumeration attack (tidak mengungkap apakah data ada atau tidak).

    Args:
        anak_id: ID anak yang ingin diambil.
        user_id: ID user (ibu) yang melakukan request.

    Returns:
        Objek ``Anak`` jika ditemukan dan milik user tersebut.

    Raises:
        HTTPException: abort(403) jika anak tidak ditemukan atau bukan milik user.

    Note:
        Harus dipanggil dalam konteks aplikasi Flask yang aktif.
    """
    from models import Anak  # import lokal untuk menghindari circular import
    from flask import abort

    anak = Anak.query.filter_by(id=anak_id, created_by=user_id).first()
    if anak is None:
        abort(403)
    return anak


def get_jadwal_anak(anak_id: int, user_id: int) -> dict:
    """
    Ambil dan kelompokkan jadwal imunisasi anak beserta statistiknya.

    Validasi kepemilikan dilakukan via ``get_anak_or_403`` sebelum
    mengambil data jadwal. Jadwal dikelompokkan ke dalam tiga kategori:
    mendatang, terjadwal, dan riwayat.

    Args:
        anak_id: ID anak yang jadwalnya ingin diambil.
        user_id: ID user (ibu) yang melakukan request.

    Returns:
        Dict dengan kunci:
        - ``anak``      : Objek ``Anak``
        - ``mendatang`` : List jadwal terjadwal dalam 30 hari ke depan
        - ``terjadwal`` : List jadwal terjadwal lebih dari 30 hari ke depan
        - ``riwayat``   : List jadwal selesai atau terlewat
        - ``total``     : Total jumlah jadwal (int)
        - ``selesai``   : Jumlah jadwal berstatus selesai (int)
        - ``persen``    : Persentase kelengkapan imunisasi (float)

    Raises:
        HTTPException: abort(403) jika anak tidak ditemukan atau bukan milik user.

    Note:
        Harus dipanggil dalam konteks aplikasi Flask yang aktif.
    """
    from models import Imunisasi  # import lokal untuk menghindari circular import

    anak = get_anak_or_403(anak_id, user_id)

    jadwal_list = (
        Imunisasi.query
        .filter_by(anak_id=anak_id)
        .order_by(Imunisasi.tanggal_jadwal)
        .all()
    )

    kelompok = kelompokkan_jadwal(jadwal_list, date.today())

    total = len(jadwal_list)
    selesai = sum(1 for j in jadwal_list if j.status == 'selesai')
    persen = (selesai / total * 100.0) if total > 0 else 0.0

    return {
        'anak': anak,
        'mendatang': kelompok['mendatang'],
        'terjadwal': kelompok['terjadwal'],
        'riwayat': kelompok['riwayat'],
        'total': total,
        'selesai': selesai,
        'persen': persen,
    }


def get_notifikasi_ibu(user_id: int, limit: int = 20) -> list:
    """
    Ambil notifikasi untuk semua anak milik ibu, diurutkan terbaru.

    Mengambil semua anak milik ``user_id`` terlebih dahulu, kemudian
    mengambil notifikasi untuk semua anak tersebut, diurutkan berdasarkan
    ``waktu_kirim`` secara descending dan dibatasi sejumlah ``limit``.

    Args:
        user_id: ID user (ibu) yang notifikasinya ingin diambil.
        limit:   Jumlah maksimal notifikasi yang dikembalikan (default 20).

    Returns:
        List objek ``NotifikasiLog`` terbaru milik anak-anak user tersebut.
        Mengembalikan list kosong jika tidak ada anak, tidak ada notifikasi,
        atau terjadi error database.

    Note:
        Harus dipanggil dalam konteks aplikasi Flask yang aktif.
    """
    from models import Anak, NotifikasiLog  # import lokal untuk menghindari circular import
    from flask import current_app

    try:
        anak_list = Anak.query.filter_by(created_by=user_id).all()
        if not anak_list:
            return []

        anak_ids = [a.id for a in anak_list]
        return (
            NotifikasiLog.query
            .filter(NotifikasiLog.anak_id.in_(anak_ids))
            .order_by(NotifikasiLog.waktu_kirim.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        current_app.logger.error(f"Error get_notifikasi_ibu user_id={user_id}: {e}")
        return []


def get_dashboard_stats(user_id: int) -> dict:
    """
    Hitung statistik dashboard untuk ibu.

    Mengumpulkan data agregat dari semua anak milik ibu: total anak,
    total jadwal selesai/mendatang/terlewat, jadwal mendatang dalam 30 hari,
    dan progress imunisasi per anak.

    Args:
        user_id: ID user (ibu) yang statistiknya ingin dihitung.

    Returns:
        Dict dengan kunci:
        - ``total_anak``      : Jumlah anak milik ibu (int)
        - ``total_selesai``   : Total jadwal berstatus selesai dari semua anak (int)
        - ``total_mendatang`` : Total jadwal terjadwal dalam 30 hari ke depan (int)
        - ``total_terlewat``  : Total jadwal berstatus terlewat dari semua anak (int)
        - ``jadwal_mendatang``: List jadwal terjadwal dalam 30 hari ke depan
        - ``anak_progress``   : List dict ``{'anak': Anak, 'total': int, 'selesai': int, 'persen': float}``

        Mengembalikan dict dengan nilai 0/[] jika terjadi error database.

    Note:
        Harus dipanggil dalam konteks aplikasi Flask yang aktif.
    """
    from models import Anak, Imunisasi  # import lokal untuk menghindari circular import
    from flask import current_app

    _empty = {
        'total_anak': 0,
        'total_selesai': 0,
        'total_mendatang': 0,
        'total_terlewat': 0,
        'jadwal_mendatang': [],
        'anak_progress': [],
    }

    try:
        anak_list = Anak.query.filter_by(created_by=user_id).order_by(Anak.nama).all()

        today = date.today()
        batas_mendatang = today + timedelta(days=30)

        total_selesai = 0
        total_mendatang = 0
        total_terlewat = 0
        jadwal_mendatang: list = []
        anak_progress: list = []

        for anak in anak_list:
            jadwal_list = (
                Imunisasi.query
                .filter_by(anak_id=anak.id)
                .order_by(Imunisasi.tanggal_jadwal)
                .all()
            )

            total_anak_ini = len(jadwal_list)
            selesai_anak_ini = 0

            for j in jadwal_list:
                if j.status == 'selesai':
                    selesai_anak_ini += 1
                    total_selesai += 1
                elif j.status == 'terlewat':
                    total_terlewat += 1
                elif j.status == 'terjadwal':
                    if today <= j.tanggal_jadwal <= batas_mendatang:
                        total_mendatang += 1
                        jadwal_mendatang.append(j)

            persen = (selesai_anak_ini / total_anak_ini * 100.0) if total_anak_ini > 0 else 0.0

            anak_progress.append({
                'anak': anak,
                'total': total_anak_ini,
                'selesai': selesai_anak_ini,
                'persen': persen,
            })

        return {
            'total_anak': len(anak_list),
            'total_selesai': total_selesai,
            'total_mendatang': total_mendatang,
            'total_terlewat': total_terlewat,
            'jadwal_mendatang': jadwal_mendatang,
            'anak_progress': anak_progress,
        }

    except Exception as e:
        current_app.logger.error(f"Error get_dashboard_stats user_id={user_id}: {e}")
        return _empty
