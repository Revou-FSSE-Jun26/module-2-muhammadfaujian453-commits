# Multi-Vendor E-Commerce API

## Table of Contents
- [Multi-Vendor E-Commerce API](#multi-vendor-e-commerce-api)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Tech Stack](#tech-stack)
  - [Core Architectural Features](#core-architectural-features)
  - [Architecture](#architecture)
  - [Business Logic \& System Workflows](#business-logic--system-workflows)
    - [1. The Split-Order Architecture](#1-the-split-order-architecture)
    - [2. Cascading Soft-Deletion](#2-cascading-soft-deletion)
    - [3. Product Deletion Guard](#3-product-deletion-guard)
    - [4. Order Deletion Constraint](#4-order-deletion-constraint)
  - [Database Schema](#database-schema)
    - [Entity Relationship Diagram (ERD)](#entity-relationship-diagram-erd)
  - [Automated Testing \& Quality Assurance](#automated-testing--quality-assurance)
  - [Load Testing (Locust)](#load-testing-locust)
  - [Installation \& Initialization](#installation--initialization)
  - [Interactive API Documentation (Swagger)](#interactive-api-documentation-swagger)
    - [1. Authentication \& Users (`/auth`, `/users`)](#1-authentication--users-auth-users)
    - [2. Store Management (`/sellers`)](#2-store-management-sellers)
    - [3. Catalog Management (`/categories`, `/products`)](#3-catalog-management-categories-products)
    - [4. Cart \& Checkout (`/carts`, `/orders`)](#4-cart--checkout-carts-orders)
  - [Postman E2E Workflow \& Security Testing](#postman-e2e-workflow--security-testing)
  - [Future Enhancements](#future-enhancements)

## Overview
This repository contains a robust, scalable backend API designed for a multi-tenant e-commerce platform. Built with Python and Flask, it utilizes a single-database configuration for Flask using PostgreSQL and SQLAlchemy. The architecture enforces strict domain boundaries, separating buyers, sellers, and system administrators, making it a highly structured foundation for complex marketplace operations.

The codebase follows a layered **Model-Controller-Service (MCS)** architecture with a dedicated **Marshmallow DTO (Data Transfer Object)** layer for request validation and response serialization — see [Architecture](#architecture) below for the full breakdown.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| Language | Python 3 |
| Framework | Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy (via Flask-SQLAlchemy) |
| Migrations | Flask-Migrate (Alembic) |
| Validation & Serialization (DTO) | Marshmallow |
| Authentication | Flask-JWT-Extended (JWT Bearer tokens) |
| API Documentation | Flasgger (Swagger UI) |
| Testing | Pytest — class-based test suites, scoped fixtures, SQLite in-memory DB |
| Load Testing | Locust |
| Production Server | Gunicorn |

---

## Core Architectural Features
*   **Split-Order Checkout System:** Intelligently dissects a single user cart into multiple isolated orders based on distinct seller IDs, ensuring accurate logistics and financial segregation.
*   **Role-Based Access Control (RBAC):** Secures endpoints using JWT authentication, strictly restricting data mutation operations based on user roles (Admin, Seller, Buyer).
*   **Resilient Data Management:** Implements comprehensive soft-deletion mechanisms across users, stores, and products to maintain referential integrity without destroying historical transaction data.
*   **Dynamic Data Filtering:** Provides robust product discovery through dynamic querying (price ranges, category IDs, text search) combined with offset pagination.
*   **Automated Slug Generation:** Prevents URL collisions by automatically generating unique, SEO-friendly product slugs embedded with UUIDs.
*   **Layered MCS + DTO Architecture:** Business logic is fully decoupled from HTTP handling via a dedicated Service layer, with Marshmallow schemas enforcing strict request/response contracts at the boundary.
*   **Product Deletion Guard:** Blocks the deletion of any product still tied to an order in `pending`, `processing`, or `shipped` status, protecting in-flight transactions from data integrity issues.

---

## Architecture

This API follows a **Model-Controller-Service (MCS)** pattern, augmented with a **DTO (Data Transfer Object) layer** powered by Marshmallow. Each layer has a single, well-defined responsibility:

```
app/
├── __init__.py          # Application factory (create_app)
├── config.py             # Environment-based configuration
├── utils.py               # Shared Flask extensions (SQLAlchemy instance)
├── models/                # SQLAlchemy ORM models — one file per domain
│   ├── user.py / seller.py / category.py
│   └── product.py / cart.py / order.py
├── schemas/               # Marshmallow DTOs — request validation & response serialization
│   ├── auth_schema.py / user_schema.py / seller_schema.py
│   ├── category_schema.py / product_schema.py
│   └── cart_schema.py / order_schema.py
├── services/               # Business logic — all database operations live here
│   ├── auth_service.py / user_service.py / seller_service.py
│   ├── category_service.py / product_service.py
│   └── cart_service.py / order_service.py
├── controllers/            # Thin route handlers (Flask Blueprints)
│   ├── auth_controller.py / category_controller.py
│   ├── seller_controller.py / product_controller.py
│   └── cart_controller.py / order_controller.py
└── middleware/             # Cross-cutting concerns
    ├── auth.py              # Password hashing, role/ownership decorators
    └── errors.py            # Global JSON error handlers
run.py                       # Application entry point
```

**Request flow for a typical write operation** (e.g. `POST /products`):

1.  **Controller** receives the HTTP request and extracts the JWT identity.
2.  **Schema** (`ProductCreateSchema`) validates and coerces the incoming JSON — malformed or missing fields are rejected with a `400` before any business logic runs.
3.  **Service** (`product_service.create_product`) executes the actual business rules and database operations, returning either the created record or a structured error — it never touches Flask's `request` or `jsonify` directly.
4.  **Controller** translates the service's result: on success, a response **Schema** (`ProductResponseSchema`) serializes the model into JSON; on failure, the service's error message and status code are returned as-is.

This keeps controllers thin (parsing and delegating only), keeps business logic testable in isolation from HTTP (see `tests/test_services.py`), and centralizes the request/response contract per resource in one place instead of scattering it across manual validation and `to_dict()` methods.

---

## Business Logic & System Workflows

### 1. The Split-Order Architecture
When a buyer places items from multiple different sellers into a single cart and initiates a checkout, the system does not create a monolithic order. Instead, the transaction engine groups the cart items by `seller_id`. It then generates distinct, independent `Order` records for each seller. This allows each seller to update their logistics status independently without interfering with other sellers' fulfillment processes.
> **Visual Proof: Split-Order Execution**
![Postman showing POST/checkout returning multiple created orders in the JSON response](assets/img_readme/splitorder.png)

### 2. Cascading Soft-Deletion
To preserve financial audit trails and prevent `IntegrityError` on foreign keys, records are rarely hard-deleted.
* If a User is deleted, their account is flagged as inactive.
* If that User is also a Seller, the `Sellers` profile is deactivated.
* Subsequently, all `Products` belonging to that seller are automatically pulled from the public catalog via an `is_active=False` flag.
* Previous `Orders` involving these deleted entities remain perfectly intact for bookkeeping.

### 3. Product Deletion Guard
Deleting a product is not a simple flag flip. Before a product can be soft-deleted, the system checks whether it is referenced by any `OrderItems` belonging to an `Order` still in `pending`, `processing`, or `shipped` status. If such a reference exists, the deletion is rejected with a `409 Conflict` — a seller cannot pull a product out from under a customer's in-flight order. Once every order referencing the product reaches a terminal state (`delivered` or `cancelled`), the same request succeeds.

### 4. Order Deletion Constraint
`Orders` are treated as append-mostly financial records, not freely-erasable resources. `DELETE /orders/{id}` only succeeds for orders whose `status` is `cancelled` — any order still `pending`, `processing`, `shipped`, or already `delivered` is rejected, preserving both in-flight transactions and the completed sales history used for reporting.

---

## Database Schema

### Entity Relationship Diagram (ERD)
> **Note:** Below is the visual representation of the database schema.
```mermaid
erDiagram
    USERS ||--o| SELLERS : "has profile (1:1)"
    USERS ||--o{ ORDERS : "places as buyer"
    USERS ||--o| CARTS : "owns"
    SELLERS ||--o{ PRODUCTS : "manages inventory"
    SELLERS ||--o{ ORDERS : "receives as seller"
    CATEGORIES ||--o{ PRODUCTS : "categorizes"
    CARTS ||--o{ CART_ITEMS : "holds"
    PRODUCTS ||--o{ CART_ITEMS : "added to"
    ORDERS ||--o{ ORDER_ITEMS : "contains"
    PRODUCTS ||--o{ ORDER_ITEMS : "purchased as"

    USERS {
        int id PK
        string email
        string role
        boolean is_active
    }
    SELLERS {
        int id PK, FK "References users.id"
        string store_name
        boolean is_active
    }
    PRODUCTS {
        int id PK
        int seller_id FK
        int category_id FK
        string slug
        numeric price
        int stock
    }
    CATEGORIES {
        int id PK
        string name
    }
    ORDERS {
        int id PK
        int user_id FK "Buyer ID"
        int seller_id FK
        string status
    }
    ORDER_ITEMS {
        int order_id PK, FK
        int product_id PK, FK
        int quantity
    }
    CARTS {
        int id PK
        int user_id FK
    }
    CART_ITEMS {
        int cart_id PK, FK
        int product_id PK, FK
        int quantity
    }
```
The database is heavily normalized to ensure data integrity across the marketplace.

| Table Name | Primary Purpose | Key Relationships |
| :--- | :--- | :--- |
| **`users`** | Central identity management and authentication. | 1:1 with `sellers`, 1:1 with `carts`, 1:M with `orders`. |
| **`sellers`** | Store profiles for users who register to sell. | PK is an FK to `users.id`. 1:M with `products`. |
| **`categories`** | Master data for product classification. | 1:M with `products`. |
| **`products`** | Inventory catalog with auto-generated slugs. | Belongs to `categories` and `sellers`. |
| **`carts` & `cart_items`** | Temporary states for pre-checkout items. | M:N association between `users` and `products`. |
| **`orders` & `order_items`**| Transaction records, deletable only once `cancelled` (see [Order Deletion Constraint](#4-order-deletion-constraint)). | Bridges `users` (buyer) and `sellers`. |

---

## Automated Testing & Quality Assurance

This backend is safeguarded by a comprehensive **End-to-End (E2E) Test Suite** built with `pytest`, organized into **class-based test suites** (`TestAuthAPI`, `TestProductAPI`, `TestOrderAPI`, `TestSellerAPI`, `TestCategoryAPI`, `TestCartAPI`) backed by session- and function-scoped fixtures in `conftest.py`. The test architecture utilizes isolated SQLite in-memory databases with per-test rollbacks, ensuring zero data leakage between test executions.

*   **Positive & Negative Testing:** Validates data boundaries (e.g., rejecting negative stock quantities or zero-priced items).
*   **Security Validations:** Actively tests against Horizontal Privilege Escalation (IDOR), ensuring buyers cannot access or modify orders belonging to other accounts.
*   **Anomaly Prevention:** Halts checkout executions involving "Ghost Products" (items soft-deleted by sellers while still resting in a buyer's cart).
*   **Isolated Unit Tests:** `tests/test_services.py` (`TestProductService`, `TestAuthMiddleware`) tests pure business logic — slug generation, password hashing — directly against the service and middleware layers, with no Flask request/response cycle involved.

> **Visual Proof: E2E Test Coverage**
![Pytest terminal showing 100% Passed metrics across 29+ test cases](assets/img_readme/pytestresult.png)

---

## Load Testing (Locust)

Performance under concurrent load is verified with `locustfile.py`, simulating two weighted, realistic traffic scenarios against a running instance of the API:

| User Class | Weight | Behavior |
| :--- | :--- | :--- |
| `BrowsingUser` | 75% of traffic | Fetches the product catalog and views random product detail pages — no authentication required. |
| `BuyingUser` | 25% of traffic | Logs in, browses the catalog, adds a random product to the cart, checks out, and reviews order history. |

To run a load test locally:
```bash
# In one terminal, run the API
flask run

# In another terminal, run Locust against it
locust -f locustfile.py --host=http://localhost:5000
```
Then open [http://localhost:8089](http://localhost:8089) in your browser to configure the number of simulated users and spawn rate, and start the test from the Locust web UI.

> **Visual Proof: Load Test Results**
![Locust statistics table showing request counts, failure rate, and response times](assets/img_readme/statistics_locust.png)
![Locust charts showing requests per second and response time over the test duration](assets/img_readme/charts_locust.png)

---

## Installation & Initialization

1. Clone the repository and navigate to the root directory.
2. Initialize and activate a Python virtual environment.
3. Install the necessary dependencies. For local development and running the test suite (this also installs Pytest and Locust):
```bash
   pip install -r requirements-dev.txt
```
   For a production-only install (no test or load-testing tools), use `pip install -r requirements.txt` instead.
4. Configure your `.env` file (use `.env.example` as a starting point) with the required environment variables:
```env
   DATABASE_URL=postgresql://user:password@localhost:5432/your_db
   JWT_SECRET_KEY=your_secure_secret_key
   FLASK_APP=run.py
```
5. Apply the schema migrations to your PostgreSQL database:
```bash
   flask db upgrade
```
6. Populate the database with a pre-configured testing environment:
```bash
   python seed.py
```
7. Run the development server:
```bash
   flask run
```
   Or, for a production-style run using Gunicorn:
```bash
   gunicorn run:app
```

---

## Interactive API Documentation (Swagger)

This system is thoroughly documented using **Flasgger**.

Once the local development server is running, navigate to the following URL in your browser to access the interactive Swagger UI and test endpoints directly:
👉 **[http://127.0.0.1:5000/apidocs](http://127.0.0.1:5000/apidocs)**

> **Visual Proof: Developer Experience**
![Swagger UI interface showing grouped endpoints](assets/img_readme/swaggerUI.png)

Below is the testing matrix covering all core functionalities.

### 1. Authentication & Users (`/auth`, `/users`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/users` | Register a new user | Validates payload shape via `UserRegisterSchema`; rejects duplicate emails. | [PASS] |
| `POST` | `/auth/login` | Authenticate & get JWT | Validates credentials, reactivates soft-deleted accounts. | [PASS] |
| `GET` | `/users/me` | Get current identity | Successfully extracts data from JWT. | [PASS] |
| `DELETE`| `/users/{id}` | Deactivate account | Triggers cascade soft-delete for sellers and products. | [PASS] |

### 2. Store Management (`/sellers`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/sellers` | Register a store | Restricts 1 store per user, validates duplicate store names. | [PASS] |
| `PUT` | `/sellers` | Update store profile | Ensures only the owner can update. | [PASS] |

### 3. Catalog Management (`/categories`, `/products`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/categories` | Create category | Protected by `@roles_required('admin')`. | [PASS] |
| `GET` | `/products` | List all products | Tests dynamic filters (name, category, min/max price) & pagination. | [PASS] |
| `POST` | `/products` | Add new product | Auto-generates UUID slug, validates stock/price constraints via `ProductCreateSchema`. | [PASS] |
| `PUT` | `/products/{id}` | Update product | Regenerates slug ONLY if the product name is changed. | [PASS] |
| `DELETE`| `/products/{id}` | Delete a product | **Blocked with `409`** if the product is tied to a `pending`, `processing`, or `shipped` order. | [PASS] |

### 4. Cart & Checkout (`/carts`, `/orders`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/carts/items` | Add to cart | Prevents sellers from buying their own products, checks stock. | [PASS] |
| `POST` | `/orders/checkout` | Process transaction | Successfully splits 1 cart into multiple distinct seller orders. | [PASS] |
| `GET` | `/orders` | Get user orders | Properly filters order history by `?status=pending/shipped`. | [PASS] |
| `PUT` | `/orders/{id}/status`| Update logistics | Admins can update anything. Sellers manage shipping. Buyers can only cancel. | [PASS] |
| `DELETE`| `/orders/{id}` | Delete an order record | Only succeeds when order status is `cancelled`; otherwise rejected. | [PASS] |

---

## Postman E2E Workflow & Security Testing

While Swagger UI provides excellent endpoint-level interaction, the complete business lifecycles and security edge cases (Negative Testing) are documented and tested using Postman. This collection contains a comprehensive suite of API requests divided into 5 core testing modules:

* **1. Auth & Identity:** JWT token generation, role extraction, and automated environment variable scripting for seamless testing.
* **2. Catalog Management:** Dynamic product filtering and seller-restricted CRUD operations.
* **3. Cart & Checkout:** Active prevention of cart exploits (negative quantity injections, out-of-stock bypassing) and the core execution of the **Split-Order Checkout** architecture.
* **4. Order Management:** End-to-end lifecycle tracking, allowing buyers to view order history and sellers to update logistics statuses.
* **5. Security & RBAC:** Active testing against Horizontal Privilege Escalation (IDOR) and role-based status manipulation (e.g., providing `403 Forbidden` proofs when sellers attempt to cancel orders or access other tenants' data).

Click the badge below to access the complete JSON collection. You can import this file directly into your local Postman workspace to replicate the End-to-End testing environment.

[![View Postman Collection](https://img.shields.io/badge/Postman-API%20Docs-orange?logo=postman)](./postman-revoshop.json)

> **Visual Proof: Example of Security & RBAC in Action when a seller tries to change other seller order**
![Postman showing 403 Forbidden](assets/img_readme/403forbidden.png)

---

## Future Enhancements

To further optimize the marketplace ecosystem and elevate the system to enterprise-grade standards, the following features are planned for future iterations:

*   **Advanced Authentication:** Implementing a dual-token `JWT architecture (Access & Refresh Tokens)` with Token Freshness to improve UX and secure sensitive endpoints.
*   **Rate Limiting:** Adding `Flask-Limiter` to protect authentication and transaction endpoints against brute-force attacks.
*   **Direct Checkout API:** Building a decoupled `"Buy Now"` route to bypass the cart state, reducing user friction for single-item purchases.
*   **CI/CD Pipeline:** Automating the `pytest` suite and a Locust smoke test via GitHub Actions on every pull request.

> ✅ Two items previously listed here have since been completed: request/response validation now runs through dedicated **Marshmallow DTO schemas** in a layered MCS architecture (see [Architecture](#architecture)), and database schema evolution is managed via **Flask-Migrate**.