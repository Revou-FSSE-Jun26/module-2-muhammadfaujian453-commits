from app.utils import db


# =========================================================================
# ASSOCIATION TABLES (Many-to-Many)
# =========================================================================

# cart_items Table
cart_items = db.Table(
    'cart_items',
    db.Column('cart_id', db.Integer, db.ForeignKey('carts.id', ondelete='CASCADE'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1),
    db.CheckConstraint('quantity > 0', name='cart_items_quantity_check')
)

# =========================================================================
# MODEL CARTS
# =========================================================================
class Carts(db.Model):
    __tablename__ = 'carts'

    # Generate Column and it's Criteria
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

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