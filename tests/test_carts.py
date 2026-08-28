from app.models import Users, Categories, Products
from app.utils import db

# =========================================================================
# HELPER FUNCTION
# =========================================================================
def setup_cart_prerequisites(client, app):
    """Setup Seller, Buyer, Category, and Product for independent test context"""
    with app.app_context():
        seller = Users(email="cart_seller@test.com", full_name="Seller User", role="user")
        seller.set_password("password123")
        
        buyer = Users(email="cart_buyer@test.com", full_name="Buyer User", role="user")
        buyer.set_password("password123")
        
        db.session.add_all([seller, buyer])
        db.session.commit()
        
        cat = Categories(name="Snacks", description="Delicious snacks")
        db.session.add(cat)
        db.session.commit()

        prod = Products(
            seller_id=seller.id, 
            category_id=cat.id, 
            name="Chocolate Cubes", 
            price=50000, 
            stock=20, 
            slug="chocolate-cubes-sample"
        )
        db.session.add(prod)
        db.session.commit()
        
        seller_id = seller.id
        buyer_id = buyer.id
        prod_id = prod.id

    res_seller = client.post('/auth/login', json={"email": "cart_seller@test.com", "password": "password123"})
    seller_token = res_seller.get_json()["token"]

    res_buyer = client.post('/auth/login', json={"email": "cart_buyer@test.com", "password": "password123"})
    buyer_token = res_buyer.get_json()["token"]

    return seller_token, buyer_token, prod_id

# =========================================================================
# TEST CASES
# =========================================================================
def test_add_own_product_forbidden(client, app):
    """Scenario: Prevent sellers from adding their own products to the cart (403)"""
    seller_token, _, prod_id = setup_cart_prerequisites(client, app)
    
    response = client.post(
        '/carts/items', 
        json={"product_id": prod_id, "quantity": 1}, 
        headers={"Authorization": f"Bearer {seller_token}"}
    )
    
    assert response.status_code == 403
    assert "cannot add your own product" in response.get_json()["error"]

def test_add_item_to_cart_success_and_stock_guard(client, app):
    """Scenario: Successfully add item to cart (200) and enforce stock limit guard (400)"""
    _, buyer_token, prod_id = setup_cart_prerequisites(client, app)
    headers = {"Authorization": f"Bearer {buyer_token}"}

    # 1. Success addition within available stock
    res_success = client.post(
        '/carts/items', 
        json={"product_id": prod_id, "quantity": 5}, 
        headers=headers
    )
    assert res_success.status_code == 200

    # 2. Exceed physical stock limit (Total stock is 20, adding 50 must be rejected)
    res_exceed = client.post(
        '/carts/items', 
        json={"product_id": prod_id, "quantity": 50}, 
        headers=headers
    )
    assert res_exceed.status_code == 400
    assert "Insufficient stock" in res_exceed.get_json()["error"]

def test_view_and_update_cart(client, app):
    """Scenario: Retrieve cart details (200) and update item quantity (200)"""
    _, buyer_token, prod_id = setup_cart_prerequisites(client, app)
    headers = {"Authorization": f"Bearer {buyer_token}"}

    # Seed cart item first
    client.post('/carts/items', json={"product_id": prod_id, "quantity": 2}, headers=headers)

    # 1. View cart
    res_view = client.get('/carts', headers=headers)
    assert res_view.status_code == 200
    data = res_view.get_json()
    assert len(data["items"]) == 1
    assert data["total_price"] == 100000.0 # 50000 * 2

    # 2. Update quantity to 5
    res_update = client.put(f'/carts/items/{prod_id}', json={"quantity": 5}, headers=headers)
    assert res_update.status_code == 200

    # Verify updated calculation
    res_verify = client.get('/carts', headers=headers)
    assert res_verify.get_json()["total_price"] == 250000.0 # 50000 * 5

def test_clear_cart(client, app):
    """Scenario: Empty the entire shopping cart (200)"""
    _, buyer_token, prod_id = setup_cart_prerequisites(client, app)
    headers = {"Authorization": f"Bearer {buyer_token}"}

    # Seed cart item
    client.post('/carts/items', json={"product_id": prod_id, "quantity": 3}, headers=headers)

    # Delete/Clear
    res_clear = client.delete('/carts', headers=headers)
    assert res_clear.status_code == 200

    # Verify empty state
    res_view = client.get('/carts', headers=headers)
    assert len(res_view.get_json()["items"]) == 0
    assert res_view.get_json()["total_price"] == 0

def test_add_invalid_quantity_to_cart(client, app):
    """Scenario: Reject adding zero or negative quantity to cart (400)"""
    _, buyer_token, prod_id = setup_cart_prerequisites(client, app)
    
    res = client.post('/carts/items', json={
        "product_id": prod_id, 
        "quantity": -2 # Invalid quantity
    }, headers={"Authorization": f"Bearer {buyer_token}"})
    
    assert res.status_code == 400