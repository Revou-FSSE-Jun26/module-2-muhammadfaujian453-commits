"""Auth schemas — login request DTO."""
from marshmallow import Schema, fields


class LoginSchema(Schema):
    """DTO for the login request."""
    email = fields.Email(required=True, error_messages={"required": "Email is required."})
    password = fields.Str(required=True, error_messages={"required": "Password is required."})