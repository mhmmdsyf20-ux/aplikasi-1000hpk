from flask import Blueprint

notifikasi_bp = Blueprint("notifikasi", __name__, url_prefix="/notifikasi")

from blueprints.notifikasi import routes  # noqa
