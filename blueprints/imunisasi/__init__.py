from flask import Blueprint

imunisasi_bp = Blueprint("imunisasi", __name__, url_prefix="/imunisasi")

from blueprints.imunisasi import routes  # noqa
