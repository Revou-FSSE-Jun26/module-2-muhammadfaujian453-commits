from app.utils import db

# =========================================================================
# MODEL SELLERS
# =========================================================================
class Sellers(db.Model):
    __tablename__ = 'sellers'

    # Generate Column and it's Criteria
    id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key = True)
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
