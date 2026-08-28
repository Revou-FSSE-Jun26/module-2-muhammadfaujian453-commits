"""Order service — business logic for checkout (split-by-seller, stock
deduction) and order lifecycle management."""
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from app.models import Orders, OrderItems, Carts, cart_items, Products
from app.utils import db


def checkout(user_id, validated_data):
    """
    Convert the user's cart into one Order PER SELLER (split-order logic).

    WARNING: `.with_for_update(of=Products)` below takes a database row lock
    on each product before checking stock. Do NOT remove this while moving
    code around — without it, two customers checking out the same product
    at nearly the same time could both pass the stock check and oversell it.
    This lock is why the whole loop must stay inside one transaction.
    """
    shipping_address = validated_data['shipping_address']

    cart = Carts.query.filter_by(user_id=user_id).first()
    if not cart:
        return None, {"message": "Cart not found", "status_code": 404}

    items = db.session.query(cart_items).filter_by(cart_id=cart.id).order_by(cart_items.c.product_id).all()
    if not items:
        return None, {"message": "Your cart is empty. Cannot proceed to checkout.", "status_code": 400}

    seller_groups = {}
    for item in items:
        product = Products.query.with_for_update(of=Products).filter_by(id=item.product_id, is_active=True).first()
        if not product:
            db.session.rollback()
            return None, {"message": f"Product with ID {item.product_id} is no longer available!", "status_code": 400}
        if item.quantity > product.stock:
            db.session.rollback()
            return None, {"message": f"Insufficient stock for '{product.name}'. Only {product.stock} left.", "status_code": 400}
        seller_groups.setdefault(product.seller_id, []).append((item, product))

    try:
        created_orders = []
        for seller_id, group_items in seller_groups.items():
            order = Orders(user_id=user_id, seller_id=seller_id, shipping_address=shipping_address, total_amount=0)
            db.session.add(order)
            db.session.flush()  # need order.id before creating its OrderItems rows

            order_total = 0
            for item, product in group_items:
                product.stock -= item.quantity  # stock deduction
                subtotal = float(product.price) * item.quantity
                order_total += subtotal
                db.session.add(OrderItems(
                    order_id=order.id, product_id=product.id,
                    quantity=item.quantity, unit_price=product.price
                ))

            order.total_amount = order_total
            created_orders.append(order)

        db.session.execute(delete(cart_items).where(cart_items.c.cart_id == cart.id))
        db.session.commit()
        return created_orders, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def get_my_orders(user_id, status_filter=None):
    query = Orders.query.filter_by(user_id=user_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    return query.order_by(Orders.created_at.desc()).all()


def get_order_details(order_id, requester_id, requester_role):
    order = db.session.get(Orders, order_id)
    if not order:
        return None, {"message": "Order not found!", "status_code": 404}
    if requester_role != 'admin' and order.user_id != requester_id and order.seller_id != requester_id:
        return None, {"message": "Unauthorized! You can only view your own orders.", "status_code": 403}
    return order, None


def update_order_status(order_id, requester_id, requester_role, validated_data):
    new_status = validated_data['status']
    order = db.session.get(Orders, order_id)
    if not order:
        return None, {"message": "Order not found!", "status_code": 404}

    if requester_role != 'admin':
        if order.user_id == requester_id:
            if new_status != 'cancelled' or order.status != 'pending':
                return None, {"message": "Buyers can only change status to 'cancelled' while it is still pending.", "status_code": 403}
        elif order.seller_id == requester_id:
            if new_status == 'cancelled':
                return None, {"message": "Sellers cannot cancel orders. Contact admin.", "status_code": 403}
        else:
            return None, {"message": "Unauthorized! You are not involved in this order.", "status_code": 403}

    try:
        if new_status == 'cancelled' and order.status != 'cancelled':
            for item in order.order_items:
                product = db.session.get(Products, item.product_id)
                if product:
                    product.stock += item.quantity  # restock on cancellation

        order.status = new_status
        db.session.commit()
        return order, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}

def delete_order(order_id, requester_id, requester_role):
    order = db.session.get(Orders, order_id)
    if not order:
        return None, {"message": "Order not found", "status_code": 404}

    if requester_role != 'admin' and order.user_id != requester_id and order.seller_id != requester_id:
        return None, {"message": "Unauthorized! You can only delete your own orders.", "status_code": 403}

    if order.status != 'cancelled':
        return None, {"message": "Order is not cancelled (immutable constraint)", "status_code": 400}

    try:
        db.session.delete(order)
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}
