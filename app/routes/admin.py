import uuid

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from app.auth import admin_required, is_admin_logged_in, login_admin, logout_admin
from app.config import Config
from app.models import add_file, change_password, delete_file, list_files

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/status")
def admin_status():
    return jsonify({"logged_in": is_admin_logged_in()})


@admin_bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    if login_admin(password):
        return jsonify({"message": "登录成功"})
    return jsonify({"error": "密码错误"}), 401


@admin_bp.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    logout_admin()
    return jsonify({"message": "已退出管理"})


@admin_bp.route("/api/admin/files")
@admin_required
def admin_files():
    return jsonify({"files": list_files()})


@admin_bp.route("/api/admin/upload", methods=["POST"])
@admin_required
def admin_upload():
    if "file" not in request.files:
        return jsonify({"error": "未选择文件"}), 400

    uploaded = request.files["file"]
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "未选择文件"}), 400

    original_name = secure_filename(uploaded.filename)
    if not original_name:
        return jsonify({"error": "文件名无效"}), 400

    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    stored_path = Config.UPLOAD_DIR / stored_name
    uploaded.save(stored_path)

    size = stored_path.stat().st_size
    file_record = add_file(original_name, stored_name, size)
    return jsonify({"message": "上传成功", "file": file_record})


@admin_bp.route("/api/admin/files/<file_id>", methods=["DELETE"])
@admin_required
def admin_delete(file_id):
    file_record = delete_file(file_id)
    if file_record is None:
        return jsonify({"error": "文件不存在"}), 404
    return jsonify({"message": "删除成功"})


@admin_bp.route("/api/admin/change-password", methods=["POST"])
@admin_required
def admin_change_password():
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    ok, message = change_password(old_password, new_password)
    if not ok:
        return jsonify({"error": message}), 400
    return jsonify({"message": message})
