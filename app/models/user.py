from app.utils import db
from app.middleware.auth import hash_password, check_password

# =========================================================================
# MODEL USER
# =========================================================================
class Users(db.Model):
    __tablename__ = 'users'

    # Generate Column and it's Criteria
    id = db.Column(db.Integer, primary_key = True)
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
        server_default = "user"
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
