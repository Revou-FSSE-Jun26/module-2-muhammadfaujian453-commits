from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import db
from models import Products, Categories
from auth import seller_required
from validation import validate_product_data
from sqlalchemy.exc import SQLAlchemyError
import re
import uuid

product_bp = Blueprint('product', __name__, url_prefix='/products')

# =========================================================================
# HELPER FUNCTION: SLUG GENERATOR
# =========================================================================
def generate_unique_slug(name):
    """Auto generate unique slug """
    # Delete non-alfanumerik character, change space into slash, and change to lowercase
    base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name).strip().lower()
    base_slug = re.sub(r'[-\s]+', '-', base_slug)
    # Add 8 UUID character
    return f"{base_slug}-{str(uuid.uuid4())[:8]}"

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

    product_name = data.get('name')

    try:
        new_product = Products(
            category_id=category_id,
            seller_id=seller_id,
            name=product_name,
            slug=generate_unique_slug(product_name),
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
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        
    
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
    category_id = request.args.get('category_id', type=int)
    search_name = request.args.get('name', type=str)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    try:
        query = Products.query.filter_by(is_active=True)

        if category_id:
            query = query.filter_by(category_id=category_id)
        if search_name:
            query = query.filter(Products.name.ilike(f"%{search_name}%"))
        if min_price is not None:
            query = query.filter(Products.price >= min_price)
        if max_price is not None:
            query = query.filter(Products.price <= max_price)

        paginated_data = query.paginate(page=page, per_page=limit, error_out=False)

        return jsonify({
            "message": "Products retrieved successfully",
            "data": [product.to_dict() for product in paginated_data.items],
            "meta": {
                "current_page": paginated_data.page,
                "total_pages": paginated_data.pages,
                "total_items": paginated_data.total,
                "items_per_page": paginated_data.per_page,
                "has_next": paginated_data.has_next, 
                "has_prev": paginated_data.has_prev
            }
        }), 200
    
    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

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
    try:
        product = Products.query.filter_by(id=product_id, is_active=True).first()
        if not product:
            return jsonify({"error": "Product not found or is no longer active!"}), 404

        return jsonify({"message": "Product retrieved successfully", "product": product.to_dict()}), 200

    except SQLAlchemyError as e:
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

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
            
        if 'name' in data:
            new_name = data.get('name')
            if new_name != product.name:
                product.name = new_name
                product.slug = generate_unique_slug(new_name)
        if 'description' in data:
            product.description = data.get('description')
        if 'price' in data:
            product.price = data.get('price')
        if 'stock' in data:
            product.stock = data.get('stock')
        if 'image_url' in data:
            product.image_url = data.get('image_url')

        db.session.commit()

        return jsonify({"message": "Product successfully updated!", "product": product.to_dict()}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        

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
      500:
        description: Internal server error
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
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
        