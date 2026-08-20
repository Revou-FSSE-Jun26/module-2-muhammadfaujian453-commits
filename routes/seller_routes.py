from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import db
from models import Sellers, Products
from sqlalchemy.exc import SQLAlchemyError
from auth import seller_required

# Blueprint
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
            avatar_url:
              type: string
              example: "https://example.com/logo.png"
    responses:
      201:
        description: Store profile successfully created
      400:
        description: Missing store_name or profile already exists
      409:
        description: Store name is already taken by another user
      500:
        description: Internal database error
    """

    data = request.get_json(silent=True) or {}
    user_id =int(get_jwt_identity())
    
    store_name = data.get('store_name')
    store_description = data.get('store_description')
    avatar_url = data.get('avatar_url')

    if not store_name:
        return jsonify({"error": "The 'store_name' field is required!"}), 400

    existing_store = Sellers.query.get(user_id)
    if existing_store:
        if not existing_store.is_active:
            return jsonify({"error": "You already have a deactivated store. Please use the update endpoint to reactivate it."}), 400
        return jsonify({"error": "Your account already has a registered store!"}), 400

    duplicate_name = Sellers.query.filter_by(store_name=store_name).first()
    if duplicate_name:
        return jsonify({"error": f"Store name '{store_name}' is already taken!"}), 409

    try:
        new_store = Sellers(
            id=user_id,
            store_name=store_name,
            store_description=store_description,
            avatar_url =avatar_url
        )
        db.session.add(new_store)
        db.session.commit()

        return jsonify({
            "message": "Store profile successfully created!",
            "store": new_store.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# B. Get store by seller ID route
@seller_bp.route('/<int:seller_id>', methods=['GET'])
def get_store_profile(seller_id):
    """View public store profile
    ---
    tags:
      - Sellers
    parameters:
      - in: path
        name: seller_id
        type: integer
        required: true
        description: The ID of the store (same as user ID)
    responses:
      200:
        description: Store profile details
      404:
        description: Store not found or inactive
    """
    try:
        store = Sellers.query.filter_by(id=seller_id, is_active=True).first()
        
        if not store:
            return jsonify({"error": f"Active store with ID {seller_id} not found!"}), 404

        return jsonify({
            "message": "Store profile retrieved successfully",
            "store": store.to_dict()
        }), 200

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error", "details": str(e.__dict__.get('orig', e))}), 500

# C. Update store route
@seller_bp.route('', methods=['PUT'])
@jwt_required()
@seller_required()
def update_store():
    """Update store profile (Partial Update)
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
          properties:
            store_name:
              type: string
            store_description:
              type: string
            avatar_url:
              type: string
            is_active:
              type: boolean
              description: Pass true to reactivate a closed store
    responses:
      200:
        description: Store profile updated successfully
      409:
        description: New store name is already taken
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    
    try:
        store = Sellers.query.get(user_id)
        
        new_name = data.get('store_name')
        
        if new_name and new_name != store.store_name:
            duplicate = Sellers.query.filter_by(store_name=new_name).first()
            if duplicate:
                return jsonify({"error": f"Store name '{new_name}' is already taken!"}), 409
            store.store_name = new_name
            
        if 'store_description' in data:
            store.store_description = data.get('store_description')
        if 'avatar_url' in data:
            store.avatar_url = data.get('avatar_url')
        if 'is_active' in data:
            store.is_active = data.get('is_active')

        db.session.commit()

        return jsonify({
            "message": "Store profile updated successfully",
            "store": store.to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e.__dict__.get('orig', e))}), 500

# D. Delete/close store route
@seller_bp.route('', methods=['DELETE'])
@jwt_required()
@seller_required()
def close_store():
    """Deactivate store (Soft Delete)
    ---
    tags:
      - Sellers
    security:
      - Bearer: []
    responses:
      200:
        description: Store and its products successfully deactivated
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())
    
    try:
        store = Sellers.query.get(user_id)
        
        # Soft delete the store
        store.is_active = False
        
        # Cascade soft-delete:
        products = Products.query.filter_by(seller_id=user_id).all()
        for product in products:
            product.is_active = False
            
        db.session.commit()

        return jsonify({
            "message": "Your store and all associated products have been deactivated."
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e.__dict__.get('orig', e))}), 500