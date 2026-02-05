from flask import Blueprint, send_from_directory, current_app

bp = Blueprint('api', __name__)

# Import all routes
from . import auth, wills, memorials, fundraisers, vendors, payments, admin

@bp.route('/static/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
