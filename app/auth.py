from functools import wraps

from flask import jsonify, session

from app.models import verify_password


def login_admin(password: str) -> bool:
    if verify_password(password):
        session["is_admin"] = True
        return True
    return False


def logout_admin() -> None:
    session.pop("is_admin", None)


def is_admin_logged_in() -> bool:
    return session.get("is_admin") is True


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_admin_logged_in():
            return jsonify({"error": "未登录或登录已过期"}), 401
        return view(*args, **kwargs)

    return wrapped
