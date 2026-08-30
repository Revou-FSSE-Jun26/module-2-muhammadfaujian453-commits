from flask import jsonify
from marshmallow.exceptions import ValidationError

def register_error_handlers(app):
    
    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(error):
        flat_errors = {field: messages[0] for field, messages in error.messages.items()}
        return jsonify({
            "error": "Validation failed",
            "details": flat_errors
        }), 400

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error.description)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "message": str(error.description)}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "Internal Server Error", "message": "Something went wrong on the server."}), 500
