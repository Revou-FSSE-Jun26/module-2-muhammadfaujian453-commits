def test_register_user_success(client):
    """Registration Test"""
    payload = {
        "email": "testuser@gmail.com",
        "password": "password123",
        "full_name": "Test User",
        "avatar_url": "https://dummyimage.com/avatar"
    }
    
    response = client.post('/users', json=payload)
    data = response.get_json()

    print("\n[DEBUG RESPONSE]:", data)

    assert response.status_code == 201
    assert data["message"] == "User registration successful"
    assert data["user"]["email"] == "testuser@gmail.com"

def test_register_duplicate_email(client):
    """Duplication Test"""
    payload = {
        "email": "duplicate@gmail.com",
        "password": "password123",
        "full_name": "Duplicate User"
    }
    
    client.post('/users', json=payload)
    
    response = client.post('/users', json=payload)
    data = response.get_json()

    assert response.status_code == 409
    assert "error" in data

def test_login_success(client):
    """Login and JWT Token Test"""
    client.post('/users', json={
        "email": "loginuser@gmail.com",
        "password": "password123",
        "full_name": "Login User"
    })
    
    # 2. Coba login
    response = client.post('/auth/login', json={
        "email": "loginuser@gmail.com",
        "password": "password123"
    })
    data = response.get_json()

    assert response.status_code == 200
    assert "token" in data
    assert data["user"]["email"] == "loginuser@gmail.com"