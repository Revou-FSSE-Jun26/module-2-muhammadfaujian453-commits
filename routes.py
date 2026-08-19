from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from utils import db
from models import Users, Sellers, Categories, Products, Orders, order_items
from sqlalchemy.exc import SQLAlchemyError
from auth import roles_required

# -------------------------------------------------------------------------
# BLUEPRINT DEFINITIONS
# -------------------------------------------------------------------------
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
users_bp = Blueprint('users', __name__, url_prefix='/users')
category_bp = Blueprint('category', __name__, url_prefix='/categories')
seller_bp = Blueprint('seller', __name__, url_prefix='/sellers')
product_bp = Blueprint('product', __name__, url_prefix='/products')
order_bp = Blueprint('order', __name__, url_prefix='/orders')

# =========================================================================
# 1. USER MODULE (BLUEPRINT: auth_bp | PREFIX: /auth)
# =========================================================================

# A. New User Registration Route
@auth_bp.route('', methods = ['POST'])
def register_user():
    """ Register a new user based on rubric criteria"""
    data = request.get_json(silent=True) or {}

    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'buyer')

    if not email or not password or not full_name:
        return jsonify({"error": "The email, password, and full_name fields are required!"}), 400

    if role not in ['admin', 'buyer', 'seller']:
        return jsonify({"error": "Invalid role! Options: admin, buyer, seller"}), 400

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered on the system!"}), 400

    try:
        new_user = Users(email=email, full_name=full_name, role=role)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User registration successful",
            "user": new_user.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "An internal database operation failure occurred!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save data: {str(e)}"}), 500


