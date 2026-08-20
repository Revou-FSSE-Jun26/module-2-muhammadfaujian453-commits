from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import db
from models import Categories
from sqlalchemy.exc import SQLAlchemyError
from auth import roles_required

category_bp = Blueprint('category', __name__, url_prefix='/categories')

# =========================================================================
# CATEGORY MODULE (BLUEPRINT: category_bp | PREFIX: /categories)
# =========================================================================

# A. Create New Category Route (Protected: Admin Only)
@category_bp.route('', methods=['POST'])
@jwt_required()
@roles_required('admin')
def create_category():
    """Create a new category (Protected: Admin Only)
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "Elektronik"
            description:
              type: string
              example: "Komponen panel dan kabel listrik"
    responses:
      201:
        description: Category successfully created
      400:
        description: Validation error or missing name
      401:
        description: Unauthorized (Missing or invalid token)
      403:
        description: Forbidden (Admin role required)
      409:
        description: Category name already exists
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return jsonify({"error": "The category 'name' field is required!"}), 400
        
    existing_category = Categories.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({"error": f"Category name '{name}' already exists on the system!"}), 409
        
    try:
        new_category = Categories(name=name, description=description)
        
        db.session.add(new_category)
        db.session.commit()

        return jsonify({
            "message": "Category successfully created!",
            "category": new_category.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while creating category!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

@category_bp.route('', methods=['GET'])
def get_categories():
    """Retrieve all categories
    ---
    tags:
        - Categories
    responses:
        200:
            description: A list of all categories
        500:
            description: Internal server error
    """
    try:
        categories = Categories.query.all()
        return jsonify({
            "message": "Categories successfully retrieved!",
            "categories": [cat.to_dict() for cat in categories]
        }), 200
    
    except SQLAlchemyError as e:
        return jsonify({"error": "Failed to retrieve categories", "details": str(e.__dict__.get('orig', e))}), 500