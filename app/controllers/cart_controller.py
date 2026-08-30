from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas import CartAddItemSchema, CartUpdateItemSchema, CartResponseSchema
from app.services import cart_service

# Blueprint
cart_bp = Blueprint('cart', __name__, url_prefix='/carts')

# Schemas
add_schema = CartAddItemSchema()
update_schema = CartUpdateItemSchema()
response_schema = CartResponseSchema()

# =========================================================================
# CART MODULE (BLUEPRINT: cart_bp | PREFIX: /carts)
# =========================================================================

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
    validated_data = add_schema.load(data)
    user_id = int(get_jwt_identity())
    
    _, error = cart_service.add_item(user_id, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({"message": "Item successfully added to cart!"}), 200


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
    cart_data = cart_service.view_cart(user_id)
    
    return jsonify({
        "message": "Cart retrieved successfully",
        **response_schema.dump(cart_data)
    }), 200


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
    validated_data = update_schema.load(data)
    user_id = int(get_jwt_identity())

    result, error = cart_service.update_item(user_id, product_id, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    message = "Item removed from cart!" if result.get("removed") else "Cart item updated successfully!"
    return jsonify({"message": message}), 200


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

    _, error = cart_service.delete_item(user_id, product_id)
    
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({"message": "Item successfully removed from cart!"}), 200


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

    _, error = cart_service.clear_cart(user_id)
    
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]
        
    return jsonify({"message": "Cart cleared successfully!"}), 200
        