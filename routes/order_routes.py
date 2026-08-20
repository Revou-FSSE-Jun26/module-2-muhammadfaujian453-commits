from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Orders, order_items, Carts, cart_items, Products
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import insert, delete

order_bp = Blueprint('order', __name__, url_prefix='/orders')

# =========================================================================
# ORDER MODULE (BLUEPRINT: order_bp | PREFIX: /orders)
# =========================================================================

# A. Place a New Order Route
@order_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    """Checkout cart items into an order
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - shipping_address
          properties:
            shipping_address:
              type: string
    responses:
      201:
        description: Order successfully created
      400:
        description: Cart is empty or validation error
      404:
        description: Cart not found
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    shipping_address = data.get('shipping_address')

    if not shipping_address or not str(shipping_address).strip:
        return jsonify({"error": "The 'shipping_address' field is required!"}), 400

    try:
        cart = Carts.query.filter_by(user_id=user_id).first()
        if not cart:
            return jsonify({"error": "Cart not found"}), 404

        items = db.session.query(cart_items).filter_by(cart_id=cart.id).order_by(cart_items.c.product_id).all()
        if not items:
            return jsonify({"error": "Your cart is empty. Cannot proceed to checkout."}), 400

        new_order = Orders(
            user_id=user_id,
            shipping_address=shipping_address
        )
        db.session.add(new_order)
        db.session.flush()

        for item in items:
            product = Products.query.with_for_update().filter_by(id=item.product_id, is_active=True).first()

            if not product:
                db.session.rollback()
                return jsonify({"error": f"Product with ID {item.product_id} is no longer available!"}), 400
                
            if item.quantity > product.stock:
                db.session.rollback()
                return jsonify({"error": f"Insufficient stock for '{product.name}'. Only {product.stock} left."}), 400

            product.stock -= item.quantity

            stmt = insert(order_items).values(
                order_id=new_order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price
            )
            db.session.execute(stmt)

        del_stmt = delete(cart_items).where(cart_items.c.cart_id == cart.id)
        db.session.execute(del_stmt)

        db.session.commit()

        return jsonify({
            "message": "Checkout successful! Your order has been placed.",
            "order_id": new_order.id
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error":"Database error during checkout",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# B. Retrieve all order that placed by current user
@order_bp.route('', methods=['GET'])
@jwt_required()
def get_my_orders():
    """Retrieve all orders placed by the current user
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    responses:
      200:
        description: List of user's orders
    """
    user_id = int(get_jwt_identity())
    
    try:
        orders = Orders.query.filter_by(user_id=user_id).order_by(Orders.created_at.desc()).all()
        return jsonify({
            "message": "Orders retrieved successfully",
            "orders": [order.to_dict() for order in orders]
        }), 200
        
    except SQLAlchemyError as e:
        return jsonify({
            "error": "Database error",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# C. Get specific order details and its item
@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    """Get specific order details and its items
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    responses:
      200:
        description: Order details
      403:
        description: Forbidden (Not the owner)
      404:
        description: Order not found
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role')

    try:
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found!"}), 404

        if order.user_id != user_id and role != 'admin':
            return jsonify({"error": "Unauthorized! You can only view your own orders."}), 403

        # Snapshot current price
        items_data = db.session.query(
            order_items.c.quantity,
            order_items.c.unit_price,
            Products.name
        ).join(Products, Products.id == order_items.c.product_id)\
         .filter(order_items.c.order_id == order_id).all()

        details = []
        total_order_price = 0
        
        for qty, price, name in items_data:
            subtotal = float(price) * qty
            total_order_price += subtotal
            details.append({
                "product_name": name,
                "quantity": qty,
                "unit_price": float(price),
                "subtotal": subtotal
            })

        order_dict = order.to_dict()
        order_dict['items'] = details
        order_dict['total_amount'] = total_order_price

        return jsonify({
            "message": "Order details retrieved successfully",
            "order": order_dict
        }), 200

    except SQLAlchemyError as e:
        return jsonify({
            "error": "Database error",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# D. Update order status route
@order_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    """Update order status (Logistics/Cancellation)
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [pending, processing, shipped, delivered, canceled]
    responses:
      200:
        description: Status successfully updated
      400:
        description: Invalid status transition
      403:
        description: Forbidden action
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role')

    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'canceled']
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status! Must be one of: {valid_statuses}"}), 400

    try:
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found!"}), 404

        # Cancelation only when status "pending"
        if role != 'admin':
            if order.user_id != user_id:
                return jsonify({"error": "Unauthorized! You do not own this order."}), 403
            
            if new_status != 'canceled':
                return jsonify({"error": "Users can only change status to 'canceled'."}), 403
                
            if order.status != 'pending':
                return jsonify({"error": f"Cannot cancel order. Current status is already '{order.status}'."}), 400

        # Cancelation
        if new_status == 'canceled' and order.status != 'canceled':
            items = db.session.query(order_items).filter_by(order_id=order.id).all()
            for item in items:
                product = Products.query.get(item.product_id)
                if product:
                    product.stock += item.quantity
                    
        order.status = new_status
        db.session.commit()

        return jsonify({
            "message": f"Order status successfully updated to '{new_status}'!",
            "order": order.to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database error",
            "details": str(e.__dict__.get('orig', e))
        }), 500