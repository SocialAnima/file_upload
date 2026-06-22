from flask import Flask, jsonify

from app.config import Config
from app.models import init_db
from app.routes.admin import admin_bp
from app.routes.public import public_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(Config.DEFAULT_ADMIN_PASSWORD)

    url_prefix = Config.BASE_PATH or None
    app.register_blueprint(public_bp, url_prefix=url_prefix)
    app.register_blueprint(admin_bp, url_prefix=url_prefix)

    @app.errorhandler(413)
    def request_entity_too_large(_error):
        return jsonify(
            {"error": f"文件大小超过 {Config.MAX_CONTENT_LENGTH // (1024 * 1024)}MB 限制"}
        ), 413

    return app
