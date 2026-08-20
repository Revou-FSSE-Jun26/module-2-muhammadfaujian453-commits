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
> 
> *[`![Database ERD](./assets/diagram.png)`]*

### Table Structure
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

## 🚀 Installation & Initialization

1. Clone the repository and navigate to the root directory.
2. Initialize and activate a Python virtual environment.
3. Install the necessary dependencies:
   ```bash
   pip install -r requirements.txt
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

---

## 🧪 API Endpoints & Testing Matrix

This system is thoroughly documented using **Flasgger**. Navigate to `/apidocs` when the server is running to interact with the Swagger UI. 

Below is the testing matrix covering all core functionalities. 
> *[Add hyperlinks to Postman screenshot proofs]*

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