"""
Blueprint Portal Ibu - Portal Web untuk Ibu/Orang Tua Anak.

Blueprint ini menyediakan akses read-only bagi ibu/orang tua untuk memantau
jadwal imunisasi anak-anaknya secara mandiri melalui browser.
Semua route diawali dengan prefix /portal dan terpisah sepenuhnya
dari sistem petugas.
"""

from flask import Blueprint

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')

from blueprints.portal import routes  # noqa
