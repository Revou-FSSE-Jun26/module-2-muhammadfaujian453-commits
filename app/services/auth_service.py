"""Auth service — business logic for authentication."""
from flask_jwt_extended import create_access_token
from app.models import Users
from app.middleware.auth import check_password
from app.utils import db


def authenticate_user(email, password):
    """
    Verify credentials, issue a JWT, and reactivate a soft-deleted account on successful login.
    
    Returns:
        (result_dict, None) on success — result_dict has 'message', 'token', 'user'
        (None, error_dict) on failure
    """
    user = Users.query.filter_by(email=email).first()

    if user is None or not check_password(password, user.password_hash):
        return None, {"message": "Invalid email or password", "status_code": 401}

    message = "Login successful"
    if not user.is_active:
        user.is_active = True
        if user.seller_profile:
            user.seller_profile.is_active = True
            for product in user.seller_profile.products:
                product.is_active = True
        db.session.commit()
        message = "Login successful. Your account has been reactivated!"

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return {"message": message, "token": token, "user": user}, None
