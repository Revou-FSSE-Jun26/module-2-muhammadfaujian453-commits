def validate_product_data(data, is_update=False):
    """
    Validate product fields from a request body dict
    require_all = True enforces name and price are present (use for POST)
    require_all = False allows partial updates (use for PUT).
    """
    errors = {}

    # Validation for must filled column (For create a new product)
    if not is_update:
        required_fields = ['category', 'name', 'price']
        for field in required_fields:
            if field not in data or data.get(field) is None:
                errors[field] = f"The '{field}' field is strictly required."

    # Validation for data type and data value (For POST and PUT)
    if 'category_id' in data and data.get('category_id') is not None:
        if type(data.get('category_id')) is not int:
            errors['category_id'] = "Must be an integer."

    if 'name' in data and data.get('name') is not None:
        name = data.get('name')
        if not isinstance(name, str) or not str(name).strip():
            errors['name'] = "Must be a non-empty string."
        elif len(str(name)) > 255:
            errors['name'] = "Cannot exceed 255 characters."

    if 'price' in data and data.get('price') is not None:
        try:
            price = float(data.get('price'))
            if price < 0:
                errors['price'] = "Cannot be negative."
        except (ValueError, TypeError):
            errors['price'] = "Must be a valid number."

    if 'stock' in data and data.get('stock') is not None:
        try:
            stock = int(data.get('stock'))
            if stock < 0:
                errors['stock'] = "Cannot be negative."
        except (ValueError, TypeError):
            errors['stock'] = "Must be a valid integer."

    if 'image_url' in data and data.get('image_url') is not None:
        if not isinstance(data.get('image_url'), str):
            errors['image_url'] = "Must be a valid string format."

    return errors
