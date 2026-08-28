"""Seller schemas — store profile create/update request DTOs and response DTO."""
from marshmallow import Schema, fields, validate


class SellerCreateSchema(Schema):
    store_name = fields.Str(required=True, validate=validate.Length(min=1))
    store_description = fields.Str(load_default=None, allow_none=True)
    avatar_url = fields.Str(load_default=None, allow_none=True)


class SellerUpdateSchema(Schema):
    store_name = fields.Str(validate=validate.Length(min=1))
    store_description = fields.Str(allow_none=True)
    avatar_url = fields.Str(allow_none=True)
    is_active = fields.Bool()


class SellerResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    store_name = fields.Str()
    store_description = fields.Str(allow_none=True)
    avatar_url = fields.Str(allow_none=True)
    is_active = fields.Bool()
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")