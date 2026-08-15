# =============================================================================================================
# NOTES: I'M ALREADY MAKING ROUTES FOR "CHECKLIST 3 ASSIGNMENT" BUT I'M MAKING IT IN A COMMENT FORMAT RIGHT NOW
# =============================================================================================================
from flask import Blueprint, request, jsonify
from app import db
from models import Users, Sellers, Categories, Products, Orders, order_items
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

# Blueprint Module
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
category_bp = Blueprint('category', __name__, url_prefix='/categories')
seller_bp = Blueprint('seller', __name__, url_prefix='/sellers')
product_bp = Blueprint('product', __name__, url_prefix='/products')
order_bp = Blueprint('order', __name__, url_prefix='/orders')


# --- AUTHENTICATION AND RETRIEVAL (MODULE USER) - Decorator to check user access rights ---
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            raw_user_id = data.get('user_id') or request.args.get('user_id')

            if not raw_user_id:
                return jsonify({"error": "Access denied. user_id is required!"}), 401

            try:
                user_id = int(raw_user_id)
            except ValueError:
                return jsonify({"error": "Bad Request! 'user_id' must be a valid numeric integer."}), 400

            try:
                # Cari user di database PostgreSQL menggunakan user_id yang sudah steril (pasti integer)
                user = Users.query.get(user_id)
                if not user:
                    return jsonify({"error": "User not found!"}), 404
                    
                if user.role not in allowed_roles:
                    role_format = ", ".join(allowed_roles)
                    return jsonify({"error": f"Access denied. Your account status is '{user.role}'; this route is only for '{role_format}'!"}), 403

            except SQLAlchemyError as e:
                return jsonify({
                    "error": "Database failure during authorization check!",
                    "details": str(e.__dict__.get('orig', e))
                }), 500

            # user = Users.query.get(user_id)
            # if not user:
            #     return jsonify({"error": "User not found!"}), 404

            # if user.role not in allowed_roles:
            #     role_format = ", ".join(allowed_roles)
            #     return jsonify({"error": f"Access denied. Your account status is '{user.role}'; this route is only for '{role_format}'!"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# =========================================================================
# 1. USER MODULE (BLUEPRINT: auth_bp | PREFIX: /auth)
# =========================================================================

# New User Registration Route
@auth_bp.route('/users', methods = ['POST'])
def register_user():
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
    
# # User Login Route
# @auth_bp.route('/login', methods=['POST'])
# def login_user():
#     data = request.get_json(silent=True) or {}

#     email = data.get('email')
#     password = data.get('password')

#     if not email or not password:
#         return jsonify({"error": "The email and password fields are required!"}), 400

#     try:
#         user = Users.query.filter_by(email=email).first()
#         if not user or not user.check_password(password):
#             return jsonify({"error": "Incorrect email or password!"}), 401

#         return jsonify({
#             "message": "Login successful! Welcome back.",
#             "user": user.to_dict()
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "A database connection failure occurred during the login process!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500
        
#     except Exception as e:
#         return jsonify({"error": f"An internal system error occurred: {str(e)}"}), 500

