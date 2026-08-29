import os
import logging
from logging.handlers import TimedRotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.middleware.errors import register_error_handlers
from flasgger import Swagger
from app.config import Config
from app.utils import db, limiter
from app.models import Users, Sellers, Categories, Products, Carts, cart_items, Orders, OrderItems
from app.controllers import auth_bp, users_bp, category_bp, seller_bp, product_bp, cart_bp, order_bp

def setup_logging(app):
    """
    Configure Python's logging system.
    Logs go to TWO places: Console and a rotating file (logs/app.log).
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        'logs/app.log', when='midnight', interval=1, backupCount=7
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def create_app(test_config=None):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    origins = app.config.get('CORS_ORIGINS', '*')
    CORS(app, origins=origins.split(',') if origins != '*' else '*')

    # Initializing logging 
    setup_logging(app)
    logging.info("Initializing the Flask application...")

    # Initializing db 
    db.init_app(app)
    # Initializing Rate Limiter
    limiter.init_app(app)
    # Initializing Flask-Migrate 
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
            logging.info("Database Connection Successfull!")

        except SQLAlchemyError as e:
            status = "Database Connection Failed!"
            logging.error(f"Database Connection Failed: {e}")

        except Exception as e:
            status = "Connection Failed!"
            logging.error(f"General Error: {e}")
            
        finally:
            db.session.close()

        return jsonify({"status": status})

    # Initializing Error Handlers
    register_error_handlers(app)

    return app