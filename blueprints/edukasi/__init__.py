from flask import Blueprint

edukasi_bp = Blueprint("edukasi", __name__, url_prefix="/edukasi")

from blueprints.edukasi import routes  # noqa
