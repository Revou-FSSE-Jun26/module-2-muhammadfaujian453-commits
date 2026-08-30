"""User service — business logic for registration, profile lookup, and account deactivation."""
import logging
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import Users
from app.utils import db


def register_user(validated_data):
    try:
        user = Users(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            avatar_url=validated_data.get('avatar_url')
        )
        user.set_password(validated_data['password'])
        db.session.add(user)
        db.session.commit()
        return user, None
    except IntegrityError:
        db.session.rollback()
        return None, {"message": "Email already registered on the system!", "status_code": 409}
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def get_user_by_id(target_user_id, requester_id, requester_role):
    user = db.session.get(Users, target_user_id)
    if not user or not user.is_active:
        return None, {"message": f"Active user with ID {target_user_id} not found!", "status_code": 404}
    if requester_id != target_user_id and requester_role != 'admin':
        return None, {"message": "Unauthorized! You can only view your own profile data unless you are an admin.", "status_code": 403}
    return user, None


def get_current_user(user_id):
    user = db.session.get(Users, user_id)
    if not user or not user.is_active:
        return None, {"message": "Active user not found!", "status_code": 404}
    return user, None


def delete_user(target_user_id, requester_id, requester_role):
    user = db.session.get(Users, target_user_id)
    if not user or not user.is_active:
        return None, {"message": f"Active user with ID {target_user_id} not found!", "status_code": 404}
    if requester_id != target_user_id and requester_role != 'admin':
        return None, {"message": "Unauthorized! You can only delete your own account unless you are an admin.", "status_code": 403}

    user.is_active = False
    if user.seller_profile:
        user.seller_profile.is_active = False
        for product in user.seller_profile.products:
            product.is_active = False
    db.session.commit()
    return user, None
