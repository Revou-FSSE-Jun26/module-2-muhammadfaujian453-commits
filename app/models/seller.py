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