from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Orders, OrderItems, Carts, cart_items, Products
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
    """Checkout cart items into split order based on sellers
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

    if not shipping_address or not str(shipping_address).strip():
        return jsonify({"error": "The 'shipping_address' field is required!"}), 400

    try:
        cart = Carts.query.filter_by(user_id=user_id).first()
        if not cart:
            return jsonify({"error": "Cart not found"}), 404

        items = db.session.query(cart_items).filter_by(cart_id=cart.id).order_by(cart_items.c.product_id).all()
        if not items:
            return jsonify({"error": "Your cart is empty. Cannot proceed to checkout."}), 400

        seller_groups = {} 
        for item in items:
            product = Products.query.with_for_update().filter_by(id=item.product_id, is_active=True).first()
            if not product:
                db.session.rollback()
                return jsonify({"error": f"Product with ID {item.product_id} is no longer available!"}), 400
                
            if item.quantity > product.stock:
                db.session.rollback()
                return jsonify({"error": f"Insufficient stock for '{product.name}'. Only {product.stock} left."}), 400

            seller_id = product.seller_id
            if seller_id not in seller_groups:
                seller_groups[seller_id] = []

            seller_groups[seller_id].append((item, product))

        created_orders = []

        for seller_id, group_items in seller_groups.items():
            new_order = Orders(
                user_id=user_id,
                seller_id=seller_id, # Injeksi seller_id ke tabel Orders
                shipping_address=shipping_address,
                total_amount=0 # Diberi nilai awal 0
            )
            db.session.add(new_order)
            db.session.flush()

            total_order_price = 0

            for item, product in group_items:
                product.stock -= item.quantity

                subtotal = float(product.price) * item.quantity
                total_order_price += subtotal

                order_item = OrderItems(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=product.price
                )
                db.session.add(order_item)

            new_order.total_amount = total_order_price
            created_orders.append(new_order.to_dict())

        del_stmt = delete(cart_items).where(cart_items.c.cart_id == cart.id)
        db.session.execute(del_stmt)
        
        db.session.commit()

        return jsonify({
            "message": "Checkout successful!", 
            "orders_created": len(created_orders),
            "orders": created_orders
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

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
    parameters:
      - in: query
        name: status
        type: string
        enum: [pending, processing, shipped, delivered, canceled]
    responses:
      200:
        description: List of user's orders
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())

    status_filter = request.args.get('status', type=str)
    
    try:
        query = Orders.query.filter_by(user_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
            
        orders = query.order_by(Orders.created_at.desc()).all()
        
        return jsonify({
            "message": "Orders retrieved successfully",
            "orders": [order.to_dict() for order in orders] 
        }), 200
        
    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

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
        description: Forbidden (Not the buyer or seller)
      404:
        description: Order not found
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role')

    try:
        order = Orders.query.get(order_id)
        if not order:
            return jsonify({"error": "Order not found!"}), 404

        if role != 'admin' and order.user_id != user_id and order.seller_id != user_id:
            return jsonify({"error": "Unauthorized! You can only view your own orders."}), 403

        return jsonify({
            "message": "Order details retrieved successfully",
            "order": order.to_dict() # Karena sudah direlasi, ini otomatis mengekstrak items
        }), 200 

    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

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
      404:
        description: Order not found
      500:
        description: Internal server error
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

        # Cancelation logic
        if role != 'admin':
            if order.user_id == user_id:
                if new_status != 'canceled' or order.status != 'pending':
                    return jsonify({"error": "Buyers can only change status to 'canceled' while it is still pending."}), 403
            elif order.seller_id == user_id:
                if new_status == 'canceled':
                    return jsonify({"error": "Sellers cannot cancel orders. Contact admin."}), 403
            else:
                return jsonify({"error": "Unauthorized! You are not involved in this order."}), 403

        # Add stock when it's cancelled
        if new_status == 'canceled' and order.status != 'canceled':
            for item in order.items:
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
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        