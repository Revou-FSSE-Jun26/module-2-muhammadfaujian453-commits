from datetime import datetime
from app import db

# Model User
class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.BigInteger, primary_key = True)
    email = db.Column(db.String(255), nullable = False, unique = True)
    password_hash = db.Column(db.String(255), nullable = False)
    full_name = db.Column(db.String(100), nullable = False)
    created_at = db.Column(db.DateTime(timezone=True), default = datetime.utcnow)

    role = db.Column(
        db.Enum('admin', 'buyer', 'seller', name='user_role'), 
        nullable=False, 
        default='buyer'
    )

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Model Sellers
class Sellers(db.Model):
    __tablename__ = 'sellers'

    id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key = True)
    store_name = db.Column(db.String(100), nullable = False, unique = True)
    store_description = db.Column(db.String(999))
    created_at = db.Column(db.DateTime(timezone=True), default = datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,  # id toko ini bernilai sama dengan id user pemiliknya
            "store_name": self.store_name,
            "store_description": self.store_description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Model Categories
class Categories(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100),nullable = False, unique = True)
    description = db.Column(db.String(999))
    created_at = db.Column(db.DateTime(timezone=True), default = datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Model Products
class Products(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.BigInteger, primary_key = True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable = False)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable = False)
    name = db.Column(db.String(255),nullable = False)
    description = db.Column(db.String(999))
    price = db.Column(db.Numeric(12, 2), nullable = False)
    stock = db.Column(db.Integer, nullable = False, default = 0)
    created_at = db.Column(db.DateTime(timezone=True), default = datetime.utcnow)

    # Constraint
    __table_args__ = (
        db.CheckConstraint('price >= 0', name='products_price_check'),
        db.CheckConstraint('stock >= 0', name='products_stock_check'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "seller_id": self.seller_id,
            "description": self.description,
            "price": float(self.price) if self.price is not None else 0.0,
            "stock": self.stock,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Model Orders
class Orders(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.BigInteger, primary_key = True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable = False)
    status = db.Column(db.Enum('PENDING', 'PAID', 'SHIPPED', 'CANCELED', name='order_status'), nullable = False, default = 'PENDING')
    total_amount = db.Column(db.Numeric(12, 2), nullable = False)
    created_at = db.Column(db.DateTime(timezone=True), default = datetime.utcnow)

    # Constraint
    __table_args__ = (
        db.CheckConstraint('total_amount >= 0', name='orders_total_amount_check'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# Model Order_Items
class Order_Items(db.Model):
    __tablename__ = 'order_items'

    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key = True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key = True)
    quantity = db.Column(db.Integer, nullable = False)
    unit_price = db.Column(db.Numeric(12, 2), nullable = False)

    # Constraint
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='order_items_quantity_check'),
        db.CheckConstraint('unit_price >= 0', name='order_items_unit_price_check'),
    )

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0
        }