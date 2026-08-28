from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.middleware.errors import register_error_handlers
from flasgger import Swagger
from app.config import Config
from app.utils import db
from app.models import Users, Sellers, Categories, Products, Carts, cart_items, Orders, OrderItems
from app.controllers import auth_bp, users_bp, category_bp, seller_bp, product_bp, cart_bp, order_bp

def create_app(test_config=None):
    print("Initializing the Flask application...")
    app = Flask(__name__)
    CORS(app)

    # Load configuration from config.py
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Initializing db with application
    db.init_app(app)
    # Setup Flask-Migrate
    Migrate(app, db)
    # Initializing JWT
    JWTManager(app)
    
    swagger_template = {
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Type 'Bearer' followed by 'space', then input your JWT Token.\n\nExample: 'Bearer eyJhbGci...'"
            }
        }
    }

    # Initializing Swagger
    Swagger(app, template=swagger_template)

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(seller_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(order_bp)

    # Endpoint routes for checking database connection
    @app.route('/health')
    def index():
        try:
            status = "Database Connection Successfull!"
            db.session.execute(db.text('SELECT 1'))
            print("Database Connection Successfull!")

        except SQLAlchemyError as e:
            status = "Database Connection Failed!"
            print(f"Database Connection Failed: {e}")

        except Exception as e:
            status = "Connection Failed!"
            print(f"General Error: {e}")
            
        finally:
            db.session.close()

        return jsonify({"status": status})

    # Initializing Error Handlers
    register_error_handlers(app)

    return app