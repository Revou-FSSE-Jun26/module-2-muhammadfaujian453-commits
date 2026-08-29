"""Cart service — business logic for the shopping cart, including quantity merging."""
import logging
from sqlalchemy import insert, update, delete
from sqlalchemy.exc import SQLAlchemyError
from app.models import Carts, Products, cart_items
from app.utils import db


def get_or_create_cart(user_id):
    cart = Carts.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Carts(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
    return cart


def add_item(user_id, validated_data):
    product_id, quantity = validated_data['product_id'], validated_data['quantity']

    product = Products.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return None, {"message": "Product not found or is no longer active!", "status_code": 404}
    if product.seller_id == user_id:
        return None, {"message": "You cannot add your own product to the cart!", "status_code": 403}
    if quantity > product.stock:
        return None, {"message": f"Insufficient stock! Only {product.stock} items left.", "status_code": 400}

    cart = get_or_create_cart(user_id)

    # Quantity-merge: if already in the cart, add to the existing row instead of creating a duplicate.
    existing_item = db.session.query(cart_items).filter(
        cart_items.c.cart_id == cart.id, cart_items.c.product_id == product_id
    ).first()

    try:
        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if new_quantity > product.stock:
                return None, {"message": f"Cannot add more. Stock limit reached ({product.stock} max).", "status_code": 400}
            stmt = update(cart_items).where(
                cart_items.c.cart_id == cart.id, cart_items.c.product_id == product_id
            ).values(quantity=new_quantity)
        else:
            stmt = insert(cart_items).values(cart_id=cart.id, product_id=product_id, quantity=quantity)

        db.session.execute(stmt)
        db.session.commit()
        return cart, None
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def view_cart(user_id):
    cart = get_or_create_cart(user_id)
    rows = (
        db.session.query(cart_items.c.product_id, cart_items.c.quantity, Products)
        .join(Products, Products.id == cart_items.c.product_id)
        .filter(cart_items.c.cart_id == cart.id)
        .all()
    )

    items, total_price = [], 0
    for product_id, quantity, product in rows:
        if not product.is_active:
            continue
        subtotal = float(product.price) * quantity
        total_price += subtotal
        items.append({
            "product_id": product_id, "product_name": product.name, "price": float(product.price),
            "quantity": quantity, "subtotal": subtotal, "image_url": product.image_url
        })

    return {"cart_id": cart.id, "items": items, "total_price": total_price}


def update_item(user_id, product_id, validated_data):
    quantity = validated_data['quantity']
    cart = get_or_create_cart(user_id)

    try:
        if quantity == 0:
            db.session.execute(delete(cart_items).where(
                cart_items.c.cart_id == cart.id, cart_items.c.product_id == product_id))
            db.session.commit()
            return {"removed": True}, None

        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return None, {"message": "Product not found or inactive!", "status_code": 404}
        if quantity > product.stock:
            return None, {"message": f"Insufficient stock! Only {product.stock} items left.", "status_code": 400}

        result = db.session.execute(update(cart_items).where(
            cart_items.c.cart_id == cart.id, cart_items.c.product_id == product_id
        ).values(quantity=quantity))
        if result.rowcount == 0:
            return None, {"message": "Item not found in your cart!", "status_code": 404}

        db.session.commit()
        return {"removed": False}, None
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def delete_item(user_id, product_id):
    cart = get_or_create_cart(user_id)
    try:
        result = db.session.execute(delete(cart_items).where(
            cart_items.c.cart_id == cart.id, cart_items.c.product_id == product_id))
        if result.rowcount == 0:
            return None, {"message": "Item not found in your cart!", "status_code": 404}
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}


def clear_cart(user_id):
    cart = get_or_create_cart(user_id)
    try:
        db.session.execute(delete(cart_items).where(cart_items.c.cart_id == cart.id))
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return None, {"message": "A database error occurred processing your request.", "status_code": 500}