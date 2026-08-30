from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.schemas import CheckoutSchema, OrderStatusUpdateSchema, OrderResponseSchema
from app.services import order_service

# Blueprint
order_bp = Blueprint('order', __name__, url_prefix='/orders')

# Schemas
checkout_schema = CheckoutSchema()
status_schema = OrderStatusUpdateSchema()
response_schema = OrderResponseSchema()
list_response_schema = OrderResponseSchema(many=True)

# =========================================================================
# ORDER MODULE (BLUEPRINT: order_bp | PREFIX: /orders)
# =========================================================================

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
        description: Bad request (Cart is empty or validation error)
      401:
        description: Unauthorized (Invalid or missing token)
      404:
        description: Cart not found
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    validated_data = checkout_schema.load(data)    
    user_id = int(get_jwt_identity())

    orders, error = order_service.checkout(user_id, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({
        "message": "Checkout successful!", 
        "orders_created": len(orders),
        "orders": list_response_schema.dump(orders)
    }), 201


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
        enum: [pending, processing, shipped, delivered, cancelled]
      - in: query
        name: product
        type: string
        description: Search orders containing a product whose name matches this keyword
      - in: query
        name: sort
        type: string
        enum: [asc, desc]
        default: desc
        description: Sort orders by creation date
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: limit
        type: integer
        default: 10
    responses:
      200:
        description: List of user's orders
      400:
        description: Invalid 'sort' value
      401:
        description: Unauthorized (Invalid or missing token)
      500:
        description: Internal server error
    """
    user_id = int(get_jwt_identity())
    status_filter = request.args.get('status', type=str)
    product_search = request.args.get('product', type=str)
    sort = request.args.get('sort', 'desc', type=str).lower()
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    if sort not in ('asc', 'desc'):
        return jsonify({"error": "Invalid 'sort' value. Must be 'asc' or 'desc'."}), 400

    paginated_orders = order_service.get_my_orders(user_id, status_filter, product_search, sort, page, limit)
        
    return jsonify({
        "message": "Orders retrieved successfully",
        "orders": list_response_schema.dump(paginated_orders.items),
        "meta": {
            "current_page": paginated_orders.page,
            "total_pages": paginated_orders.pages,
            "total_items": paginated_orders.total,
            "items_per_page": paginated_orders.per_page,
            "has_next": paginated_orders.has_next, 
            "has_prev": paginated_orders.has_prev
        }
    }), 200
    

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
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Not the buyer or seller)
      404:
        description: Order not found
      500:
        description: Internal server error
    """
    requester_id = int(get_jwt_identity())
    requester_role = get_jwt().get('role')

    order, error = order_service.get_order_details(order_id, requester_id, requester_role)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({
        "message": "Order details retrieved successfully",
        "order": response_schema.dump(order)
    }), 200 


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
              enum: [pending, processing, shipped, delivered, cancelled]
    responses:
      200:
        description: Status successfully updated
      400:
        description: Invalid status transition
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden action
      404:
        description: Order not found
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    validated_data = status_schema.load(data)

    requester_id = int(get_jwt_identity())
    requester_role = get_jwt().get('role')

    order, error = order_service.update_order_status(order_id, requester_id, requester_role, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({
        "message": f"Order status successfully updated to '{order.status}'!",
        "order": response_schema.dump(order)
    }), 200


@order_bp.route('/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    """Permanently delete a cancelled order
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
        description: Order permanently deleted
      400:
        description: Order is not cancelled (immutable constraint)
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Not the buyer, seller, or admin)
      404:
        description: Order not found
      500:
        description: Internal server error
    """
    requester_id = int(get_jwt_identity())
    requester_role = get_jwt().get('role')

    _, error = order_service.delete_order(order_id, requester_id, requester_role)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({"message": f"Order {order_id} has been permanently deleted."}), 200
