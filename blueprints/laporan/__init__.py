from flask import Blueprint

laporan_bp = Blueprint("laporan", __name__, url_prefix="/laporan")

from blueprints.laporan import routes  # noqa
