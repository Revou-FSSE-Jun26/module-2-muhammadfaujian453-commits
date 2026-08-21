from models import Users, Sellers
from utils import db

# =========================================================================
# HELPER
# =========================================================================
def get_auth_token(client, app, email, role="user"):
    """Inject a user and return a JWT Token"""
    with app.app_context():
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(email=email, full_name="Test User", role=role)
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
    res = client.post('/auth/login', json={"email": email, "password": "password123"})
    return res.get_json()["token"]

# =========================================================================
# TEST CASES
# =========================================================================
def test_create_store_success_and_duplicate(client, app):
    """Scenario: Successfully create a store (201), then fail on the second attempt (400)"""
    token = get_auth_token(client, app, "seller1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"store_name": "Alpha Store", "store_description": "Store description"}

    res_1 = client.post('/sellers', json=payload, headers=headers)
    assert res_1.status_code == 201

    res_2 = client.post('/sellers', json={"store_name": "Beta Store"}, headers=headers)
    assert res_2.status_code == 400

def test_create_store_name_conflict(client, app):
    """Scenario: Reject store name that is already taken by another entity (409)"""
    # Create store 1 first
    token1 = get_auth_token(client, app, "seller1@test.com")
    client.post('/sellers', json={"store_name": "Alpha Store"}, headers={"Authorization": f"Bearer {token1}"})

    # Try creating a store with the same name using seller2
    token2 = get_auth_token(client, app, "seller2@test.com")
    res = client.post('/sellers', json={"store_name": "Alpha Store"}, headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 409

def test_get_store_profile(client, app):
    """Scenario: Retrieve public store profile (200)"""
    token = get_auth_token(client, app, "seller1@test.com")
    client.post('/sellers', json={"store_name": "Alpha Store"}, headers={"Authorization": f"Bearer {token}"})

    with app.app_context():
        seller = Sellers.query.filter_by(store_name="Alpha Store").first()
        seller_id = seller.id

    res = client.get(f'/sellers/{seller_id}')
    assert res.status_code == 200
    assert res.get_json()["store"]["store_name"] == "Alpha Store"

def test_update_and_delete_store(client, app):
    """Scenario: Update profile (200) followed by a Soft Delete (200)"""
    token = get_auth_token(client, app, "seller1@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Pre-create store for this isolated test context
    client.post('/sellers', json={"store_name": "Alpha Store"}, headers=headers)

    res_update = client.put('/sellers', json={"store_name": "Alpha Store Updated"}, headers=headers)
    assert res_update.status_code == 200

    res_delete = client.delete('/sellers', headers=headers)
    assert res_delete.status_code == 200

    with app.app_context():
        seller = Sellers.query.filter_by(id=Users.query.filter_by(email="seller1@test.com").first().id).first()
        assert seller.is_active is False