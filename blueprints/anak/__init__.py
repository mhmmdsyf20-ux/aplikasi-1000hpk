from flask import Blueprint

anak_bp = Blueprint('anak', __name__, url_prefix='/anak')

from blueprints.anak import routes  # noqa
