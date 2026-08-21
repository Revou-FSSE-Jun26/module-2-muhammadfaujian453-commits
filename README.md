# Multi-Vendor E-Commerce API

## 📖 Overview
This repository contains a robust, scalable backend API designed for a multi-tenant e-commerce platform. Built with Python and Flask, it utilizes a single-database configuration for Flask using PostgreSQL and SQLAlchemy. The architecture enforces strict domain boundaries, separating buyers, sellers, and system administrators, making it a highly structured foundation for complex marketplace operations.

## ✨ Core Architectural Features
*   **Split-Order Checkout System:** Intelligently dissects a single user cart into multiple isolated orders based on distinct seller IDs, ensuring accurate logistics and financial segregation.
*   **Role-Based Access Control (RBAC):** Secures endpoints using JWT authentication, strictly restricting data mutation operations based on user roles (Admin, Seller, Buyer).
*   **Resilient Data Management:** Implements comprehensive soft-deletion mechanisms across users, stores, and products to maintain referential integrity without destroying historical transaction data.
*   **Dynamic Data Filtering:** Provides robust product discovery through dynamic querying (price ranges, category IDs, text search) combined with offset pagination.
*   **Automated Slug Generation:** Prevents URL collisions by automatically generating unique, SEO-friendly product slugs embedded with UUIDs.

## 🧠 Business Logic & System Workflows

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

---

## 🗄️ Database Schema

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
| **`orders` & `order_items`**| Immutable transaction records (Aggregate Root). | Bridges `users` (buyer) and `sellers`. |

---

## 🛡️ Automated Testing & Quality Assurance

This backend is safeguarded by a comprehensive **End-to-End (E2E) Test Suite** built with `pytest`. The test architecture utilizes isolated SQLite in-memory databases with session rollbacks, ensuring zero data leakage between test executions.

*   **Positive & Negative Testing:** Validates data boundaries (e.g., rejecting negative stock quantities or zero-priced items).
*   **Security Validations:** Actively tests against Horizontal Privilege Escalation (IDOR), ensuring buyers cannot access or modify orders belonging to other accounts.
*   **Anomaly Prevention:** Halts checkout executions involving "Ghost Products" (items soft-deleted by sellers while still resting in a buyer's cart).

> **Visual Proof: E2E Test Coverage**
![Pytest terminal showing 100% Passed metrics across 29+ test cases](assets/img_readme/pytestresult.png)

---

## 🚀 Installation & Initialization

1. Clone the repository and navigate to the root directory.
2. Initialize and activate a Python virtual environment[cite: 8].
3. Install the necessary dependencies[cite: 8]:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your `.env` file with the required environment variables:
   ```env
   SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost:5432/your_db
   JWT_SECRET_KEY=your_secure_secret_key
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

---

## 🧪 Interactive API Documentation (Swagger UI)

This system is thoroughly documented using **Flasgger**. 

Once the local development server is running, navigate to the following URL in your browser to access the interactive Swagger UI and test endpoints directly:
👉 **[http://127.0.0.1:5000/apidocs](http://127.0.0.1:5000/apidocs)**

> **Visual Proof: Developer Experience**
![Swagger UI interface showing grouped endpoints](assets/img_readme/swaggerUI.png)

Below is the testing matrix covering all core functionalities. 

### 1. Authentication & Users (`/auth`, `/users`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Register a new user | Validates duplicate emails. | [PASS] |
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
| `POST` | `/products` | Add new product | Auto-generates UUID slug, validates stock/price constraints. | [PASS] |
| `PUT` | `/products/{id}` | Update product | Regenerates slug ONLY if the product name is changed. | [PASS] |

### 4. Cart & Checkout (`/carts`, `/orders`)
| Method | Endpoint | Description | Testing Criteria | Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/carts/items` | Add to cart | Prevents sellers from buying their own products, checks stock. | [PASS] |
| `POST` | `/orders/checkout` | Process transaction | Successfully splits 1 cart into multiple distinct seller orders. | [PASS] |
| `GET` | `/orders` | Get user orders | Properly filters order history by `?status=pending/shipped`. | [PASS] |
| `PUT` | `/orders/{id}/status`| Update logistics | Admins can update anything. Sellers manage shipping. Buyers can only cancel. | [PASS] |

---

> **Visual Proof: Example of Security & RBAC in Action when a seller tries to cancel order**
![Postman showing 403 Forbidden](assets/img_readme/rbacforbidden.png)