"""Cart schemas — add/update item request DTOs and response DTOs."""
from marshmallow import Schema, fields, validate


class CartAddItemSchema(Schema):
    product_id = fields.Int(required=True, strict=True)
    quantity = fields.Int(load_default=1, strict=True, validate=validate.Range(min=1))


class CartUpdateItemSchema(Schema):
    quantity = fields.Int(required=True, strict=True, validate=validate.Range(min=0))


class CartItemResponseSchema(Schema):
    product_id = fields.Int()
    product_name = fields.Str()
    price = fields.Float()
    quantity = fields.Int()
    subtotal = fields.Float()
    image_url = fields.Str(allow_none=True)


class CartResponseSchema(Schema):
    cart_id = fields.Int()
    items = fields.List(fields.Nested(CartItemResponseSchema))
    total_price = fields.Float()