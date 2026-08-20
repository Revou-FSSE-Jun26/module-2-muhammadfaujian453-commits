from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Sellers, Categories, Products, order_items
from auth import roles_required
from validation import validate_product_data
from sqlalchemy.exc import SQLAlchemyError

product_bp = Blueprint('product', __name__, url_prefix='/products')

# =========================================================================
# 4. PRODUCT MODULE (BLUEPRINT: product_bp | PREFIX: /products)
# =========================================================================

# Create New Product Route (Protected: Seller Only with Input Validation)
@product_bp.route('', methods=['POST'])
@role_required(['seller'])
def create_product():
    data = request.get_json(silent=True) or {}

    seller_id = data.get('user_id') or request.args.get('user_id')
    name = data.get('name')
    description = data.get('description')
    price_raw = data.get('price')
    stock_raw = data.get('stock', 0)
    category_id = data.get('category_id')

    if not name or price_raw is None or category_id is None:
        return jsonify({"error": "The name, price, and category_id fields are required!"}), 400

    try:
        price = float(price_raw)
        stock = int(stock_raw)
    except (ValueError, TypeError):
        return jsonify({
            "error": "Bad Request! The 'price' field must be a valid numeric decimal and 'stock' must be an integer value."
        }), 400

    if price < 0 or stock < 0:
        return jsonify({"error": "Price and Stock cannot be negative values!"}), 400

    category = Categories.query.get(category_id)
    if not category:
        return jsonify({"error": f"Category with ID {category_id} does not exist!"}), 404

    store = Sellers.query.get(seller_id)
    if not store:
        return jsonify({"error": "You must create a store profile before listing products!"}), 400

    try:
        new_product = Products(
            category_id=category_id,
            seller_id=seller_id,
            name=name,
            description=description,
            price=price,
            stock=stock
        )
        db.session.add(new_product)
        db.session.commit()

        return jsonify({
            "message": "Product successfully created!",
            "product": new_product.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while creating product!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

HARDCODED_PRODUCTS = [
    {
        "id": 1, 
        "name": "MCB 3 Phase 16A", 
        "description": "Miniature Circuit Breaker untuk proteksi arus lebih",
        "price": 155000.00, 
        "stock": 50, 
        "category_id": 2, 
        "seller_id": 4
    },
    {
        "id": 2, 
        "name": "Box Panel Indoor 40x50x20", 
        "description": "Plat baja tebal 1.2mm dengan powder coating",
        "price": 450000.00, 
        "stock": 15, 
        "category_id": 2, 
        "seller_id": 4
    },
    {
        "id": 4, 
        "name": "Cokelat Almond Premium Bar", 
        "description": "Cokelat hitam 65 persen dengan kacang almond panggang utuh",
        "price": 35000.00, 
        "stock": 100, 
        "category_id": 1, 
        "seller_id": 3
    },
    {
        "id": 5, 
        "name": "Truffle Cokelat Lumer Pack", 
        "description": "Isi 10 pcs truffle dengan taburan bubuk kakao murni",
        "price": 45000.00, 
        "stock": 80, 
        "category_id": 1, 
        "seller_id": 3
    }
]

# Get all product list
@product_bp.route('', methods=['GET'])
def list_products():
    return jsonify({
        "message": "Products catalog successfully retrieved (Hardcoded Data Compliant)!",
        "products": HARDCODED_PRODUCTS
    }), 200

# Get specific product by its ID
@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    # Menyaring list menggunakan generator expression untuk mencari ID produk yang cocok
    product = next((p for p in HARDCODED_PRODUCTS if p["id"] == product_id), None)
    
    # Penanganan Kasus Not-Found (Wajib tercantum di bukti demo lokal)
    if not product:
        return jsonify({"error": f"Product with ID {product_id} not found on the hardcoded catalog!"}), 404

    return jsonify({
        "message": "Product details successfully retrieved (Hardcoded Data Compliant)!",
        "product": product
    }), 200