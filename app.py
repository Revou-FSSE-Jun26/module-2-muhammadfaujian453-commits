from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mfaujian:pou444@localhost/revoshop_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

from models import Users, Sellers, Categories, Products, Orders
from routes import auth_bp, category_bp, seller_bp, product_bp, order_bp

app.register_blueprint(auth_bp)
app.register_blueprint(category_bp)
app.register_blueprint(seller_bp)
app.register_blueprint(product_bp)
app.register_blueprint(order_bp)

# End point routes for checking database connection
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


if __name__ == '__main__':
    app.run(debug=True)
