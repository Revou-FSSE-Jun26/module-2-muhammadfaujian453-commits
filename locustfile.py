"""
Locust load-testing file adapted for the MCS Architecture.
Run with: locust -f locustfile.py --host=http://localhost:5000
"""
import random
from locust import HttpUser, task, between

class BrowsingUser(HttpUser):
    """Scenario 1: Casual visitor browsing products."""
    weight = 3  # 75% of traffic
    wait_time = between(1, 3)

    def on_start(self):
        """Fetch available products dynamically to avoid 404s."""
        self.product_ids = []
        res = self.client.get("/products")
        if res.status_code == 200:
            data = res.json().get("data", [])
            self.product_ids = [p["id"] for p in data]

    @task(3)
    def browse_all_products(self):
        self.client.get("/products")

    @task(1)
    def view_single_product(self):
        if self.product_ids:
            product_id = random.choice(self.product_ids)
            self.client.get(f"/products/{product_id}", name="/products/<id>")


class BuyingUser(HttpUser):
    """Scenario 2: Logged-in buyer checking out the cart."""
    weight = 1  # 25% of traffic
    wait_time = between(2, 5)

    def on_start(self):
        """Login and fetch available products dynamically."""
        response = self.client.post("/auth/login", json={
            "email": "buyer@test.com", 
            "password": "password123"
        })
        if response.status_code == 200:
            self.token = response.json()["token"]
        else:
            self.token = None

        self.product_ids = []
        res = self.client.get("/products")
        if res.status_code == 200:
            data = res.json().get("data", [])
            self.product_ids = [p["id"] for p in data]

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(2)
    def browse_and_view(self):
        self.client.get("/products")

    @task(1)
    def add_to_cart_and_checkout(self):
        if not self.token or not self.product_ids:
            return

        product_id = random.choice(self.product_ids)
        
        with self.client.post("/carts/items", json={"product_id": product_id, "quantity": 1}, 
                              headers=self.auth_headers(), name="/carts/items", catch_response=True) as res:
            if res.status_code == 400:
                res.success()
                return

        with self.client.post("/orders/checkout", json={"shipping_address": "Simulated Load Test Address"}, 
                              headers=self.auth_headers(), name="/orders/checkout", catch_response=True) as res:
            if res.status_code == 400:
                res.success()

    @task(1)
    def check_order_history(self):
        if not self.token:
            return
        self.client.get("/orders", headers=self.auth_headers())
