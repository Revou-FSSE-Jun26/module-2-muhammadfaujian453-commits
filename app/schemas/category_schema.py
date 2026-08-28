"""Category schemas — create/update request DTOs and response DTO."""
from marshmallow import Schema, fields, validate


class CategoryCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(load_default=None, allow_none=True)


class CategoryUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1))
    description = fields.Str(allow_none=True)


class CategoryResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    description = fields.Str(allow_none=True)
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")