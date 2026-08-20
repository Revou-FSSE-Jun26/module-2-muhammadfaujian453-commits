from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Products, Orders, order_items
from sqlalchemy.exc import SQLAlchemyError
from auth import roles_required

order_bp = Blueprint('order', __name__, url_prefix='/orders')

# =========================================================================
# ORDER MODULE (BLUEPRINT: order_bp | PREFIX: /orders)
# =========================================================================

# Place a New Order Route
@order_bp.route('', methods=['POST'])
@role_required(['buyer', 'seller'])
def create_order():
    data = request.get_json(silent=True) or {}

    user_id = data.get('user_id') or request.args.get('user_id')
    items_data = data.get('items')

    if not items_data or not isinstance(items_data, list):
        return jsonify({"error": "The 'items' field is required and must be a list of products!"}), 400

    aggregated_cart = {}
    for item in items_data:
        p_id = item.get('product_id')
        raw_qty = item.get('quantity')
        
        if not p_id or raw_qty is None:
            return jsonify({"error": "Each item must include product_id and quantity!"}), 400

        try:
            qty = int(raw_qty)
        except (ValueError, TypeError):
            return jsonify({"error": "Bad Request! Quantity values must be valid integers."}), 400

        if qty <= 0:
            return jsonify({"error": "Quantity must be greater than 0!"}), 400

        if p_id in aggregated_cart:
            aggregated_cart[p_id] += qty
        else:
            aggregated_cart[p_id] = qty


    try:
        total_amount = 0
        order_items_to_create = []

        for p_id, qty in aggregated_cart.items():
            product = Products.query.get(p_id)
            if not product:
                return jsonify({"error": f"Product with ID {p_id} not found!"}), 404

            if product.seller_id == int(user_id):
                return jsonify({"error": f"Violation! You cannot purchase your own product '{product.name}' from your own store."}), 400

            if product.stock < qty:
                return jsonify({"error": f"Insufficient stock for product '{product.name}'! Available stock: {product.stock}"}), 400

            item_price = float(product.price)
            total_amount += item_price * int(qty)

            product.stock -= int(qty)

            order_items_to_create.append({
                "product_id": p_id,
                "quantity": int(qty),
                "unit_price": item_price
            })

        new_order = Orders(user_id=user_id, status='PENDING', total_amount=total_amount)
        db.session.add(new_order)
        db.session.flush()

        for oi in order_items_to_create:
            statement = order_items.insert().values(
                order_id=new_order.id,
                product_id=oi["product_id"],
                quantity=oi["quantity"],
                unit_price=oi["unit_price"]
            )
            db.session.execute(statement)

        db.session.commit()

        return jsonify({
            "message": "Order successfully placed!",
            "order": new_order.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while processing checkout order!",
            "details": str(e.__dict__.get('orig', e))
        }), 500