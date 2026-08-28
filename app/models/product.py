from app.utils import db

# =========================================================================
# MODEL PRODUCTS
# =========================================================================
class Products(db.Model):
    __tablename__ = 'products'

    # Generate Column and it's Criteria
    id = db.Column(db.Integer, primary_key = True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable = False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.id', ondelete='RESTRICT'), nullable = False)
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
