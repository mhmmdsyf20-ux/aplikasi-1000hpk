"""
services/wa_service.py — Layanan pengiriman notifikasi WhatsApp.

Mendukung dua provider: Fonnte (default, lokal Indonesia) dan Twilio WhatsApp API.
Provider dikonfigurasi via variabel WA_GATEWAY di file .env.
"""

import requests
from datetime import date
from flask import current_app

from extensions import db
from models import NotifikasiLog


def format_pesan_wa(nama_anak: str, nama_vaksin: str, tanggal: date, nama_fasilitas: str) -> str:
    """
    Format pesan WhatsApp untuk reminder jadwal imunisasi.

    Args:
        nama_anak      : Nama lengkap anak.
        nama_vaksin    : Nama vaksin yang dijadwalkan.
        tanggal        : Tanggal jadwal imunisasi.
        nama_fasilitas : Nama puskesmas/fasilitas kesehatan.

    Returns:
        String pesan yang sudah diformat.
    """
    tgl_str = tanggal.strftime('%d %B %Y') if isinstance(tanggal, date) else str(tanggal)
    return (
        f"Yth. Orang tua {nama_anak}, jadwal imunisasi {nama_vaksin} "
        f"pada {tgl_str} sudah mendekat. "
        f"Harap datang ke {nama_fasilitas}. "
        f"Info: 1000HPK App."
    )


class WAService:
    """
    Layanan pengiriman pesan WhatsApp.
    Mendukung provider Fonnte dan Twilio.
    """

    def __init__(self, gateway: str = None, api_key: str = None, sender: str = None):
        self.gateway = gateway or current_app.config.get('WA_GATEWAY', 'fonnte')
        self.api_key = api_key or current_app.config.get('WA_API_KEY', '')
        self.sender = sender or current_app.config.get('WA_SENDER', '')

    def kirim_pesan(self, no_tujuan: str, pesan: str) -> dict:
        """
        Kirim pesan WhatsApp ke nomor tujuan.

        Args:
            no_tujuan : Nomor HP tujuan (format Indonesia: 08xx atau +62xx).
            pesan     : Isi pesan yang akan dikirim.

        Returns:
            dict: {"success": bool, "message": str, "provider": str}
        """
        # Normalisasi nomor: ubah 08xx menjadi 628xx untuk API
        no_normalized = no_tujuan.strip()
        if no_normalized.startswith('0'):
            no_normalized = '62' + no_normalized[1:]
        elif no_normalized.startswith('+'):
            no_normalized = no_normalized[1:]

        if self.gateway == 'twilio':
            return self._kirim_twilio(no_normalized, pesan)
        else:
            return self._kirim_fonnte(no_normalized, pesan)

    def _kirim_fonnte(self, no_tujuan: str, pesan: str) -> dict:
        """Kirim via Fonnte API."""
        try:
            resp = requests.post(
                'https://api.fonnte.com/send',
                headers={'Authorization': self.api_key},
                data={
                    'target': no_tujuan,
                    'message': pesan,
                    'countryCode': '62',
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') is True:
                    return {"success": True, "message": "Pesan terkirim via Fonnte.", "provider": "fonnte"}
                else:
                    return {"success": False, "message": data.get('reason', 'Gagal kirim via Fonnte.'), "provider": "fonnte"}
            else:
                return {"success": False, "message": f"HTTP {resp.status_code} dari Fonnte.", "provider": "fonnte"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Timeout saat menghubungi Fonnte API.", "provider": "fonnte"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Error koneksi Fonnte: {str(e)}", "provider": "fonnte"}

    def _kirim_twilio(self, no_tujuan: str, pesan: str) -> dict:
        """Kirim via Twilio WhatsApp API."""
        try:
            # api_key format: "account_sid:auth_token"
            parts = self.api_key.split(':', 1)
            if len(parts) != 2:
                return {"success": False, "message": "Format WA_API_KEY Twilio tidak valid (harus account_sid:auth_token).", "provider": "twilio"}

            account_sid, auth_token = parts
            url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'

            resp = requests.post(
                url,
                auth=(account_sid, auth_token),
                data={
                    'From': f'whatsapp:{self.sender}',
                    'To': f'whatsapp:+{no_tujuan}',
                    'Body': pesan,
                },
                timeout=15,
            )
            if resp.status_code in (200, 201):
                return {"success": True, "message": "Pesan terkirim via Twilio.", "provider": "twilio"}
            else:
                data = resp.json()
                return {"success": False, "message": data.get('message', f'HTTP {resp.status_code} dari Twilio.'), "provider": "twilio"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Timeout saat menghubungi Twilio API.", "provider": "twilio"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Error koneksi Twilio: {str(e)}", "provider": "twilio"}


def kirim_dan_log(anak_id: int, no_tujuan: str, pesan: str) -> dict:
    """
    Kirim pesan WhatsApp dan catat hasilnya ke NotifikasiLog.

    Args:
        anak_id   : ID anak yang dinotifikasi.
        no_tujuan : Nomor HP tujuan.
        pesan     : Isi pesan.

    Returns:
        dict hasil pengiriman dari WAService.kirim_pesan().
    """
    wa = WAService()
    hasil = wa.kirim_pesan(no_tujuan, pesan)

    log = NotifikasiLog(
        anak_id=anak_id,
        pesan=pesan,
        no_tujuan=no_tujuan,
        status_kirim='terkirim' if hasil['success'] else 'gagal',
        error_message=None if hasil['success'] else hasil.get('message'),
    )
    db.session.add(log)
    db.session.commit()

    return hasil
