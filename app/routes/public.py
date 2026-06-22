from flask import Blueprint, abort, render_template, send_file

from app.config import Config
from app.models import get_file, get_stored_path, list_files

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    files = list_files()
    return render_template(
        "index.html",
        files=files,
        base_path=Config.BASE_PATH,
        max_upload_mb=Config.MAX_CONTENT_LENGTH // (1024 * 1024),
    )


@public_bp.route("/download/<file_id>")
def download(file_id):
    file_record = get_file(file_id)
    if file_record is None:
        abort(404)
    try:
        path = get_stored_path(file_record["stored_name"])
    except ValueError:
        abort(404)
    if not path.is_file():
        abort(404)
    return send_file(
        path,
        as_attachment=True,
        download_name=file_record["original_name"],
    )
