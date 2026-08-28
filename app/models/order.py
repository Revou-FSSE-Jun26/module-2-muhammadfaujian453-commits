from app.utils import db

# =========================================================================
# MODEL ORDERS
# =========================================================================
class Orders(db.Model):
    __tablename__ = 'orders'

    # Generate Column and it's Criteria
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable = False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable = False)
    status = db.Column(
        db.Enum('pending', 'processing', 'shipped','delivered' ,'cancelled', name='order_logistics_status'),
        nullable = False,
        server_default = "pending"
    )
    total_amount = db.Column(db.Numeric(12, 2), nullable = False)
    shipping_address = db.Column(db.Text, nullable=  False)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Relationship between Table
    buyer = db.relationship('Users', back_populates = 'orders', lazy = 'joined')
    seller = db.relationship('Sellers', backref=db.backref('store_orders', lazy='selectin'), lazy='joined')
    order_items = db.relationship('OrderItems', backref='order', cascade='all, delete-orphan', lazy='selectin')

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

# =========================================================================
# MODEL ORDER ITEMS
# =========================================================================

class OrderItems(db.Model):
    __tablename__ = 'order_items'
    
    # Composite Primary Key
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True)
    
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