from app import create_app
from app.utils import db
from app.models import Users, Sellers, Categories, Products, Orders, OrderItems, Carts, cart_items
from app.services.product_service import generate_unique_slug
from sqlalchemy.exc import IntegrityError
from sqlalchemy import insert

app = create_app()

def run_seeder():
    with app.app_context():
        print("=== STARTING UNIFIED DATABASE SEEDING PROCESS ===")

        try:
            # 1. SEED CATEGORIES (Business & Locust)
            cat_data = [
                {"name": "Electrical & Panels", "desc": "Electrical components, cables, and panel boxes."},
                {"name": "Food & Beverages", "desc": "Snacks, chocolates, and light culinary items."},
                {"name": "Load Test Category", "desc": "Dedicated category for Locust performance testing."}
            ]
            cats = {}
            for cd in cat_data:
                cat = Categories.query.filter_by(name=cd["name"]).first()
                if not cat:
                    cat = Categories(name=cd["name"], description=cd["desc"])
                    db.session.add(cat)
                    db.session.flush()
                cats[cd["name"]] = cat
            print("[1/6] Categories successfully mapped.")

            # 2. SEED USERS (Business & Locust)
            users_data = [
                {"email": "admin@revoshop.com", "name": "System Admin", "role": "admin"},
                {"email": "faujian@angkasa.com", "name": "Muhammad Faujian", "role": "user"},
                {"email": "mesya@mianis.com", "name": "Mesya", "role": "user"},
                {"email": "hendrik@gmail.com", "name": "Hendrik Setiawan", "role": "user"},
                {"email": "eko@gmail.com", "name": "Eko Rusdiyanto", "role": "user"},
                {"email": "buyer@test.com", "name": "Locust Buyer", "role": "user"},
                {"email": "seller_locust@test.com", "name": "Locust Seller", "role": "user"}
            ]
            
            user_objs = {}
            for ud in users_data:
                u = Users.query.filter_by(email=ud["email"]).first()
                if not u:
                    u = Users(email=ud["email"], full_name=ud["name"], role=ud["role"])
                    u.set_password("password123")
                    db.session.add(u)
                    db.session.flush()
                user_objs[ud["email"]] = u
            print("[2/6] User accounts successfully created.")

            # 3. SEED SELLERS
            sellers_config = [
                (user_objs["faujian@angkasa.com"].id, "PT Angkasa Panelindo Elektrik", "Specialist in panel assembly and electrical component distribution.", "https://dummyimage.com/200x200/000/fff&text=Angkasa+Panel"),
                (user_objs["mesya@mianis.com"].id, "Mianis Cubes", "Production of premium homemade chocolate snacks.", "https://dummyimage.com/200x200/000/fff&text=Mianis+Cubes"),
                (user_objs["seller_locust@test.com"].id, "Locust Mega Store", "High volume store for load testing.", "https://dummyimage.com/200x200/000/fff&text=Locust")
            ]

            seller_objs = {}
            for uid, name, desc, avatar in sellers_config:
                seller = db.session.get(Sellers, uid)
                if not seller:
                    seller = Sellers(id=uid, store_name=name, store_description=desc, avatar_url=avatar)
                    db.session.add(seller)
                    db.session.flush()
                seller_objs[name] = seller
            print("[3/6] Store profiles successfully configured.")

            # 4. SEED PRODUCTS
            products_data = [
                # Angkasa Panel Products
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Electrical & Panels", "name": "MCB 10 Ampere Schneider", "price": 55000.00, "stock": 100, "img": "https://dummyimage.com/400x400/ccc/000&text=MCB+10A"},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Electrical & Panels", "name": "Supreme NYM Cable 3x2.5mm", "price": 450000.00, "stock": 50, "img": "https://dummyimage.com/400x400/ccc/000&text=NYM+Cable"},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Electrical & Panels", "name": "Topindo Panel Box 30x40x15", "price": 150000.00, "stock": 25, "img": "https://dummyimage.com/400x400/ccc/000&text=Panel+Box"},
                # Mianis Cubes Products
                {"seller": "Mianis Cubes", "cat": "Food & Beverages", "name": "Mianis Chocolate Cubes Original", "price": 35000.00, "stock": 200, "img": "https://dummyimage.com/400x400/5c3a21/fff&text=Choco+Cubes"},
                {"seller": "Mianis Cubes", "cat": "Food & Beverages", "name": "Mianis Matcha Bites", "price": 38000.00, "stock": 150, "img": "https://dummyimage.com/400x400/2d5a27/fff&text=Matcha+Bites"},
                {"seller": "Mianis Cubes", "cat": "Food & Beverages", "name": "Mianis Dark Choco Premium", "price": 42000.00, "stock": 100, "img": "https://dummyimage.com/400x400/1a110b/fff&text=Dark+Choco"},
                # Locust Load Test Product (Massive Stock)
                {"seller": "Locust Mega Store", "cat": "Load Test Category", "name": "Titanium Widget", "price": 5000.00, "stock": 999999, "img": "https://dummyimage.com/400x400/f00/fff&text=Locust+Widget"}
            ]

            prod_objs = {}
            for pd in products_data:
                p = Products.query.filter_by(name=pd["name"]).first()
                if not p:
                    p = Products(
                        category_id=cats[pd["cat"]].id,
                        seller_id=seller_objs[pd["seller"]].id,
                        name=pd["name"],
                        slug=generate_unique_slug(pd["name"]), # Uses Service Layer logic
                        price=pd["price"],
                        stock=pd["stock"],
                        image_url=pd["img"]
                    )
                    db.session.add(p)
                    db.session.flush()
                prod_objs[pd["name"]] = p
            print("[4/6] Product lines and Locust test items successfully inserted.")

            # 5. SEED ORDERS & ORDER ITEMS
            existing_orders = Orders.query.first()
            if not existing_orders:
                orders_to_create = [
                    (user_objs["hendrik@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "delivered", 110000.00, [("MCB 10 Ampere Schneider", 2, 55000.00)]),
                    (user_objs["eko@gmail.com"].id, seller_objs["Mianis Cubes"].id, "shipped", 190000.00, [("Mianis Matcha Bites", 5, 38000.00)]),
                    (user_objs["hendrik@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "pending", 150000.00, [("Topindo Panel Box 30x40x15", 1, 150000.00)]),
                    (user_objs["hendrik@gmail.com"].id, seller_objs["Mianis Cubes"].id, "cancelled", 70000.00, [("Mianis Chocolate Cubes Original", 2, 35000.00)]),
                    (user_objs["eko@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "processing", 450000.00, [("Supreme NYM Cable 3x2.5mm", 1, 450000.00)]),
                ]
                
                for uid, sid, status, total, items in orders_to_create:
                    new_order = Orders(user_id=uid, seller_id=sid, status=status, total_amount=total, shipping_address="Jl. Dummy Address No. 123, Bandung")
                    db.session.add(new_order)
                    db.session.flush()
                    for item_name, qty, price in items:
                        db.session.add(OrderItems(order_id=new_order.id, product_id=prod_objs[item_name].id, quantity=qty, unit_price=price))
                print("[5/6] Order history representing all ENUM statuses successfully seeded.")
            else:
                print("[5/6] Orders already exist, skipping.")

            # 6. SEED ACTIVE CARTS
            cart_eko = Carts.query.filter_by(user_id=user_objs["eko@gmail.com"].id).first()
            if not cart_eko:
                cart_eko = Carts(user_id=user_objs["eko@gmail.com"].id)
                db.session.add(cart_eko)
                db.session.flush()
                
                stmt1 = insert(cart_items).values(cart_id=cart_eko.id, product_id=prod_objs["MCB 10 Ampere Schneider"].id, quantity=5)
                stmt2 = insert(cart_items).values(cart_id=cart_eko.id, product_id=prod_objs["Mianis Dark Choco Premium"].id, quantity=2)
                db.session.execute(stmt1)
                db.session.execute(stmt2)
                print("[6/6] Active cross-store cart successfully prepared.")
            else:
                print("[6/6] Cart already exists, skipping.")

            db.session.commit()
            print("=== SEEDING COMPLETED SUCCESSFULLY ===")

        except IntegrityError as e:
            db.session.rollback()
            print(f"[FAILED] Relational key violation occurred: {e}")
        except Exception as e:
            db.session.rollback()
            print(f"[FAILED] Unexpected error: {e}")

if __name__ == "__main__":
    run_seeder()
