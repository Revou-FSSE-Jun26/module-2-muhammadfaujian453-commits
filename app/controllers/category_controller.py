from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.middleware.auth import roles_required
from app.schemas import CategoryCreateSchema, CategoryUpdateSchema, CategoryResponseSchema
from app.schemas import ProductResponseSchema
from app.services import category_service

# Blueprint
category_bp = Blueprint('category', __name__, url_prefix='/categories')

# Schemas
create_schema = CategoryCreateSchema()
update_schema = CategoryUpdateSchema()
response_schema = CategoryResponseSchema()
list_response_schema = CategoryResponseSchema(many=True)


# =========================================================================
# CATEGORY MODULE (BLUEPRINT: category_bp | PREFIX: /categories)
# =========================================================================

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
              example: "Electronic"
            description:
              type: string
              example: "Electrical component"
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
    validated_data = create_schema.load(data)
    
    category, error = category_service.create_category(validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]
        
    return jsonify({
        "message": "Category successfully created!",
        "category": response_schema.dump(category)
    }), 201


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
    categories = category_service.get_all_categories()
    return jsonify({
        "message": "Categories successfully retrieved!",
        "categories": list_response_schema.dump(categories)
    }), 200


@category_bp.route('/<int:category_id>', methods=['GET'])
def get_category_by_id(category_id):
    """Get a specific category by ID, including its active products
    ---
    tags:
      - Categories
    parameters:
      - in: path
        name: category_id
        type: integer
        required: true
    responses:
      200:
        description: Category details with its subcategories and active products
      404:
        description: Category not found
      500:
        description: Internal server error
    """
    result, error = category_service.get_category_by_id(category_id)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]

    category_data = response_schema.dump(result["category"])
    category_data["products"] = ProductResponseSchema(many=True).dump(result["products"])

    return jsonify({
        "message": "Category retrieved successfully",
        "category": category_data
    }), 200


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
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Admin role required)
      404:
        description: Category not found
      409:
        description: Category name already exists
      500:
        description: Internal server error
    """
    data = request.get_json(silent=True) or {}
    validated_data = update_schema.load(data)
    
    category, error = category_service.update_category(category_id, validated_data)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]
        
    return jsonify({
        "message": "Category updated successfully!",
        "category": response_schema.dump(category)
    }), 200


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
      401:
        description: Unauthorized (Invalid or missing token)
      403:
        description: Forbidden (Admin role required)
      404:
        description: Category not found
      409:
        description: Cannot delete, category in use
      500:
        description: Internal server error
    """
    deleted_name, error = category_service.delete_category(category_id)
    if error:
        return jsonify({"error": error["message"]}), error["status_code"]
        
    return jsonify({"message": f"Category '{deleted_name}' deleted successfully!"}), 200
