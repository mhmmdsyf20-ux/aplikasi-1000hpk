"""
blueprints/edukasi/routes.py — Route halaman edukasi 1000 HPK.
"""

from flask import render_template

from blueprints.edukasi import edukasi_bp
from services.master_service import master_only
from services.imunisasi_service import JADWAL_IDAI


@edukasi_bp.route("/")
@master_only
def index():
    """Halaman edukasi 1000 HPK dengan konten terstruktur."""
    return render_template("edukasi/index.html", jadwal_idai=JADWAL_IDAI)
