from app.utils import db

# =========================================================================
# MODEL CATEGORIES
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
