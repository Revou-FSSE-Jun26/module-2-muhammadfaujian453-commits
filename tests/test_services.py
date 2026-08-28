from app.services.product_service import generate_unique_slug
from app.middleware.auth import hash_password, check_password

class TestProductService:
    def test_generate_unique_slug(self):
        """Unit test: Logic correctness for slug generator (Isolated)"""
        name = "Laptop Pro 15-inch! @2026"
        slug = generate_unique_slug(name)
        
        assert "laptop-pro-15-inch-2026-" in slug
        assert len(slug) == len("laptop-pro-15-inch-2026-") + 8
        assert "!" not in slug
        assert "@" not in slug

class TestAuthMiddleware:
    def test_hash_password(self):
        """Unit test: Hashing a password returns a different string"""
        password = "my_secure_password"
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 20

    def test_check_password(self):
        """Unit test: Verifying correct and incorrect passwords against a hash"""
        password = "my_secure_password"
        hashed = hash_password(password)
        
        assert check_password(password, hashed) is True
        assert check_password("wrong_password", hashed) is False
