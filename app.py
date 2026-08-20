from flask import Flask, jsonify
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from errors import register_error_handlers
from flasgger import Swagger
from config import Config
from utils import db

def create_app():
    print("Initializing the Flask application...")
    app = Flask(__name__)

    # Load configuration from config.py
    app.config.from_object(Config)

    # Initializing db with application
    db.init_app(app)

    # Setup Flask-Migrate
    migrate = Migrate(app, db)

    # Initializing JWT
    jwt = JWTManager(app)

    # Initializing Swagger
    swagger = Swagger(app)

    # Import models
    from models import Users, Sellers, Categories, Products, Orders

    # Import routes
    from routes.auth_routes import auth_bp, users_bp
    from routes.category_routes import category_bp
    from routes.seller_routes import seller_bp
    # from routes.product_routes import product_bp
    # from routes.order_routes import order_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(seller_bp)
    # app.register_blueprint(product_bp)
    # app.register_blueprint(order_bp)

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

# Application development execution
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
