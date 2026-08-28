"""User schemas — registration request DTO and response DTO."""
from marshmallow import Schema, fields, validate


class UserRegisterSchema(Schema):
    """DTO for registering a new user."""
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    full_name = fields.Str(required=True, validate=validate.Length(min=3))
    avatar_url = fields.Str(load_default=None, allow_none=True)


class UserResponseSchema(Schema):
    """DTO for serializing a user in API responses."""
    id = fields.Int(dump_only=True)
    email = fields.Str()
    full_name = fields.Str()
    role = fields.Str()
    avatar_url = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")
