def validate_product_data(data, require_all=True):
    """
    Validate product fields from a request body dict
    require_all = True enforces name and price are present (use for POST)
    require_all = False allows partial updates (use for PUT).
    """
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    category_id = data.get('category_id')

    if require_all and name is None:
        return "name is required", 400
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return "name cannot be empty", 300

    if require_all and price is None:
        return "price is required", 400
    if price is not None:
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            return "price must be a number", 400
        if price < 0:
            return "price must be 0 or greater", 422

    if stock is not None:
        if not isinstance(stock, int) or isinstance(stock, bool):
            return "stock must be an integer", 400
        if stock < 0:
            return "stock must be 0 or greater", 422

    if category_id is not None:
        if not isinstance(category_id, int) or isinstance(category_id, bool):
            return "category_id must be an integer", 400

    return None, None