import re

# Helper Function for validate user registration
def validate_user_registration(data):
    errors = {}
    if not data.get('username') or len(str(data.get('username')).strip()) < 3:
        errors['username'] = "Must be at least 3 characters long."
    if not data.get('email') or not re.match(r"[^@]+@[^@]+\.[^@]+", str(data.get('email'))):
        errors['email'] = "Must be a valid email format."
    if not data.get('password') or len(str(data.get('password'))) < 6:
        errors['password'] = "Must be at least 6 characters long."
    return errors

# Helper Function for validate category
def validate_category_data(data, is_update=False):
    errors = {}
    if not is_update and not data.get('name'):
        errors['name'] = "The category 'name' field is required."
    elif 'name' in data and (not isinstance(data.get('name'), str) or not str(data.get('name')).strip()):
        errors['name'] = "Must be a non-empty string."
    return errors

# Helper Function for validate store
def validate_store_data(data, is_update=False):
    errors = {}
    if not is_update and not data.get('store_name'):
        errors['store_name'] = "The 'store_name' field is required."
    elif 'store_name' in data and (not isinstance(data.get('store_name'), str) or not str(data.get('store_name')).strip()):
        errors['store_name'] = "Must be a non-empty string."

    if 'store_description' in data and not isinstance(data.get('store_description'), str):
        errors['store_description'] = "Must be a valid string."
    if 'avatar_url' in data and not isinstance(data.get('avatar_url'), str):
        errors['avatar_url'] = "Must be a valid string URL."
    
    return errors

# Helper Function for validate product
def validate_product_data(data, is_update=False):
    """
    Validate product fields from a request body dict
    require_all = True enforces name and price are present (use for POST)
    require_all = False allows partial updates (use for PUT).
    """
    errors = {}

    # Validation for must filled column (For create a new product)
    if not is_update:
        required_fields = ['category_id', 'name', 'price']
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
