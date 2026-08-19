from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
import bcrypt

# =========================================================================
# BCRYPT HASHING LOGIC
# =========================================================================
def hash_password(plain_password):
    """Hash a plain text password using bcrypt."""
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt().decode('utf-8'))

def check_password(plain_password, hashed_password):
    """Verify a plain text password againt its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# =========================================================================
# JWT AUTHORIZATION MIDDLEWARE
# =========================================================================
def roles_required(*allowed_roles):
    """
    Decorator that checks if the current user has one of the allowed roles.
    Extracts the role claim directly from the JWT payload.
    """
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
