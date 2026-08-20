from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Users, Orders
from sqlalchemy.exc import SQLAlchemyError
from auth import roles_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
users_bp = Blueprint('users', __name__, url_prefix='/users')

# =========================================================================
# 1. USER MODULE (BLUEPRINT: auth_bp | PREFIX: /auth)
# =========================================================================

# A. New User Registration Route
@auth_bp.route('', methods = ['POST'])
def register_user():
    """Register a new user
    ---
    tags:
      - Users
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - full_name
          properties:
            email:
              type: string
              example: "johndoe@example.com"
            password:
              type: string
              example: "securepassword123"
            full_name:
              type: string
              example: "John Doe"
            role:
              type: string
              example: "buyer"
              enum: ['admin', 'buyer', 'seller']
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing required fields or invalid role
      409:
        description: Email already registered
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}

    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'buyer')

    if not email or not password or not full_name:
        return jsonify({"error": "The email, password, and full_name fields are required!"}), 400

    if role not in ['admin', 'buyer', 'seller']:
        return jsonify({"error": "Invalid role! Options: admin, buyer, seller"}), 400

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered on the system!"}), 409

    try:
        new_user = Users(email=email, full_name=full_name, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User registration successful",
            "user": new_user.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "An internal database operation failure occurred!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save data: {str(e)}"}), 500


# B. Retrieve Specific User Route
@auth_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_by_id(user_id):
    """Get user profile by ID
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The user ID
    responses:
      200:
        description: User profile details
      403:
        description: Forbidden (Not the owner and not an admin)
      404:
        description: User not found
    """
    
    # Identity extraction from JWT Token
    requester_id = int(get_jwt_identity())
    claims = get_jwt()
    requester_role= claims.get('role')

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found on the system!"}), 404

        if requester_id != user_id and requester_role != 'admin':
            return jsonify({"error": "Unauthorized! You can only view your own profile data unless you are an admin."}), 403
    
        return jsonify({
            "message": "User data successfully retrieved!",
            "user": user.to_dict()
        }), 200
    
    except SQLAlchemyError as e:
        return jsonify({
            "error": "Failed to retrieve data from the database!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# C. Delete User Account Route
@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete user account
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The user ID
    responses:
      200:
        description: Account successfully deleted
      400:
        description: Deletion guard triggered (linked orders or active products)
      403:
        description: Forbidden (Not the owner and not an admin)
      404:
        description: User not found
    """

    # Identity extraction from JWT Token
    requester_id = int(get_jwt_identity())
    claims = get_jwt()
    requester_role = claims.get('role')

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found on the system!"}), 404

        if requester_id != user_id and requester_role != 'admin':
            return jsonify({"error": "Unauthorized! You can only delete your own account unless you are an admin."}), 403

        any_purchase_history = Orders.query.filter_by(user_id=user_id).first()
        if any_purchase_history:
            return jsonify({
                "error": "Cannot delete account! This user profile is linked to historical purchase order records."
            }), 400

        if user.role == 'seller' and user.seller_profile:
            if user.seller_profile.products:
                return jsonify({
                    "error": "Cannot delete account! Your store still has active products listed. Please delete all products first."
                }), 400

        db.session.delete(user)
        db.session.commit()

        return jsonify({
            "message": f"User with ID {user_id} and its associated store profile have been successfully deleted!"
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while deleting user account!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# =========================================================================
# 2. AUTH MODULE (BLUEPRINT: auth_bp | PREFIX: /auth)
# =========================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login and generate JWT Token
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "johndoe@example.com"
            password:
              type: string
              example: "securepassword123"
    responses:
      200:
        description: Login successful, returns JWT token
      400:
        description: Missing email or password
      401:
        description: Invalid credentials
    """
    data = request.get_json(silent=True) or ()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": 'Missing email or password'}), 400

    # Retrieve user and verify password
    user = Users.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": 'Invalid email or password'}), 401

    # Generate JWT Token carrying the user's ID and Role
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({
        "message": 'Login successful',
        "token": token,
        'user': user.to_dict()
    }), 200