# Retrieve Specific User Data Route (Dynamic Route)
@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@role_required(['buyer', 'seller', 'admin'])
def get_user_by_id(user_id):
    data = request.get_json(silent=True) or {}
    requester_id = data.get('user_id') or request.args.get('user_id')

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found on the system!"}), 404

        if int(requester_id) != user_id:
            requester_user = Users.query.get(requester_id)
            if not requester_user or requester_user.role != 'admin':
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
@role_required(['buyer', 'seller', 'admin'])
def delete_user(user_id):
    data = request.get_json(silent=True) or {}
    requester_id = data.get('user_id') or request.args.get('user_id')

    try:
        user = Users.query.get(user_id)
        if not user:
            return jsonify({"error": f"User with ID {user_id} not found on the system!"}), 404

        if int(requester_id) != user_id:
            requester_user = Users.query.get(requester_id)
            if not requester_user or requester_user.role != 'admin':
                return jsonify({"error": "Unauthorized! You can only delete your own account unless you are an admin."}), 403

        any_purchase_history = Orders.query.filter_by(user_id=user_id).first()
        if any_purchase_history:
            return jsonify({
                "error": "Cannot delete account! This user profile is linked to historical purchase order records. Database restriction applied."
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
# 2. CATEGORY MODULE (BLUEPRINT: category_bp | PREFIX: /categories)
# =========================================================================

# List All Categories Route
# @category_bp.route('', methods=['GET'])
# def list_categories():
#     try:
#         categories = Categories.query.all()
#         return jsonify({
#             "message": "Categories successfully retrieved!",
#             "categories": [category.to_dict() for category in categories]
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch categories from database!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500

# # Get Specific Category with its Products Route (Dynamic Route)
# @category_bp.route('/<int:category_id>', methods=['GET'])
# def get_category_by_id(category_id):
#     try:
#         category = Categories.query.get(category_id)
#         if not category:
#             return jsonify({"error": f"Category with ID {category_id} not found!"}), 404
            
#         category_data = category.to_dict()
#         category_data['products'] = [product.to_dict() for product in category.products]
        
#         return jsonify({
#             "message": "Category and its products successfully retrieved!",
#             "category": category_data
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch category details!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500

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


# # Get Specific Store Profile with its Products (Dynamic Route)
# @seller_bp.route('/<int:seller_id>', methods=['GET'])
# def get_store_by_id(seller_id):
#     try:
#         store = Sellers.query.get(seller_id)
#         if not store:
#             return jsonify({"error": f"Store with ID {seller_id} not found!"}), 404

#         store_data = store.to_dict()
#         store_data['products'] = [product.to_dict() for product in store.products]

#         return jsonify({
#             "message": "Store profile and products successfully retrieved!",
#             "store": store_data
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch store profile details!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500


# # Update Store Profile Route (Protected: Owner Seller Only)
# @seller_bp.route('/<int:seller_id>', methods=['PUT'])
# @role_required(['seller'])
# def update_store(seller_id):
#     data = request.get_json(silent=True) or {}

#     user_id = data.get('user_id') or request.args.get('user_id')

#     if int(user_id) != seller_id:
#         return jsonify({"error": "Unauthorized! You can only update your own store profile."}), 403

#     store = Sellers.query.get(seller_id)
#     if not store:
#         return jsonify({"error": f"Store with ID {seller_id} not found!"}), 404

#     new_store_name = data.get('store_name')
#     new_store_description = data.get('store_description')

#     if not new_store_name:
#         return jsonify({"error": "The 'store_name' field cannot be empty!"}), 400

#     if new_store_name != store.store_name:
#         duplicate_name = Sellers.query.filter_by(store_name=new_store_name).first()
#         if duplicate_name:
#             return jsonify({"error": f"Store name '{new_store_name}' is already taken by another store!"}), 400

#     try:
#         store.store_name = new_store_name
#         store.store_description = new_store_description
#         db.session.commit()

#         return jsonify({
#             "message": "Store profile successfully updated!",
#             "store": store.to_dict()
#         }), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database failure while updating store profile!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500


# # Close/Delete Store Profile Only
# @seller_bp.route('/<int:seller_id>', methods=['DELETE'])
# @role_required(['seller'])
# def delete_store(seller_id):
#     data = request.get_json(silent=True) or {}

#     user_id = data.get('user_id') or request.args.get('user_id')

#     if int(user_id) != seller_id:
#         return jsonify({"error": "Unauthorized! You can only delete your own store profile."}), 403

#     try:
#         store = Sellers.query.get(seller_id)
#         if not store:
#             return jsonify({"error": f"Store with ID {seller_id} not found!"}), 404

#         if store.products:
#             return jsonify({
#                 "error": "Cannot close store! Your store still has active products listed. Please delete all products first."
#             }), 400

#         user = Users.query.get(seller_id)
#         if user:
#             user.role = 'buyer'

#         db.session.delete(store)
#         db.session.commit()

#         return jsonify({
#             "message": "Your store profile has been successfully closed. Your user account role has been reverted back to 'buyer'!"
#         }), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database failure while closing store profile!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500

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
        "name": "Kripik Singkong Balado Premium", 
        "description": "Camilan renyah pedas manis khas Nusantara.",
        "price": 15000.00, 
        "stock": 50, 
        "category_id": 1, 
        "seller_id": 2
    },
    {
        "id": 2, 
        "name": "Basreng Pedas Daun Jeruk", 
        "description": "Bakso goreng kriuk potongan stik aroma daun jeruk segar.",
        "price": 12000.00, 
        "stock": 35, 
        "category_id": 1, 
        "seller_id": 2
    },
    {
        "id": 3, 
        "name": "Kemeja Flanel Casual Unisex", 
        "description": "Kemeja lengan panjang bahan katun premium adem.",
        "price": 135000.00, 
        "stock": 20, 
        "category_id": 3, 
        "seller_id": 3
    },
    {
        "id": 4, 
        "name": "Celana Chino Slimfit Stretch", 
        "description": "Celana panjang bahan melar premium untuk hangout.",
        "price": 150000.00, 
        "stock": 0, 
        "category_id": 4, 
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

# # List All Products Route
# @product_bp.route('', methods=['GET'])
# def list_products():
#     try:
#         products = Products.query.all()
#         return jsonify({
#             "message": "Products successfully retrieved!",
#             "products": [product.to_dict() for product in products]
#         }), 200
    
#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch products catalog!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500


# # Get Specific Product Details Route
# @product_bp.route('/<int:product_id>', methods=['GET'])
# def get_product_by_id(product_id):
#     try:
#         product = Products.query.get(product_id)
#         if not product:
#             return jsonify({"error": f"Product with ID {product_id} not found!"}), 404

#         return jsonify({
#             "message": "Product details successfully retrieved!",
#             "product": product.to_dict()
#         }), 200
    
#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch product details!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500


# # Update Product Route (Protected: Owner Seller Only with Input Validation)
# @product_bp.route('/<int:product_id>', methods=['PUT'])
# @role_required(['seller'])
# def update_product(product_id):
#     data = request.get_json(silent=True) or {}

#     seller_id = data.get('user_id') or request.args.get('user_id')

#     product = Products.query.get(product_id)
#     if not product:
#         return jsonify({"error": f"Product with ID {product_id} not found!"}), 404

#     if product.seller_id != int(seller_id):
#         return jsonify({"error": "Unauthorized! You can only update your own products."}), 403

#     name = data.get('name')
#     description = data.get('description')
#     price_raw = data.get('price')
#     stock_raw = data.get('stock')
#     category_id = data.get('category_id')

#     if not name or price_raw is None or stock_raw is None or category_id is None:
#         return jsonify({"error": "The name, price, stock, and category_id fields are required!"}), 400

#     try:
#         price = float(price_raw)
#         stock = int(stock_raw)
#     except (ValueError, TypeError):
#         return jsonify({
#             "error": "Bad Request! The 'price' field must be a valid numeric decimal and 'stock' must be an integer value."
#         }), 400

#     if price < 0 or stock < 0:
#         return jsonify({"error": "Price and Stock cannot be negative values!"}), 400

#     if category_id != product.category_id:
#         category = Categories.query.get(category_id)
#         if not category:
#             return jsonify({"error": f"Category with ID {category_id} does not exist!"}), 404

#     try:
#         product.name = name
#         product.description = description
#         product.price = price
#         product.stock = stock
#         product.category_id = category_id
        
#         db.session.commit()

#         return jsonify({
#             "message": "Product successfully updated!",
#             "product": product.to_dict()
#         }), 200

    # except SQLAlchemyError as e:
    #     db.session.rollback()
    #     return jsonify({
    #         "error": "Database failure while updating product!",
    #         "details": str(e.__dict__.get('orig', e))
    #     }), 500


# # Delete Product Route
# @product_bp.route('/products/<int:product_id>', methods=['DELETE'])
# @role_required(['seller'])
# def delete_product(product_id):
#     data = request.get_json(silent=True) or {}

#     seller_id = data.get('user_id') or request.args.get('user_id')

#     product = Products.query.get(product_id)
#     if not product:
#         return jsonify({"error": f"Product with ID {product_id} not found!"}), 404

#     if product.seller_id != int(seller_id):
#         return jsonify({"error": "Unauthorized! You can only delete your own products."}), 403

#     active_order_link = db.session.execute(
#         db.select(order_items).where(order_items.c.product_id == product_id)
#     ).first()
    
#     if active_order_link:
#         return jsonify({
#             "error": "Cannot delete product! This item is linked to active or historical order records (Deletion Guard Blocked)."
#         }), 400

#     try:
#         db.session.delete(product)
#         db.session.commit()
#         return jsonify({"message": f"Product with ID {product_id} has been successfully deleted!"}), 200
    
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database failure while deleting product!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500

# # =========================================================================
# # 5. ORDER MODULE (BLUEPRINT: order_bp | PREFIX: /orders)
# # =========================================================================

# # Place a New Order Route
# @order_bp.route('', methods=['POST'])
# @role_required(['buyer', 'seller'])
# def create_order():
#     data = request.get_json(silent=True) or {}

#     user_id = data.get('user_id') or request.args.get('user_id')
#     items_data = data.get('items')

#     if not items_data or not isinstance(items_data, list):
#         return jsonify({"error": "The 'items' field is required and must be a list of products!"}), 400

#     aggregated_cart = {}
#     for item in items_data:
#         p_id = item.get('product_id')
#         raw_qty = item.get('quantity')
        
#         if not p_id or raw_qty is None:
#             return jsonify({"error": "Each item must include product_id and quantity!"}), 400

#         try:
#             qty = int(raw_qty)
#         except (ValueError, TypeError):
#             return jsonify({"error": "Bad Request! Quantity values must be valid integers."}), 400

#         if qty <= 0:
#             return jsonify({"error": "Quantity must be greater than 0!"}), 400

#         if p_id in aggregated_cart:
#             aggregated_cart[p_id] += qty
#         else:
#             aggregated_cart[p_id] = qty


#     try:
#         total_amount = 0
#         order_items_to_create = []

#         for p_id, qty in aggregated_cart.items():
#             product = Products.query.get(p_id)
#             if not product:
#                 return jsonify({"error": f"Product with ID {p_id} not found!"}), 404

#             if product.seller_id == int(user_id):
#                 return jsonify({"error": f"Violation! You cannot purchase your own product '{product.name}' from your own store."}), 400

#             if product.stock < qty:
#                 return jsonify({"error": f"Insufficient stock for product '{product.name}'! Available stock: {product.stock}"}), 400

#             item_price = float(product.price)
#             total_amount += item_price * int(qty)

#             product.stock -= int(qty)

#             order_items_to_create.append({
#                 "product_id": p_id,
#                 "quantity": int(qty),
#                 "unit_price": item_price
#             })

#         new_order = Orders(user_id=user_id, status='PENDING', total_amount=total_amount)
#         db.session.add(new_order)
#         db.session.flush()

#         for oi in order_items_to_create:
#             statement = order_items.insert().values(
#                 order_id=new_order.id,
#                 product_id=oi["product_id"],
#                 quantity=oi["quantity"],
#                 unit_price=oi["unit_price"]
#             )
#             db.session.execute(statement)

#         db.session.commit()

#         return jsonify({
#             "message": "Order successfully placed!",
#             "order": new_order.to_dict()
#         }), 201

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database failure while processing checkout order!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500


# # List All Orders for Current User (Buyer View / Seller Audit)
# @order_bp.route('', methods=['GET'])
# @role_required(['buyer', 'seller', 'admin'])
# def list_orders():
#     data = request.get_json(silent=True) or {}
#     user_id = request.args.get('user_id') or data.get('user_id')

#     if not user_id:
#         return jsonify({"error": "The 'user_id' url parameter is required to view order history!"}), 400

#     try:
#         user = Users.query.get(user_id)
#         if not user:
#             return jsonify({"error": "User not found!"}), 404

#         if user.role == 'buyer':
#             user_orders = Orders.query.filter_by(user_id=user_id).all()
        
#         elif user.role == 'seller':
#             user_orders = Orders.query.join(order_items).join(Products).filter(Products.seller_id == user_id).distinct().all()
#         else:
#             user_orders = Orders.query.all()

#         return jsonify({
#             "message": "Orders history successfully retrieved!",
#             "orders": [order.to_dict() for order in user_orders]
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch orders history!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500


# # View Specific Order Detail with its Order Items (Dynamic Route)
# @order_bp.route('/<int:order_id>', methods=['GET'])
# @role_required(['buyer', 'seller', 'admin'])
# def get_order_by_id(order_id):
#     data = request.get_json(silent=True) or {}
#     requester_id = data.get('user_id') or request.args.get('user_id')

#     try:
#         order = Orders.query.get(order_id)
#         if not order:
#             return jsonify({"error": f"Order with ID {order_id} not found!"}), 404

#         if order.user_id != int(requester_id):
#             requester_user = Users.query.get(requester_id)

#             if requester_user:
#                 if requester_user.role == 'admin':
#                     pass

#             elif requester_user.role == 'seller':
#                     cross_query = db.select(order_items).join(
#                         Products, order_items.c.product_id == Products.id
#                     ).where(
#                         order_items.c.order_id == order_id,
#                         Products.seller_id == int(requester_id)
#                     )
                    
#                     has_item_in_order = db.session.execute(cross_query).first()
                    
#                     if not has_item_in_order:
#                         return jsonify({"error": "Unauthorized! As a seller, you can only view orders containing your store's products."}), 403
                
#             else:
#                 return jsonify({"error": "Unauthorized! You can only view details of your own purchase history records."}), 403

#         else:
#                 return jsonify({"error": "Unauthorized! User profile not found."}), 403

#         order_data = order.to_dict()

#         query_statement = db.select(
#             order_items.c.product_id, 
#             order_items.c.quantity, 
#             order_items.c.unit_price
#         ).where(order_items.c.order_id == order_id)
        
#         result_rows = db.session.execute(query_statement).all()

#         formatted_items = []
#         for row in result_rows:
#             formatted_items.append({
#                 "order_id": order_id,
#                 "product_id": row.product_id,
#                 "quantity": row.quantity,
#                 "unit_price": float(row.unit_price) if row.unit_price is not None else 0.0
#             })

#         order_data['order_items'] = formatted_items

#         return jsonify({
#             "message": "Order details successfully retrieved!",
#             "order": order_data
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({
#             "error": "Failed to fetch order details!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500       


# # Delete / Cancel Order Route
# @order_bp.route('/<int:order_id>', methods=['DELETE'])
# @role_required(['buyer', 'seller', 'admin'])
# def delete_order(order_id):
#     data = request.get_json(silent=True) or {}
#     user_id = request.args.get('user_id') or data.get('user_id')
    
#     if not user_id:
#         return jsonify({"error": "The 'user_id' is required to authorize order deletion!"}), 400

#     try:
#         order = Orders.query.get(order_id)
#         if not order:
#             return jsonify({"error": f"Order with ID {order_id} not found!"}), 404

#         if order.user_id != int(user_id):
#             user_checker = Users.query.get(user_id)
#             if not user_checker or user_checker.role != 'admin':
#                 return jsonify({"error": "Unauthorized! You can only delete or cancel your own orders."}), 403

#         if order.status != 'PENDING':
#             return jsonify({
#                 "error": f"Action blocked! Cannot delete or cancel an order that is already '{order.status}'. Only 'PENDING' orders can be removed."
#             }), 400

#         query_statement = db.select(order_items.c.product_id, order_items.c.quantity).where(order_items.c.order_id == order_id)
#         result_rows = db.session.execute(query_statement).all()

#         for row in result_rows:
#             product = Products.query.get(row.product_id)
#             if product:
#                 product.stock += row.quantity

#         db.session.delete(order)
#         db.session.commit()

#         return jsonify({
#             "message": f"Order with ID {order_id} was in 'PENDING' status and has been successfully canceled and deleted from the system."
#         }), 200

#     except SQLAlchemyError as e:
#         db.session.rollback()
#         return jsonify({
#             "error": "Database failure while deleting order!",
#             "details": str(e.__dict__.get('orig', e))
#         }), 500

