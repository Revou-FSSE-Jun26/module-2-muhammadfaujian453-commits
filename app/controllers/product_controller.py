from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.middleware.auth import seller_required
from app.schemas import ProductCreateSchema, ProductUpdateSchema, ProductResponseSchema
from app.services import product_service

# Blueprint
product_bp = Blueprint('product', __name__, url_prefix='/products')

# Schemas
create_schema = ProductCreateSchema()
update_schema = ProductUpdateSchema()
response_schema = ProductResponseSchema()
list_response_schema = ProductResponseSchema(many=True)

# =========================================================================
# PRODUCT MODULE (BLUEPRINT: product_bp | PREFIX: /products)
# =========================================================================

# A. Create New Product Route (Protected: Seller Only with Input Validation)
@product_bp.route('', methods=['POST'])
@jwt_required()
@seller_required()
def create_product():
    """Create a new product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - category_id
            - name
            - price
          properties:
            category_id:
              type: integer
            name:
              type: string
            description:
              type: string
            price:
              type: number
            stock:
              type: integer
            image_url:
              type: string
    responses:
      201:
        description: Product successfully created
      400:
        description: Validation error
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Requires active seller profile)
      404:
        description: Category not found
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    validated_data = create_schema.load(data)
    seller_id = int(get_jwt_identity())

    product, error = product_service.create_product(seller_id, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({
        "message": "Product successfully created!", 
        "product": response_schema.dump(product)
    }), 201
    
# B. Get all product list route
@product_bp.route('', methods=['GET'])
def get_products():
    """Retrieve all active products with pagination and filters
    ---
    tags:
      - Products
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
      - in: query
        name: limit
        type: integer
        default: 10
      - in: query
        name: category_id
        type: integer
      - in: query
        name: name
        type: string
        description: Search product by name
      - in: query
        name: min_price
        type: number
      - in: query
        name: max_price
        type: number
    responses:
      200:
        description: A paginated list of products
      500:
        description: Internal server error
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    filters = {
        'category_id': request.args.get('category_id', type=int),
        'name': request.args.get('name', type=str),
        'min_price': request.args.get('min_price', type=float),
        'max_price': request.args.get('max_price', type=float)
    }

    paginated_data = product_service.get_products(filters, page, limit)

    return jsonify({
        "message": "Products retrieved successfully",
        "data": list_response_schema.dump(paginated_data.items),
        "meta": {
            "current_page": paginated_data.page,
            "total_pages": paginated_data.pages,
            "total_items": paginated_data.total,
            "items_per_page": paginated_data.per_page,
            "has_next": paginated_data.has_next, 
            "has_prev": paginated_data.has_prev
        }
    }), 200       

# C. Get specific product by its ID route
@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """Get a specific product by ID
    ---
    tags:
      - Products
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
    responses:
      200:
        description: Product details
      404:
        description: Product not found or is no longer active
      500:
        description: Internal server error
    """
    product, error = product_service.get_product_by_id(product_id)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({
        "message": "Product retrieved successfully", 
        "product": response_schema.dump(product)
    }), 200        

# D. Update product route
@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
@seller_required()
def update_product(product_id):
    """Update a product (Partial Update)
    ---
    tags:
      - Products
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
          properties:
            category_id:
              type: integer
            name:
              type: string
            description:
              type: string
            price:
              type: number
            stock:
              type: integer
            image_url:
              type: string
    responses:
      200:
        description: Product updated successfully
      400:
        description: Validation error
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Unauthorized user ID or seller profile)
      404:
        description: Product not found or inactive
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    validated_data = update_schema.load(data)
    seller_id = int(get_jwt_identity())

    product, error = product_service.update_product(product_id, seller_id, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({
        "message": "Product successfully updated!", 
        "product": response_schema.dump(product)
    }), 200

# E. Delete product route
@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
@seller_required()
def delete_product(product_id):
    """Soft delete a product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - in: path
        name: product_id
        type: integer
        required: true
    responses:
      200:
        description: Product successfully deactivated
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Unauthorized user ID or seller profile)
      404:
        description: Product not found or already deactivated
      409:
        description: Cannot delete, product in use by active orders
      500:
        description: Internal server error
    """
    seller_id = int(get_jwt_identity())

    product, error = product_service.delete_product(product_id, seller_id)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    return jsonify({"message": f"Product '{product.name}' has been successfully deactivated."}), 200
        