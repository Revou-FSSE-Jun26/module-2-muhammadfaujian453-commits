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
            # SEED CATEGORIES
            cat_data = [
                {"name": "Electrical & Panels", "desc": "Electrical components, cables, and panel boxes.", "parent": None},
                {"name": "Circuit Breakers & MCBs", "desc": "Miniature circuit breakers and protection devices.", "parent": "Electrical & Panels"},
                {"name": "Cables & Wiring", "desc": "Power and control cables for electrical installations.", "parent": "Electrical & Panels"},
                {"name": "Panel Enclosures", "desc": "Distribution boxes and panel housings.", "parent": "Electrical & Panels"},
                {"name": "Food & Beverages", "desc": "Snacks, chocolates, and light culinary items.", "parent": None},
                {"name": "Chocolate & Confectionery", "desc": "Premium chocolate-based snacks and treats.", "parent": "Food & Beverages"},
                {"name": "Office & Stationery", "desc": "Office supplies and business equipment.", "parent": None},
                {"name": "Writing Instruments", "desc": "Pens, pencils, and markers.", "parent": "Office & Stationery"},
                {"name": "Paper & Filing", "desc": "Notebooks, binders, and filing supplies.", "parent": "Office & Stationery"},
                {"name": "Load Test Category", "desc": "Dedicated category for Locust performance testing.", "parent": None},
            ]
            cats = {}
            for cd in cat_data:
                cat = Categories.query.filter_by(name=cd["name"]).first()
                if not cat:
                    parent_id = cats[cd["parent"]].id if cd["parent"] else None
                    cat = Categories(name=cd["name"], description=cd["desc"], parent_id=parent_id)
                    db.session.add(cat)
                    db.session.flush()
                cats[cd["name"]] = cat
            print("[1/6] Categories and subcategories successfully mapped.")

            # SEED USERS
            users_data = [
                {"email": "admin@revoshop.com", "name": "System Admin", "role": "admin"},
                {"email": "faujian@angkasa.com", "name": "Muhammad Faujian", "role": "user"},
                {"email": "mesya@mianis.com", "name": "Mesya", "role": "user"},
                {"email": "dedi@officemart.com", "name": "Dedi Kurniawan", "role": "user"},
                {"email": "hendrik@gmail.com", "name": "Hendrik Setiawan", "role": "user"},
                {"email": "eko@gmail.com", "name": "Eko Rusdiyanto", "role": "user"},
                {"email": "siti.rahma@gmail.com", "name": "Siti Rahmawati", "role": "user"},
                {"email": "budi.santoso@gmail.com", "name": "Budi Santoso", "role": "user"},
                {"email": "dewi.lestari@gmail.com", "name": "Dewi Lestari", "role": "user"},
                {"email": "agus.pratama@gmail.com", "name": "Agus Pratama", "role": "user"},
                {"email": "buyer@test.com", "name": "Locust Buyer", "role": "user"},
                {"email": "seller_locust@test.com", "name": "Locust Seller", "role": "user"},
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

            # SEED SELLERS
            sellers_config = [
                (user_objs["faujian@angkasa.com"].id, "PT Angkasa Panelindo Elektrik", "Specialist in panel assembly and electrical component distribution.", "https://dummyimage.com/200x200/000/fff&text=Angkasa+Panel"),
                (user_objs["mesya@mianis.com"].id, "Mianis Cubes", "Production of premium homemade chocolate snacks.", "https://dummyimage.com/200x200/000/fff&text=Mianis+Cubes"),
                (user_objs["dedi@officemart.com"].id, "OfficeMart Bandung", "Wholesale and retail supplier of office and stationery essentials.", "https://dummyimage.com/200x200/000/fff&text=OfficeMart"),
                (user_objs["seller_locust@test.com"].id, "Locust Mega Store", "High volume store for load testing.", "https://dummyimage.com/200x200/000/fff&text=Locust"),
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

            # SEED PRODUCTS
            products_data = [
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Circuit Breakers & MCBs", "name": "MCB 10 Ampere Schneider", "price": 55000.00, "stock": 100, "img": "https://dummyimage.com/400x400/ccc/000&text=MCB+10A"},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Circuit Breakers & MCBs", "name": "MCB 16 Ampere Mitsubishi", "price": 62000.00, "stock": 80, "img": "https://dummyimage.com/400x400/ccc/000&text=MCB+16A"},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Cables & Wiring", "name": "Supreme NYM Cable 3x2.5mm", "price": 450000.00, "stock": 50, "img": "https://dummyimage.com/400x400/ccc/000&text=NYM+Cable"},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Cables & Wiring", "name": "Eterna NYA Cable 1x1.5mm", "price": 180000.00, "stock": 70, "img": "https://dummyimage.com/400x400/ccc/000&text=NYA+Cable"},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Cables & Wiring", "name": "Legacy PVC Cable 1x1.0mm (Discontinued)", "price": 120000.00, "stock": 0, "img": "https://dummyimage.com/400x400/999/fff&text=Discontinued", "is_active": False},
                {"seller": "PT Angkasa Panelindo Elektrik", "cat": "Panel Enclosures", "name": "Topindo Panel Box 30x40x15", "price": 150000.00, "stock": 25, "img": "https://dummyimage.com/400x400/ccc/000&text=Panel+Box"},

                {"seller": "Mianis Cubes", "cat": "Chocolate & Confectionery", "name": "Mianis Chocolate Cubes Original", "price": 35000.00, "stock": 200, "img": "https://dummyimage.com/400x400/5c3a21/fff&text=Choco+Cubes"},
                {"seller": "Mianis Cubes", "cat": "Chocolate & Confectionery", "name": "Mianis Matcha Bites", "price": 38000.00, "stock": 150, "img": "https://dummyimage.com/400x400/2d5a27/fff&text=Matcha+Bites"},
                {"seller": "Mianis Cubes", "cat": "Chocolate & Confectionery", "name": "Mianis Dark Choco Premium", "price": 42000.00, "stock": 100, "img": "https://dummyimage.com/400x400/1a110b/fff&text=Dark+Choco"},
                {"seller": "Mianis Cubes", "cat": "Chocolate & Confectionery", "name": "Mianis Almond Crunch", "price": 45000.00, "stock": 90, "img": "https://dummyimage.com/400x400/704214/fff&text=Almond+Crunch"},

                {"seller": "OfficeMart Bandung", "cat": "Writing Instruments", "name": "Pilot G2 Gel Pen 0.5mm (Box of 12)", "price": 84000.00, "stock": 60, "img": "https://dummyimage.com/400x400/003366/fff&text=Gel+Pen"},
                {"seller": "OfficeMart Bandung", "cat": "Writing Instruments", "name": "Staedtler Highlighter Set (6 Colors)", "price": 45000.00, "stock": 75, "img": "https://dummyimage.com/400x400/ffcc00/000&text=Highlighter"},
                {"seller": "OfficeMart Bandung", "cat": "Paper & Filing", "name": "Sinar Dunia A4 Paper 80gsm (1 Ream)", "price": 52000.00, "stock": 120, "img": "https://dummyimage.com/400x400/eee/000&text=A4+Paper"},
                {"seller": "OfficeMart Bandung", "cat": "Paper & Filing", "name": "Bantex Ring Binder 2-Inch", "price": 38000.00, "stock": 55, "img": "https://dummyimage.com/400x400/006633/fff&text=Ring+Binder"},

                {"seller": "Locust Mega Store", "cat": "Load Test Category", "name": "Titanium Widget", "price": 5000.00, "stock": 999999, "img": "https://dummyimage.com/400x400/f00/fff&text=Locust+Widget"},
            ]
            prod_objs = {}
            for pd in products_data:
                p = Products.query.filter_by(name=pd["name"]).first()
                if not p:
                    p = Products(
                        category_id=cats[pd["cat"]].id,
                        seller_id=seller_objs[pd["seller"]].id,
                        name=pd["name"],
                        slug=generate_unique_slug(pd["name"]),
                        price=pd["price"],
                        stock=pd["stock"],
                        image_url=pd["img"],
                        is_active=pd.get("is_active", True)
                    )
                    db.session.add(p)
                    db.session.flush()
                prod_objs[pd["name"]] = p
            print("[4/6] Product lines, discontinued item, and Locust test item successfully inserted.")

            # SEED ORDERS & ORDER ITEMS
            existing_orders = Orders.query.first()
            if not existing_orders:
                orders_to_create = [
                    (user_objs["hendrik@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "delivered", 110000.00, "Jl. Braga No. 45, Sumur Bandung, Bandung, Jawa Barat 40111", [("MCB 10 Ampere Schneider", 2, 55000.00)]),
                    (user_objs["siti.rahma@gmail.com"].id, seller_objs["Mianis Cubes"].id, "delivered", 84000.00, "Jl. Diponegoro No. 12, Citarum, Bandung, Jawa Barat 40115", [("Mianis Dark Choco Premium", 2, 42000.00)]),
                    (user_objs["eko@gmail.com"].id, seller_objs["Mianis Cubes"].id, "shipped", 190000.00, "Komplek Riung Bandung Blok C2 No. 8, Bandung, Jawa Barat 40295", [("Mianis Matcha Bites", 5, 38000.00)]),
                    (user_objs["budi.santoso@gmail.com"].id, seller_objs["OfficeMart Bandung"].id, "shipped", 104000.00, "Jl. Setiabudi No. 200, Bandung, Jawa Barat 40154", [("Sinar Dunia A4 Paper 80gsm (1 Ream)", 2, 52000.00)]),
                    (user_objs["hendrik@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "processing", 150000.00, "Jl. Braga No. 45, Sumur Bandung, Bandung, Jawa Barat 40111", [("Topindo Panel Box 30x40x15", 1, 150000.00)]),
                    (user_objs["dewi.lestari@gmail.com"].id, seller_objs["OfficeMart Bandung"].id, "processing", 90000.00, "Perumahan Batununggal Indah II No. 15, Bandung, Jawa Barat 40266", [("Staedtler Highlighter Set (6 Colors)", 2, 45000.00)]),
                    (user_objs["agus.pratama@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "pending", 62000.00, "Jl. Cihampelas No. 88, Bandung, Jawa Barat 40131", [("MCB 16 Ampere Mitsubishi", 1, 62000.00)]),
                    (user_objs["eko@gmail.com"].id, seller_objs["PT Angkasa Panelindo Elektrik"].id, "pending", 450000.00, "Komplek Riung Bandung Blok C2 No. 8, Bandung, Jawa Barat 40295", [("Supreme NYM Cable 3x2.5mm", 1, 450000.00)]),
                    (user_objs["hendrik@gmail.com"].id, seller_objs["Mianis Cubes"].id, "cancelled", 70000.00, "Jl. Braga No. 45, Sumur Bandung, Bandung, Jawa Barat 40111", [("Mianis Chocolate Cubes Original", 2, 35000.00)]),
                    (user_objs["siti.rahma@gmail.com"].id, seller_objs["OfficeMart Bandung"].id, "cancelled", 76000.00, "Jl. Diponegoro No. 12, Citarum, Bandung, Jawa Barat 40115", [("Bantex Ring Binder 2-Inch", 2, 38000.00)]),
                ]
                for uid, sid, status, total, address, items in orders_to_create:
                    new_order = Orders(user_id=uid, seller_id=sid, status=status, total_amount=total, shipping_address=address)
                    db.session.add(new_order)
                    db.session.flush()
                    for item_name, qty, price in items:
                        db.session.add(OrderItems(order_id=new_order.id, product_id=prod_objs[item_name].id, quantity=qty, unit_price=price))
                print("[5/6] Order history covering all lifecycle statuses successfully seeded — note Hendrik and Siti each appear as returning customers across different sellers.")
            else:
                print("[5/6] Orders already exist, skipping.")

            # SEED ACTIVE CARTS
            cart_configs = [
                (user_objs["eko@gmail.com"].id, [("MCB 10 Ampere Schneider", 5), ("Mianis Dark Choco Premium", 2)]),
                (user_objs["dewi.lestari@gmail.com"].id, [("Pilot G2 Gel Pen 0.5mm (Box of 12)", 3)]),
            ]
            for uid, items in cart_configs:
                cart = Carts.query.filter_by(user_id=uid).first()
                if not cart:
                    cart = Carts(user_id=uid)
                    db.session.add(cart)
                    db.session.flush()
                    for item_name, qty in items:
                        db.session.execute(insert(cart_items).values(cart_id=cart.id, product_id=prod_objs[item_name].id, quantity=qty))
            print("[6/6] Active carts successfully prepared.")

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