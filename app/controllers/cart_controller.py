from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import insert, update, delete
from app.utils import db
from app.models import Carts, Products, cart_items
from sqlalchemy.exc import SQLAlchemyError

cart_bp = Blueprint('cart', __name__, url_prefix='/carts')

# =========================================================================
# HELPER FUNCTION
# =========================================================================
def get_or_create_cart(user_id):
    """Search for user cart or make a new cart."""
    cart = Carts.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Carts(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart

# =========================================================================
# CART MODULE (BLUEPRINT: cart_bp | PREFIX: /carts)
# =========================================================================

# A. Add order item to cart route
@cart_bp.route('/items', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add an item to the shopping cart
    ---
    tags:
      - Carts
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - product_id
          properties:
            product_id:
              type: integer
            quantity:
              type: integer
              default: 1
    responses:
      200:
        description: Item successfully added to cart
      400:
        description: Bad request (Validation error or insufficient stock)
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Cannot buy your own product)
      404:
        description: Product not found or inactive
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({"error": "The 'product_id' field is required!"}), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({"error": "Quantity must be greater than zero!"}), 400
    except ValueError:
        return jsonify({"error": "Quantity must be a valid integer!"}), 400

    try:
        # Product Validation
        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({"error": "Product not found or is no longer active!"}), 404

        # Ownership Guard
        if product.seller_id == user_id:
            return jsonify({"error": "You cannot add your own product to the cart!"}), 403

        # Stock Guard
        if quantity > product.stock:
            return jsonify({"error": f"Insufficient stock! Only {product.stock} items left."}), 400

        cart = get_or_create_cart(user_id)

        existing_item = db.session.query(cart_items).filter(
            cart_items.c.cart_id == cart.id,
            cart_items.c.product_id == product_id
        ).first()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if new_quantity > product.stock:
                return jsonify({"error": f"Cannot add more. Stock limit reached ({product.stock} max)."}), 400
            
            stmt = update(cart_items).where(
                cart_items.c.cart_id == cart.id,
                cart_items.c.product_id == product_id
            ).values(quantity=new_quantity)
            db.session.execute(stmt)
        else:
            stmt = insert(cart_items).values(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.execute(stmt)

        db.session.commit()
        return jsonify({"message": "Item successfully added to cart!"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

# B. Retrieve or vew cart route
@cart_bp.route('', methods=['GET'])
@jwt_required()
def view_cart():
    """Retrieve the current user's shopping cart
    ---
    tags:
      - Carts
    security:
      - Bearer: []
    responses:
      200:
        description: Cart details retrieved successfully
      401:
        description: Unauthorized (Invalid or missing token)
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())
    
    try:
        cart = get_or_create_cart(user_id)
        
        # Join table between cart_items and products
        items = (
            db.session.query(
                cart_items.c.product_id,
                cart_items.c.quantity,
                Products
            )
            .join(Products, Products.id == cart_items.c.product_id)
            .filter(cart_items.c.cart_id == cart.id)
            .all()
        )

        cart_data = []
        total_price = 0

        for product_id, quantity, product_obj in items:
            if not product_obj.is_active:
                continue
                
            subtotal = float(product_obj.price) * quantity
            total_price += subtotal
            
            cart_data.append({
                "product_id": product_id,
                "product_name": product_obj.name,
                "price": float(product_obj.price),
                "quantity": quantity,
                "subtotal": subtotal,
                "image_url": product_obj.image_url
            })

        return jsonify({
            "message": "Cart retrieved successfully",
            "cart_id": cart.id,
            "items": cart_data,
            "total_price": total_price
        }), 200

    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

# C. Update cart route
@cart_bp.route('/items/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(product_id):
    """Update the quantity of a specific item in the cart
    ---
    tags:
      - Carts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - quantity
          properties:
            quantity:
              type: integer
    responses:
      200:
        description: Cart item updated successfully
      400:
        description: Bad request (Validation error or insufficient stock)
      401:
        description: Unauthorized (Invalid or missing token)
      404:
        description: Item not found in cart or product not found
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    quantity = data.get('quantity')

    if quantity is None:
        return jsonify({"error": "The 'quantity' field is required!"}), 400

    try:
        quantity = int(quantity)
        if quantity < 0:
            return jsonify({"error": "Quantity cannot be negative!"}), 400
    except ValueError:
        return jsonify({"error": "Quantity must be a valid integer!"}), 400

    try:
        cart = get_or_create_cart(user_id)
        
        if quantity == 0:
            stmt = delete(cart_items).where(
                cart_items.c.cart_id == cart.id,
                cart_items.c.product_id == product_id
            )
            db.session.execute(stmt)
            db.session.commit()
            return jsonify({"message": "Item removed from cart!"}), 200

        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({"error": "Product not found or inactive!"}), 404
            
        if quantity > product.stock:
            return jsonify({"error": f"Insufficient stock! Only {product.stock} items left."}), 400

        stmt = update(cart_items).where(
            cart_items.c.cart_id == cart.id,
            cart_items.c.product_id == product_id
        ).values(quantity=quantity)
        
        result = db.session.execute(stmt)
        if result.rowcount == 0:
            return jsonify({"error": "Item not found in your cart!"}), 404

        db.session.commit()
        return jsonify({"message": "Cart item updated successfully!"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

# D. Delete item from the cart
@cart_bp.route('/items/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_cart_item(product_id):
    """Remove a specific item from the cart
    ---
    tags:
      - Carts
    security:
      - Bearer: []
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
    responses:
      200:
        description: Item removed from cart
      401:
        description: Unauthorized (Invalid or missing token)
      404:
        description: Item not found in cart
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())

    try:
        cart = get_or_create_cart(user_id)
        
        stmt = delete(cart_items).where(
            cart_items.c.cart_id == cart.id,
            cart_items.c.product_id == product_id
        )
        result = db.session.execute(stmt)
        
        if result.rowcount == 0:
            return jsonify({"error": "Item not found in your cart!"}), 404

        db.session.commit()
        return jsonify({"message": "Item successfully removed from cart!"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

# E. Delete/clear all item and its cart
@cart_bp.route('', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Empty the entire shopping cart
    ---
    tags:
      - Carts
    security:
      - Bearer: []
    responses:
      200:
        description: Cart cleared successfully
      401:
        description: Unauthorized (Invalid or missing token)
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())

    try:
        cart = get_or_create_cart(user_id)
        
        stmt = delete(cart_items).where(cart_items.c.cart_id == cart.id)
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({"message": "Cart cleared successfully!"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        