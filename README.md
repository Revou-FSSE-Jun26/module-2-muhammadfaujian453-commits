# Multi-Vendor E-Commerce API

[![Tests](https://github.com/mfaujian/e-commerce-multivendor-api/actions/workflows/tests.yml/badge.svg)](https://github.com/mfaujian/e-commerce-multivendor-api/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Live API](https://img.shields.io/badge/Live%20API-Railway-8A2BE2)](https://<your-app>.up.railway.app/apidocs)

> 🔗 **Live API Documentation:** [https://e-commerce-multivendor-api.up.railway.app/apidocs/](https://e-commerce-multivendor-api.up.railway.app/apidocs/)

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
  - [Infrastructure \& Deployment Readiness](#infrastructure--deployment-readiness)
  - [Containerization (Docker)](#containerization-docker)
  - [Cloud Architecture (Railway)](#cloud-architecture-railway)
    - [Managing the production database (migrations \& seeding)](#managing-the-production-database-migrations--seeding)
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

The codebase follows a layered **Model-Controller-Service (MCS)** architecture with a dedicated **Marshmallow DTO (Data Transfer Object)** layer for request validation and response serialization — see [Architecture](#architecture) below for the full breakdown. Beyond the application code, this project is fully **containerized with Docker** and **live-deployed on Railway** — see [Containerization](#containerization-docker) and [Cloud Architecture](#cloud-architecture-railway).

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
| Rate Limiting | Flask-Limiter |
| API Documentation | Flasgger (Swagger UI) |
| Testing | Pytest — class-based test suites, scoped fixtures, SQLite in-memory DB |
| Load Testing | Locust |
| Production Server | Gunicorn |
| Containerization | Docker |
| Hosting / PaaS | Railway (Web Service + managed PostgreSQL) |
| CI | GitHub Actions |

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
├── utils.py               # Shared Flask extensions (SQLAlchemy instance, Limiter)
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
    └── errors.py            # Global JSON error handlers (incl. Marshmallow ValidationError)
run.py                       # Application entry point
Dockerfile                   # Production container image definition
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
The database is heavily normalized to ensure data integrity across the marketplace. Frequently filtered and sorted columns (`orders.status`, `orders.created_at`, `products.category_id`, `products.seller_id`, `carts.user_id`) are backed by explicit indexes for query performance at scale.

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

This backend is safeguarded by a comprehensive **End-to-End (E2E) Test Suite** built with `pytest`, organized into **class-based test suites** (`TestAuthAPI`, `TestProductAPI`, `TestOrderAPI`, `TestSellerAPI`, `TestCategoryAPI`, `TestCartAPI`) backed by session- and function-scoped fixtures in `conftest.py`. The test architecture utilizes isolated SQLite in-memory databases with per-test rollbacks, ensuring zero data leakage between test executions. Every push and pull request against `main` automatically triggers this full suite via **GitHub Actions**.

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

## Infrastructure & Deployment Readiness

Beyond passing its own test suite, this API includes several production-hardening measures that only become relevant once real traffic and real hosting are involved:

*   **Structured, Platform-Aware Logging:** Uses Python's `logging` module (not `print()`) with a console handler that integrates with any hosting platform's log dashboard. File-based rotating logs are only enabled when `IS_PRODUCTION` is unset — this avoids writing to disk on platforms with an ephemeral filesystem (like Railway), where local log files are wiped on every redeploy.
*   **Database Connection Resilience:** `SQLALCHEMY_ENGINE_OPTIONS` is configured with `pool_pre_ping=True` and a `pool_recycle` interval, preventing the common "server closed the connection unexpectedly" failure that occurs when a managed Postgres provider silently drops idle connections.
*   **Rate Limiting:** `Flask-Limiter` protects `POST /auth/login` (5/minute) and `POST /users` (10/hour) against brute-force and registration-spam attacks.
    > ⚠️ **Known limitation:** the current rate limiter uses in-memory storage, which is *not* shared across Gunicorn's multiple worker processes — under `--workers 2`, the effective limit is roughly double the configured value, since each worker tracks its own counters independently. A Redis-backed store closes this gap; see [Future Enhancements](#future-enhancements).
*   **Environment-Aware CORS:** Allowed origins are controlled via the `CORS_ORIGINS` environment variable rather than hardcoded, so the same codebase can run wide-open in development and locked-down in production.
*   **Fail-Fast Configuration:** The app refuses to start if `DATABASE_URL` or `JWT_SECRET_KEY` are missing, rather than silently falling back to an insecure default.
*   **Database Scheme Normalization:** `config.py` automatically rewrites a legacy `postgres://` connection string (as issued by some hosting providers, including Railway) into the `postgresql://` scheme SQLAlchemy 1.4+ requires — without this, the app would crash on startup on those providers.
*   **Continuous Integration:** Every push and pull request runs the full `pytest` suite via GitHub Actions (`.github/workflows/tests.yml`), catching regressions before they reach `main`.

---

## Containerization (Docker)

The application is fully containerized — the same `Dockerfile` in this repository is what builds the image actually running in production (see [Cloud Architecture](#cloud-architecture-railway)), not a separate demo file.

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn run:app --bind 0.0.0.0:$PORT --workers 2"]
```

A few deliberate choices worth calling out:
*   **Non-root user (`appuser`):** the app never runs as root inside the container, following the Principle of Least Privilege — if the application layer is ever compromised, the blast radius is limited to an unprivileged user.
*   **`exec` in the CMD:** ensures Gunicorn runs as PID 1 and receives shutdown signals (`SIGTERM`) directly, enabling graceful shutdowns instead of an abrupt kill.
*   **`$PORT` binding:** the container binds to whatever port the hosting platform injects at runtime rather than a hardcoded value — required by Railway, Render, and most modern PaaS providers.

**Run it locally:**
```bash
docker build -t multivendor-api .

docker run -p 8000:8000 \
  -e DATABASE_URL="your-database-url" \
  -e JWT_SECRET_KEY="your-secret-key" \
  -e PORT=8000 \
  multivendor-api
```
Then visit `http://localhost:8000/health`.

> **Visual Proof: Container Running Locally**
![Docker Desktop showing the multivendor-api container running with its port mapping and status](assets/img_readme/docker-desktop-container.png)

---

## Cloud Architecture (Railway)

This API is deployed on **Railway**, a container-native PaaS. A single Railway project hosts two services that communicate over Railway's private network:

```mermaid
flowchart LR
    A[Developer: git push] --> B[GitHub Repository]
    B -->|Webhook trigger| C[Railway: Build via Dockerfile]
    C --> D[Web Service Container]
    D <-->|Private network<br/>postgres.railway.internal| E[(PostgreSQL Service)]
    E -.->|TCP Proxy / Public Networking<br/>external tools only| F[DBeaver - Local Machine]
    D --> G[Public Domain<br/>*.up.railway.app]
```

*   **Web Service:** built directly from this repository's `Dockerfile` on every push to `main` — no Nixpacks auto-detection or Procfile involved, since the Dockerfile's `CMD` already fully specifies how the app starts. Railway injects the runtime `PORT`, which Gunicorn binds to dynamically.
*   **PostgreSQL Service:** a managed Postgres instance, private by default. The Web Service connects to it using Railway's internal service reference (`${{Postgres.DATABASE_URL}}`) rather than a manually copy-pasted connection string — this resolves automatically at deploy time, uses the private network (no egress cost, lower latency), and never needs updating if the database credentials rotate.
*   **TCP Proxy (Public Networking):** disabled by default for security — explicitly enabled on the Postgres service to expose a `DATABASE_PUBLIC_URL`, used *only* for connecting external tools (e.g. DBeaver) and running one-off administrative commands (schema migrations) from a local machine. The application itself never uses this public URL.
*   **Environment Variables:** `JWT_SECRET_KEY`, `CORS_ORIGINS`, and `IS_PRODUCTION` are configured directly on the Web Service, separate from the database credentials.

> **Visual Proof: Railway Project Architecture**
![Railway dashboard showing the Web Service and PostgreSQL service connected within one project](assets/img_readme/railway-architecture-overview.png)

> **Visual Proof: Live, Deployed API**
![Swagger UI opened at the live Railway domain, confirming the API is publicly reachable and fully documented](assets/img_readme/railway-live-apidocs.png)

### Managing the production database (migrations & seeding)
Because this project runs on Railway's free trial tier (no shell access), schema migrations and seed data are applied from a local machine, explicitly pointed at the production database for a single command only — the local `.env` file is never modified for this:
```bash
# Apply schema migrations
DATABASE_URL="<DATABASE_PUBLIC_URL from Railway>" flask db upgrade

# Populate the live database with sample data
DATABASE_URL="<DATABASE_PUBLIC_URL from Railway>" python seed.py
```
`seed.py` checks for existing records before inserting, so it is safe to re-run against production at any time without creating duplicates.

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
   Or, to run it exactly as it runs in production, via Docker — see [Containerization](#containerization-docker).

---

## Interactive API Documentation (Swagger)

This system is thoroughly documented using **Flasgger**.

Once the local development server is running, navigate to the following URL in your browser to access the interactive Swagger UI and test endpoints directly:
👉 **[http://127.0.0.1:5000/apidocs](http://127.0.0.1:5000/apidocs)**

The same documentation is also available on the live deployment — see the [Live API Documentation](#multi-vendor-e-commerce-api) link at the top of this README.

> **Visual Proof: Developer Experience**
![Swagger UI interface showing grouped endpoints](assets/img_readme/swaggerUI.png)

Below is the testing matrix covering all core functionalities.

### 1. Authentication & Users (`/auth`, `/users`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/users` | Register a new user | Validates payload shape via `UserRegisterSchema`; rejects duplicate emails; rate-limited to 10/hour. | ✅ |
| `POST` | `/auth/login` | Authenticate & get JWT | Validates credentials, reactivates soft-deleted accounts; rate-limited to 5/minute. | ✅ |
| `GET` | `/users/me` | Get current identity | Successfully extracts data from JWT. | ✅ |
| `DELETE`| `/users/{id}` | Deactivate account | Triggers cascade soft-delete for sellers and products. | ✅ |

### 2. Store Management (`/sellers`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/sellers` | Register a store | Restricts 1 store per user, validates duplicate store names. | ✅ |
| `PUT` | `/sellers` | Update store profile | Ensures only the owner can update. | ✅ |

### 3. Catalog Management (`/categories`, `/products`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/categories` | Create category | Protected by `@roles_required('admin')`. | ✅ |
| `GET` | `/products` | List all products | Tests dynamic filters (name, category, min/max price) & pagination. | ✅ |
| `POST` | `/products` | Add new product | Auto-generates UUID slug, validates stock/price constraints via `ProductCreateSchema`. | ✅ |
| `PUT` | `/products/{id}` | Update product | Regenerates slug ONLY if the product name is changed. | ✅ |
| `DELETE`| `/products/{id}` | Delete a product | **Blocked with `409`** if the product is tied to a `pending`, `processing`, or `shipped` order. | ✅ |

### 4. Cart & Checkout (`/carts`, `/orders`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/carts/items` | Add to cart | Prevents sellers from buying their own products, checks stock. | ✅ |
| `POST` | `/orders/checkout` | Process transaction | Successfully splits 1 cart into multiple distinct seller orders. | ✅ |
| `GET` | `/orders` | Get user orders | Filters by `?status=`, searches by `?product=`, sorts by `?sort=asc/desc`, paginated. | ✅ |
| `PUT` | `/orders/{id}/status`| Update logistics | Admins can update anything. Sellers manage shipping. Buyers can only cancel. | ✅ |
| `DELETE`| `/orders/{id}` | Delete an order record | Only succeeds when order status is `cancelled`; otherwise rejected. | ✅ |

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

*   **Distributed Rate Limiting:** Migrating `Flask-Limiter`'s storage backend from in-memory to a Redis-backed store, so rate limits are enforced consistently across all Gunicorn worker processes rather than per-worker (see [Infrastructure & Deployment Readiness](#infrastructure--deployment-readiness)).
*   **Advanced Authentication:** Implementing a dual-token `JWT architecture (Access & Refresh Tokens)` with Token Freshness to improve UX and secure sensitive endpoints.
*   **Direct Checkout API:** Building a decoupled `"Buy Now"` route to bypass the cart state, reducing user friction for single-item purchases.
*   **API Versioning:** Introducing a `/api/v1/` prefix ahead of any breaking changes, to support long-term client compatibility.

> ✅ Several items previously listed here have since been completed: request/response validation now runs through dedicated **Marshmallow DTO schemas** in a layered MCS architecture, database schema evolution is managed via **Flask-Migrate**, **rate limiting** protects auth endpoints, and a **CI pipeline** runs the full test suite on every push (see [Infrastructure & Deployment Readiness](#infrastructure--deployment-readiness)). The application is also fully **containerized** and **live-deployed** (see [Containerization](#containerization-docker) and [Cloud Architecture](#cloud-architecture-railway)).