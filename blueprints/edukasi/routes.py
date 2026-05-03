"""
blueprints/edukasi/routes.py — Route halaman edukasi 1000 HPK.
"""

from flask import render_template
from flask_login import login_required

from blueprints.edukasi import edukasi_bp
from services.imunisasi_service import JADWAL_IDAI


@edukasi_bp.route("/")
@login_required
def index():
    """Halaman edukasi 1000 HPK dengan konten terstruktur."""
    return render_template("edukasi/index.html", jadwal_idai=JADWAL_IDAI)
