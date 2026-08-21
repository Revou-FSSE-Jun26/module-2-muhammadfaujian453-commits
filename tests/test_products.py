from models import Users, Categories, Sellers, Products
from utils import db

def setup_product_prerequisites(client, app):
    """Prepare Category and Seller Store, then return Token & Category ID"""
    with app.app_context():
        cat = Categories.query.filter_by(name="Tech").first()
        if not cat:
            cat = Categories(name="Tech")
            db.session.add(cat)
            db.session.commit()
        cat_id = cat.id

        user = Users.query.filter_by(email="prod_seller@test.com").first()
        if not user:
            user = Users(email="prod_seller@test.com", full_name="Product Seller", role="user")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            
    res_login = client.post('/auth/login', json={"email": "prod_seller@test.com", "password": "password123"})
    token = res_login.get_json()["token"]

    # Register a store to acquire @seller_required access
    client.post('/sellers', json={"store_name": "Gadget Store"}, headers={"Authorization": f"Bearer {token}"})
    
    return token, cat_id

# =========================================================================
# TEST CASES
# =========================================================================
def test_create_product_success(client, app):
    """Scenario: Successfully create a product and generate a UUID slug (201)"""
    token, cat_id = setup_product_prerequisites(client, app)
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "category_id": cat_id,
        "name": "Laptop Pro",
        "price": 15000000,
        "stock": 10
    }
    
    res = client.post('/products', json=payload, headers=headers)
    assert res.status_code == 201
    assert "laptop-pro" in res.get_json()["product"]["slug"] # Test auto slug generation

def test_create_product_forbidden_non_seller(client, app):
    """Scenario: Regular user attempts to create a product (403)"""
    with app.app_context():
        user = Users(email="buyer@test.com", full_name="Buyer", role="user")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    
    res_login = client.post('/auth/login', json={"email": "buyer@test.com", "password": "password123"})
    token = res_login.get_json()["token"]
    
    res = client.post('/products', json={"category_id": 1, "name": "Fake Product", "price": 10}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403

def test_get_products_with_filters(client, app):
    """Scenario: Test dynamic search filters and price range"""
    token, cat_id = setup_product_prerequisites(client, app)
    client.post('/products', json={
        "category_id": cat_id,
        "name": "Laptop Pro",
        "price": 15000000,
        "stock": 10
    }, headers={"Authorization": f"Bearer {token}"})

    res = client.get('/products?name=Laptop&min_price=10000000&max_price=20000000')
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

def test_update_and_delete_product(client, app):
    """Scenario: Test ownership RBAC during update and delete operations"""
    token, cat_id = setup_product_prerequisites(client, app)
    headers = {"Authorization": f"Bearer {token}"}
    
    client.post('/products', json={
        "category_id": cat_id,
        "name": "Laptop",
        "price": 15000000,
        "stock": 10
    }, headers=headers)

    res_list = client.get('/products?name=Laptop')
    prod_id = res_list.get_json()["data"][0]["id"]

    res_put = client.put(f'/products/{prod_id}', json={"stock": 50}, headers=headers)
    assert res_put.status_code == 200
    assert res_put.get_json()["product"]["stock"] == 50

    res_del = client.delete(f'/products/{prod_id}', headers=headers)
    assert res_del.status_code == 200

def test_create_product_negative_value(client, app):
    """Scenario: Reject product creation with negative price or stock (400)"""
    token, cat_id = setup_product_prerequisites(client, app)
    
    payload = {
        "category_id": cat_id,
        "name": "Minus Product",
        "price": -15000, # Data ilegal
        "stock": -5      # Data ilegal
    }
    
    res = client.post('/products', json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400