# B. Retrieve Specific User Route
@auth_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_by_id(user_id):
    # Identity extraction from JWT Token
    requester_id = int(get_jwt_identity())
    claims = get_jwt()
    requester_role= claims.get('role')

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found on the system!"}), 404

        if requester_id != user_id and requester_role != 'admin':
            return jsonify({"error": "Unauthorized! You can only view your own profile data unless you are an admin."}), 403
    
        return jsonify({
            "message": "User data successfully retrieved!",
            "user": user.to_dict()
        }), 200
    
    except SQLAlchemyError as e:
        return jsonify({
            "error": "Failed to retrieve data from the database!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# Delete User Account Route
@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    # Identity extraction from JWT Token
    requester_id = int(get_jwt_identity())
    claims = get_jwt()
    requester_role = claims.get('role')

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found on the system!"}), 404

        if requester_id != user_id and requester_role != 'admin':
            return jsonify({"error": "Unauthorized! You can only delete your own account unless you are an admin."}), 403

        any_purchase_history = Orders.query.filter_by(user_id=user_id).first()
        if any_purchase_history:
            return jsonify({
                "error": "Cannot delete account! This user profile is linked to historical purchase order records."
            }), 400

        if user.role == 'seller' and user.seller_profile:
            if user.seller_profile.products:
                return jsonify({
                    "error": "Cannot delete account! Your store still has active products listed. Please delete all products first."
                }), 400

        db.session.delete(user)
        db.session.commit()

        return jsonify({
            "message": f"User with ID {user_id} and its associated store profile have been successfully deleted!"
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while deleting user account!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

# =========================================================================
# 2. AUTH MODULE (BLUEPRINT: auth_bp | PREFIX: /auth)
# =========================================================================

@auth_bp.route('/login', methods=['POST'])
def login():
    """ Login and generate JWT Token"""
    data = request.get_json(silent=True) or ()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": 'Missing email or password'}), 400

    # Retrieve user and verify password
    user = Users.query.filter_by(email=email).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": 'Invalid email or password'}), 401

    # Generate JWT Token carrying the user's ID and Role
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({
        "message": 'Login successful',
        "token": token,
        'user': user.to_dict()
    }), 200


# =========================================================================
# 2. CATEGORY MODULE (BLUEPRINT: category_bp | PREFIX: /categories)
# =========================================================================

# Create New Category Route (Protected: Admin Only)
@category_bp.route('', methods=['POST'])
@role_required(['admin'])
def create_category():
    data = request.get_json(silent=True) or {}
    
    name = data.get('name')
    description = data.get('description')
    
    if not name:
        return jsonify({"error": "The category 'name' field is required!"}), 400
        
    existing_category = Categories.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({"error": f"Category name '{name}' already exists on the system!"}), 400
        
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

# =========================================================================
# 3. SELLER MODULE (BLUEPRINT: seller_bp | PREFIX: /sellers)
# =========================================================================

# Register/Create Store Profile Route
@seller_bp.route('', methods=['POST'])
@role_required(['buyer', 'seller'])
def create_store():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or request.args.get('user_id')
    store_name = data.get('store_name')
    store_description = data.get('store_description')

    if not store_name:
        return jsonify({"error": "The 'store_name' field is required!"}), 400

    existing_store = Sellers.query.get(user_id)
    if existing_store:
        return jsonify({"error": "Your account already has a registered store!"}), 400

    duplicate_name = Sellers.query.filter_by(store_name=store_name).first()
    if duplicate_name:
        return jsonify({"error": f"Store name '{store_name}' is already taken!"}), 400

    try:
        new_store = Sellers(id=user_id, store_name=store_name, store_description=store_description)
        db.session.add(new_store)

        user = Users.query.get(user_id)
        if user and user.role == 'buyer':
            user.role = 'seller'

        db.session.commit()

        return jsonify({
            "message": "Store profile successfully created! Your account role has been upgraded to 'seller'.",
            "store": new_store.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while creating store profile!",
            "details": str(e.__dict__.get('orig', e))
        }), 500

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

# =========================================================================
# 5. ORDER MODULE (BLUEPRINT: order_bp | PREFIX: /orders)
# =========================================================================

# Place a New Order Route
@order_bp.route('', methods=['POST'])
@role_required(['buyer', 'seller'])
def create_order():
    data = request.get_json(silent=True) or {}

    user_id = data.get('user_id') or request.args.get('user_id')
    items_data = data.get('items')

    if not items_data or not isinstance(items_data, list):
        return jsonify({"error": "The 'items' field is required and must be a list of products!"}), 400

    aggregated_cart = {}
    for item in items_data:
        p_id = item.get('product_id')
        raw_qty = item.get('quantity')
        
        if not p_id or raw_qty is None:
            return jsonify({"error": "Each item must include product_id and quantity!"}), 400

        try:
            qty = int(raw_qty)
        except (ValueError, TypeError):
            return jsonify({"error": "Bad Request! Quantity values must be valid integers."}), 400

        if qty <= 0:
            return jsonify({"error": "Quantity must be greater than 0!"}), 400

        if p_id in aggregated_cart:
            aggregated_cart[p_id] += qty
        else:
            aggregated_cart[p_id] = qty


    try:
        total_amount = 0
        order_items_to_create = []

        for p_id, qty in aggregated_cart.items():
            product = Products.query.get(p_id)
            if not product:
                return jsonify({"error": f"Product with ID {p_id} not found!"}), 404

            if product.seller_id == int(user_id):
                return jsonify({"error": f"Violation! You cannot purchase your own product '{product.name}' from your own store."}), 400

            if product.stock < qty:
                return jsonify({"error": f"Insufficient stock for product '{product.name}'! Available stock: {product.stock}"}), 400

            item_price = float(product.price)
            total_amount += item_price * int(qty)

            product.stock -= int(qty)

            order_items_to_create.append({
                "product_id": p_id,
                "quantity": int(qty),
                "unit_price": item_price
            })

        new_order = Orders(user_id=user_id, status='PENDING', total_amount=total_amount)
        db.session.add(new_order)
        db.session.flush()

        for oi in order_items_to_create:
            statement = order_items.insert().values(
                order_id=new_order.id,
                product_id=oi["product_id"],
                quantity=oi["quantity"],
                unit_price=oi["unit_price"]
            )
            db.session.execute(statement)

        db.session.commit()

        return jsonify({
            "message": "Order successfully placed!",
            "order": new_order.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            "error": "Database failure while processing checkout order!",
            "details": str(e.__dict__.get('orig', e))
        }), 500
