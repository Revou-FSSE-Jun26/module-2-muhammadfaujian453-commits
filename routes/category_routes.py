from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import db
from models import Categories
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from validation import validate_category_data
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
        description: Validation error
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

    validation_errors = validate_category_data(data, is_update=False)
    if validation_errors:
        return jsonify({
            "error": "Validation failed",
            "details": validation_errors
        }), 400

    name = data.get('name')
    description = data.get('description')
        
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
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

# B. Retrieve all categories route
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
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

# C. Update category routes
@category_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
@roles_required('admin')
def update_category(category_id):
    """Update a category (Admin Only)
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - in: path
        name: category_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
    responses:
      200:
        description: Category updated
      400:
        description: Validation failed
      404:
        description: Category not found
      409:
        description: Category name already exists
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}

    validation_errors = validate_category_data(data, is_update=True)
    if validation_errors:
        return jsonify({
            "error": "Validation failed",
            "details": validation_errors
        }), 400
    
    new_name = data.get('name')
    new_description = data.get('description')
    
    try:
        category = Categories.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found!"}), 404

        if 'name' in data:
            new_name = data.get('name')
            if new_name != category.name:
                duplicate_category = Categories.query.filter_by(name=new_name).first()
                if duplicate_category:
                    return jsonify({"error": f"Category name '{new_name}' already exists!"}), 409
                category.name = new_name
            
        if 'description' in data:
            category.description = new_description

        db.session.commit()
        
        return jsonify({
            "message": "Category updated successfully!", 
            "category": category.to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500

# D. Delete category route
@category_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
@roles_required('admin')
def delete_category(category_id):
    """Delete a category (Admin Only)
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    parameters:
      - in: path
        name: category_id
        type: integer
        required: true
    responses:
      200:
        description: Category deleted
      404:
        description: Category not found
      409:
        description: Cannot delete, category in use
      500:
        description: Internal server error
    """
    try:
        category = Categories.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found!"}), 404

        db.session.delete(category)
        db.session.commit()
        
        return jsonify({"message": f"Category '{category.name}' deleted successfully!"}), 200

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Cannot delete this category because there are products currently assigned to it."
        }), 409
    
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB ERROR]: {str(e.__dict__.get('orig', e))}")
        return jsonify({"error": "A database error occurred processing your request."}), 500
