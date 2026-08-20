from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import db
from models import Users, Sellers
from sqlalchemy.exc import SQLAlchemyError

seller_bp = Blueprint('seller', __name__, url_prefix='/sellers')

# =========================================================================
# SELLER MODULE (BLUEPRINT: seller_bp | PREFIX: /sellers)
# =========================================================================

# A. Register/Create Store Profile Route
@seller_bp.route('', methods=['POST'])
@jwt_required()
def create_store():
    """Register a store profile and upgrade account role
    ---
    tags:
      - Sellers
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - store_name
          properties:
            store_name:
              type: string
              example: "Toko Angkasa Elektrik"
            store_description:
              type: string
              example: "Distributor utama panel dan komponen kelistrikan"
    responses:
      201:
        description: Store profile successfully created
      400:
        description: Missing store_name or profile already exists
      401:
        description: Unauthorized (Invalid token)
      409:
        description: Store name is already taken by another user
      500:
        description: Internal database error
    """

    data = request.get_json(silent=True) or {}

    user_id =int(get_jwt_identity())
    
    store_name = data.get('store_name')
    store_description = data.get('store_description')

    if not store_name:
        return jsonify({"error": "The 'store_name' field is required!"}), 400

    existing_store = Sellers.query.get(user_id)
    if existing_store:
        return jsonify({"error": "Your account already has a registered store!"}), 400

    duplicate_name = Sellers.query.filter_by(store_name=store_name).first()
    if duplicate_name:
        return jsonify({"error": f"Store name '{store_name}' is already taken!"}), 409

    try:
        new_store = Sellers(
            id=user_id,
            store_name=store_name,
            store_description=store_description
        )
        db.session.add(new_store)

        # Upgrade the user role from buyer -> seller
        user = Users.query.get(user_id)
        if user and user.role == 'buyer':
            user.role = 'seller'

        db.session.commit()

        return jsonify({
            "message": "Store profile successfully created! Your account role has been upgraded to 'seller'.",
            "store": new_store.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while creating store profile!",
            "details": str(e.__dict__.get('orig', e))
        }), 500