from app.models import Users
from app.utils import db

# =========================================================================
# HELPER FUNCTION
# =========================================================================
def setup_test_user(app, email, role):
    """Inject a test user directly into the database for RBAC testing"""
    with app.app_context():
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(email=email, full_name=f"Test {role}", role=role)
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

# =========================================================================
# TEST CASES
# =========================================================================
class TestCategoryAPI:
    def test_create_category_no_token(self, client):
        """Scenario 1: Rejected due to missing authentication token (401)"""
        response = client.post('/categories', json={
            "name": "Electronics",
            "description": "Electronic components"
        })
        
        assert response.status_code == 401

    def test_create_category_forbidden(self, client, app):
        """Scenario 2: Rejected because the token belongs to a regular user, not an admin (403)"""
        setup_test_user(app, "user@test.com", "user")
        
        # Obtain regular user token
        res_login = client.post('/auth/login', json={"email": "user@test.com", "password": "password123"})
        token = res_login.get_json()["token"]
        
        # Hit category route with user token
        response = client.post('/categories', json={
            "name": "Mechanical"
        }, headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 403

    def test_create_category_success_and_duplicate(self, client, app):
        """Scenario 3 & 4: Successfully create category (201) then get rejected on duplication (409)"""
        setup_test_user(app, "admin@test.com", "admin")
        
        # Obtain admin token
        res_login = client.post('/auth/login', json={"email": "admin@test.com", "password": "password123"})
        token = res_login.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"name": "Electrical", "description": "Cables and Panels"}
        
        # First attempt: Success
        response_success = client.post('/categories', json=payload, headers=headers)
        assert response_success.status_code == 201
        assert response_success.get_json()["category"]["name"] == "Electrical"

        # Second attempt: Failed due to duplicate name
        response_duplicate = client.post('/categories', json=payload, headers=headers)
        assert response_duplicate.status_code == 409

    def test_get_all_categories(self, client):
        """Scenario 5: Retrieve the full list of categories (200)"""
        response = client.get('/categories')
        data = response.get_json()

        assert response.status_code == 200
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_get_category_by_id(self, client, app):
        """Scenario 6: Retrieve a single category by its ID (200), then a non-existent ID (404)"""
        setup_test_user(app, "admin2@test.com", "admin")
        res_login = client.post('/auth/login', json={"email": "admin2@test.com", "password": "password123"})
        token = res_login.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post('/categories', json={"name": "Furniture"}, headers=headers)
        category_id = create_response.get_json()["category"]["id"]

        response = client.get(f'/categories/{category_id}')
        assert response.status_code == 200
        assert response.get_json()["category"]["name"] == "Furniture"

        response_404 = client.get('/categories/999999')
        assert response_404.status_code == 404