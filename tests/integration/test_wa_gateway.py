"""
tests/integration/test_wa_gateway.py — Integration test WA Gateway.

CATATAN: Test ini memerlukan konfigurasi WA_API_KEY dan WA_SENDER yang valid di .env.
Jalankan secara terpisah: pytest tests/integration/ -v
"""

import pytest


@pytest.mark.integration
def test_wa_format_pesan():
    """Verifikasi format pesan WhatsApp mengandung semua komponen wajib."""
    from datetime import date
    from services.wa_service import format_pesan_wa

    nama_anak = "Budi Santoso"
    nama_vaksin = "BCG"
    tanggal = date(2025, 6, 15)
    nama_fasilitas = "Puskesmas Test"

    pesan = format_pesan_wa(nama_anak, nama_vaksin, tanggal, nama_fasilitas)

    assert nama_anak in pesan, "Pesan harus mengandung nama anak"
    assert nama_vaksin in pesan, "Pesan harus mengandung nama vaksin"
    assert nama_fasilitas in pesan, "Pesan harus mengandung nama fasilitas"
    assert "2025" in pesan or "Juni" in pesan or "15" in pesan, "Pesan harus mengandung tanggal"
