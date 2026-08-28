import bcrypt
from functools import wraps
from flask import jsonify
from app.utils import db
from flask_jwt_extended import get_jwt, verify_jwt_in_request, get_jwt_identity

# =========================================================================
# BCRYPT HASHING LOGIC
# =========================================================================
def hash_password(password: str) -> str:
    """Generate bcrypt hash from plain text password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Verify a plain text password againt its bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# =========================================================================
# JWT AUTHORIZATION MIDDLEWARE
# =========================================================================
def roles_required(*allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Verify the token exists and is valid
            verify_jwt_in_request()

            # Extract claims from the token
            claims = get_jwt()
            user_role = claims.get("role", "buyer")

            # Block access if the role is not permitted
            if user_role not in allowed_roles:
                return jsonify ({
                    "error": "Forbidden",
                    "message": f"Access denied. Required role(s): {', '.join(allowed_roles)}"
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper

def seller_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            from app.models import Sellers
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())

            store = db.session.get(Sellers, user_id)
            if not store or not store.is_active:
                return jsonify({
                    "error": "forbidden",
                    "message": "Access denied. You must be register an active store first to perform this action."
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
