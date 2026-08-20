from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Users
from validation import validate_user_registration
from sqlalchemy.exc import SQLAlchemyError

# Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
users_bp = Blueprint('users', __name__, url_prefix='/users')

# =========================================================================
# 1. USER MODULE (BLUEPRINT: users_bp | PREFIX: /users)
# =========================================================================

# A. New User Registration Route
@users_bp.route('', methods = ['POST'])
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
            avatar_url:
              type: string
              example: "https://example.com/avatar.jpg"
    responses:
      201:
        description: User registered successfully
      400:
        description: Missing required fields or validation error
      409:
        description: Email already registered
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}

    validation_errors = validate_user_registration(data)
    if validation_errors:
        return jsonify({"error": "Validation failed", "details": validation_errors}), 400

    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    avatar_url = data.get('avatar_url')

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered on the system!"}), 409

    try:
        new_user = Users(email=email, full_name=full_name, avatar_url=avatar_url)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User registration successful",
            "user": new_user.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500


# B. Retrieve Specific User Route
@users_bp.route('/<int:user_id>', methods=['GET'])
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
      500:
        description: Internal server error
    """
    
    # Identity extraction from JWT Token
    requester_id = int(get_jwt_identity())
    claims = get_jwt()
    requester_role= claims.get('role')

    try:
        user = Users.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": f"Active user with ID {user_id} not found!"}), 404

        if requester_id != user_id and requester_role != 'admin':
            return jsonify({"error": "Unauthorized! You can only view your own profile data unless you are an admin."}), 403
    
        return jsonify({
            "message": "User data successfully retrieved!",
            "user": user.to_dict()
        }), 200
    
    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

# C. Delete User Account Route
@users_bp.route('/<int:user_id>', methods=['DELETE'])
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
        description: Account successfully deactivated
      403:
        description: Forbidden (Not the owner and not an admin)
      404:
        description: User not found
      500:
        description: Internal server error
    """

    # Identity extraction from JWT Token
    requester_id = int(get_jwt_identity())
    claims = get_jwt()
    requester_role = claims.get('role')

    try:
        user = Users.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": f"Active user with ID {user_id} not found!"}), 404

        if requester_id != user_id and requester_role != 'admin':
            return jsonify({"error": "Unauthorized! You can only delete your own account unless you are an admin."}), 403

        user.is_active = False

        if user.seller_profile:
            user.seller_profile.is_active = False

            for product in user.seller_profile.products:
                product.is_active = False

        db.session.commit()

        return jsonify({"error": f"User with ID {user_id} and its associated data successfully deactivated"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

# D. Retrieve Current Authenticated User Route
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user profile
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Current user profile details
      401:
        description: Unauthorized (Missing or invalid token)
      404:
        description: User not found
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())

    try:
        user = Users.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({"error": "Active user not found!"}), 404
    
        return jsonify({
            "message": "Current user data successfully retrieved!",
            "user": user.to_dict()
        }), 200
    
    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

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
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": 'Missing email or password'}), 400

    # Retrieve user and verify password
    user = Users.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": 'Invalid email or password'}), 401

    message = 'Login successful'
    if not user.is_active:
        user.is_active = True

        if user.seller_profile:
            user.seller_profile.is_active = True

            for product in user.seller_profile.products:
                product.is_active = True

        db.session.commit()
        message = 'Login successful. Your account has been reactivated!'

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