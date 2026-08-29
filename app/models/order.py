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
        server_default = "pending",
        index = True
    )
    total_amount = db.Column(db.Numeric(12, 2), nullable = False)
    shipping_address = db.Column(db.Text, nullable=  False)

    created_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), index = True)
    updated_at = db.Column(db.DateTime(timezone=True), server_default = db.func.now(), onupdate = db.func.now())

    # Relationship between Table
    buyer = db.relationship('Users', back_populates = 'orders', lazy = 'joined')
    seller = db.relationship('Sellers', backref=db.backref('store_orders', lazy='selectin'), lazy='joined')
    order_items = db.relationship('OrderItems', backref='order', cascade='all, delete-orphan', lazy='selectin')

    # Constraint for Column
    __table_args__ = (
        db.CheckConstraint('total_amount >= 0', name='orders_total_amount_check'),
    )


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
