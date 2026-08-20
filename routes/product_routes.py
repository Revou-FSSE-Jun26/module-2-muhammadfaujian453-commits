from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import db
from models import Products, Categories
from auth import seller_required
from validation import validate_product_data
from sqlalchemy.exc import SQLAlchemyError

product_bp = Blueprint('product', __name__, url_prefix='/products')

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
      403:
        description: Forbidden (Requires active seller profile)
      404:
        description: Category not found
    """
    data = request.get_json(silent=True) or {}
    seller_id = int(get_jwt_identity())

    # Structural Validation
    validation_errors = validate_product_data(data, is_update=False)
    if validation_errors:
        return jsonify({
            "error": "Validation failed",
            "details": validation_errors
        }), 400

    # Business Logic Validation
    category_id = data.get('category_id')
    category = Categories.query.get(category_id)
    if not category:
        return jsonify({"error": f"Category with ID {category_id} not found!"}), 404

    try:
        new_product = Products(
            category_id=category_id,
            seller_id=seller_id,
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            stock=data.get('stock', 0),
            image_url=data.get('image_url')
        )
        db.session.add(new_product)
        db.session.commit()

        return jsonify({"message": "Product successfully created!", "product": new_product.to_dict()}), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure",
            "details": str(e.__dict__.get('orig', e))
        }), 500
    
# B. Get all product list route
@product_bp.route('', methods=['GET'])
def get_products():
    """Retrieve all active products with pagination
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
    responses:
      200:
        description: A paginated list of products
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    category_id = request.args.get('category_id', type=int)

    try:
        query = Products.query.filter_by(is_active=True)
        if category_id:
            query = query.filter_by(category_id=category_id)

        paginated_data = query.paginate(page=page, per_page=limit, error_out=False)

        return jsonify({
            "message": "Products retrieved successfully",
            "data": [product.to_dict() for product in paginated_data.items],
            "meta": {
                "current_page": paginated_data.page,
                "total_pages": paginated_data.pages,
                "total_items": paginated_data.total,
                "items_per_page": paginated_data.per_page
            }
        }), 200
    
    except SQLAlchemyError as e:
        return jsonify({
            "error": "Database error",
            "details": str(e.__dict__.get('orig', e))
        }), 500

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
    """
    try:
        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({"error": "Product not found or is no longer active!"}), 404

        return jsonify({"message": "Product retrieved successfully", "product": product.to_dict()}), 200

    except SQLAlchemyError as e:
        return jsonify({"error": "Database error"}), 500

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
    """
    data = request.get_json(silent=True) or {}
    seller_id = int(get_jwt_identity())

    # Structural Validation (is_update=True)
    validation_errors = validate_product_data(data, is_update=True)
    if validation_errors:
        return jsonify({"error": "Validation failed", "details": validation_errors}), 400

    try:
        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({"error": "Product not found or inactive!"}), 404

        if product.seller_id != seller_id:
            return jsonify({"error": "Unauthorized! You do not own this product."}), 403

        if 'category_id' in data:
            if not Categories.query.get(data.get('category_id')):
                return jsonify({"error": f"Category ID {data.get('category_id')} not found!"}), 404
            product.category_id = data.get('category_id')
            
        if 'name' in data: product.name = data.get('name')
        if 'description' in data: product.description = data.get('description')
        if 'price' in data: product.price = data.get('price')
        if 'stock' in data: product.stock = data.get('stock')
        if 'image_url' in data: product.image_url = data.get('image_url')

        db.session.commit()

        return jsonify({"message": "Product successfully updated!", "product": product.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database error",
            "details": str(e.__dict__.get('orig', e))
        }), 500

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
    """
    seller_id = int(get_jwt_identity())

    try:
        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({"error": "Product not found or already deactivated!"}), 404

        if product.seller_id != seller_id:
            return jsonify({"error": "Unauthorized! You can only delete your own products."}), 403

        product.is_active = False
        db.session.commit()

        return jsonify({"message": f"Product '{product.name}' has been successfully deactivated."}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 500