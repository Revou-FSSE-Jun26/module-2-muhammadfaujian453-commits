from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# Konfigurasi Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mfaujian:pou444@localhost/revoshop_db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

db = SQLAlchemy(app)


@app.route('/health')  # Endpoint untuk memeriksa konektivitas database.
def index():
    try:
        # Menjalankan kueri SQL mentah dengan aman menggunakan text()
        status = "Database Connection Successfull!"
        db.session.execute(text('SELECT 1'))
        print("Database Connection Successfull!")
    except SQLAlchemyError as e:
        # Menangkap eror spesifik dari SQLAlchemyv
        status = "Database Connection Failed!"
        print(f"Database Connection Failed: {e}")
    except Exception as e:
        # Menangkap eror umum lainnya
        status = "Connection Failed!"
        print(f"General Error: {e}")
    finally:
        # Menutup sesi untuk mengembalikan koneksi ke pool
        db.session.close()

    return jsonify({"status": status})
