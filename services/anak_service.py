"""
services/anak_service.py — Layanan validasi dan logika bisnis data anak.

Menyediakan fungsi validasi nomor HP Indonesia dan validasi data anak
sebelum disimpan ke database.
"""

import re

HP_PATTERN = re.compile(r'^(\+62|08)\d{8,13}$')


def validate_hp(no_hp: str) -> bool:
    """
    Validasi nomor HP format Indonesia.
    Valid: diawali 08 atau +62, total panjang 10-15 digit angka.

    Args:
        no_hp: Nomor HP yang akan divalidasi.

    Returns:
        True jika format valid, False jika tidak.
    """
    if not no_hp:
        return False
    cleaned = no_hp.strip()
    return bool(HP_PATTERN.match(cleaned))


def validate_anak_data(data: dict) -> list[str]:
    """
    Validasi data anak dari form.

    Memeriksa semua field wajib dan format nomor HP.

    Args:
        data: Dictionary berisi data anak dari form request.

    Returns:
        List of error messages. Empty list = valid.
    """
    errors = []
    required_fields = {
        'nama': 'Nama anak',
        'tanggal_lahir': 'Tanggal lahir',
        'jenis_kelamin': 'Jenis kelamin',
        'nama_ibu': 'Nama ibu',
        'no_hp_ortu': 'Nomor HP orang tua',
    }
    for field, label in required_fields.items():
        if not data.get(field, '').strip():
            errors.append(f'{label} wajib diisi.')

    if data.get('no_hp_ortu') and not validate_hp(data['no_hp_ortu']):
        errors.append('Format nomor HP tidak valid. Gunakan format 08xx atau +62xx.')

    return errors
