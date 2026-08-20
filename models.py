from datetime import datetime
from utils import db
from auth import hash_password, check_password

# =========================================================================
# ASSOCIATION TABLES (Many-to-Many)
# =========================================================================

# 1. cart_items Table
cart_items = db.Table(
    'cart_items',
    db.Column('cart_id', db.BigInteger, db.ForeignKey('carts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('product_id', db.BigInteger, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1),
    db.CheckConstraint('quantity > 0', name='cart_items_quantity_check')
)

# =========================================================================
# 1. MODEL USER
# =========================================================================
class Users(db.Model):
    __tablename__ = 'users'

    # Generate Column and it's Criteria
    id = db.Column(db.BigInteger, primary_key = True)
    email = db.Column(db.String(255), nullable = False, unique = True)
    password_hash = db.Column(db.String(255), nullable = False)
    full_name = db.Column(db.String(100), nullable = False)
    avatar_url = db.Column(db.String(255), nullable = True)

    # Soft Deletion Flag
    is_active = db.Column(db.Boolean, default = True, nullable = False)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Data Enum for Role Column
    role = db.Column(
        db.Enum('admin', 'user', name='system_role'), 
        nullable = False, 
        server_default = "'user'"
    )

    # Relationship between Table
    seller_profile = db.relationship('Sellers', back_populates = 'user', uselist = False, lazy = 'joined')
    orders = db.relationship('Orders', back_populates = 'buyer', lazy = 'selectin')
    cart = db.relationship('Carts', back_populates = 'user', uselist = False, lazy = 'joined')

    # Function  for Automate Password Plaintext Encyscription 
    def set_password(self, password):
        self.password_hash = hash_password(password)

    # Function for Checking between Login Password and Hash in Database
    def check_password(self, password):
        return check_password(password, self.password_hash)

    # Function for Converting to Dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =========================================================================
# 2. MODEL SELLERS
# =========================================================================
class Sellers(db.Model):
    __tablename__ = 'sellers'

    # Generate Column and it's Criteria
    id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key = True)
    store_name = db.Column(db.String(100), nullable = False, unique = True)
    store_description = db.Column(db.Text)
    avatar_url = db.Column(db.String(255), nullable = True)

    #Soft Deletion Flag
    is_active = db.Column(db.Boolean, default = True, nullable = False)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Relationship between Table
    user = db.relationship('Users', back_populates = 'seller_profile')
    products = db.relationship('Products', back_populates = 'seller', lazy = 'selectin')

    # Function for Converting to Dictionary
    def to_dict(self):
        return {
            "id": self.id,  # id toko ini bernilai sama dengan id user pemiliknya
            "store_name": self.store_name,
            "store_description": self.store_description,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =========================================================================
# 3. MODEL CATEGORIES
# =========================================================================
class Categories(db.Model):
    __tablename__ = 'categories'

    # Generate Column and it's Criteria
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100),nullable = False, unique = True)
    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Relationship between Table
    products = db.relationship('Products', back_populates = 'category', lazy = 'selectin')

    # Function for Converting to Dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =========================================================================
# 4. MODEL PRODUCTS
# =========================================================================
class Products(db.Model):
    __tablename__ = 'products'

    # Generate Column and it's Criteria
    id = db.Column(db.BigInteger, primary_key = True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable = False)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable = False)
    name = db.Column(db.String(255),nullable = False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable = False)
    stock = db.Column(db.Integer, nullable = False, server_default = '0')
    image_url = db.Column(db.String(255), nullable = True)

    #Soft Deletion Flag
    is_active = db.Column(db.Boolean, default = True, nullable = False)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Relationship between Table
    category = db.relationship('Categories', back_populates = 'products', lazy = 'joined')
    seller = db.relationship('Sellers', back_populates = 'products', lazy = 'joined')

    # Constraint for Column
    __table_args__ = (
        db.CheckConstraint('price >= 0', name='products_price_check'),
        db.CheckConstraint('stock >= 0', name='products_stock_check'),
    )

    # Function for Converting to Dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "seller_id": self.seller_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price": float(self.price) if self.price is not None else 0.0,
            "stock": self.stock,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =========================================================================
# 5. MODEL CARTS
# =========================================================================
class Carts(db.Model):
    __tablename__ = 'carts'

    # Generate Column and it's Criteria
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    # Relationship between Table
    user = db.relationship('Users', back_populates = 'cart')
    items = db.relationship('Products', secondary = cart_items, lazy = 'selectin', backref=  db.backref('carts', lazy='selectin'))

    # Function for Converting to Dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

# =========================================================================
# 6. MODEL ORDERS
# =========================================================================
class Orders(db.Model):
    __tablename__ = 'orders'

    # Generate Column and it's Criteria
    id = db.Column(db.BigInteger, primary_key = True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable = False)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable = False)
    status = db.Column(
        db.Enum('pending', 'processing', 'shipped','delivered' ,'canceled', name='order_logistics_status'),
        nullable = False,
        server_default = "'pending'"
    )
    total_amount = db.Column(db.Numeric(12, 2), nullable = False)
    shipping_address = db.Column(db.Text, nullable=  False)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Relationship between Table
    buyer = db.relationship('Users', back_populates = 'orders', lazy = 'joined')
    seller = db.relationship('Sellers', backref=db.backref('store_orders', lazy='selectin'), lazy='joined')

    # Constraint for Column
    __table_args__ = (
        db.CheckConstraint('total_amount >= 0', name='orders_total_amount_check'),
    )

    # Function for Converting to Dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "seller_id": self.seller_id,
            "status": self.status,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "shipping_address": self.shipping_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class OrderItems(db.Model):
    __tablename__ = 'order_items'
    
    # Composite Primary Key
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True)
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)

    # Constraint for Column
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='order_items_quantity_check'),
        db.CheckConstraint('unit_price >= 0', name='order_items_unit_price_check')
    )

    # Relationship between Table
    product = db.relationship('Products', lazy='joined')

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else "Unknown Product",
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.unit_price) * self.quantity
        }