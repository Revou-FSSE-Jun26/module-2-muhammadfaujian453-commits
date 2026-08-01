-- 1. Insert Users
INSERT INTO users (email, password_hash, full_name) VALUES
('budi.teknik@email.com', '$2y$10$Qx/hO8Z8Z9z...', 'Budi Santoso'),
('citra.rasa@email.com', '$2y$10$Yc/jK1V9V2p...', 'Citra Lestari'),
('andi.procurement@email.com', '$2y$10$Zx/pM4N5N8m...', 'Andi Wijaya');

-- 2. Insert Categories
INSERT INTO categories (name, description) VALUES
('Komponen Elektrikal', 'Peralatan dan suku cadang untuk perakitan panel listrik industri.'),
('Camilan & Konfeksi', 'Produk makanan ringan buatan rumahan berdasar cokelat.');

-- 3. Insert Products
INSERT INTO products (category_id, name, description, price, stock) VALUES
(1, 'MCB 3 Phase 16A', 'Miniature Circuit Breaker untuk proteksi arus lebih', 155000.00, 50),
(1, 'Box Panel Indoor 40x50x20', 'Plat baja tebal 1.2mm dengan powder coating', 450000.00, 15),
(2, 'Cokelat Almond Premium Bar', 'Cokelat hitam 65% dengan kacang almond panggang utuh', 35000.00, 100),
(2, 'Truffle Cokelat Lumer Pack', 'Isi 10 pcs truffle dengan taburan bubuk kakao murni', 45000.00, 80);

-- 4. Insert Orders
INSERT INTO orders (user_id, status, total_amount) VALUES
(3, 'PENDING', 1060000.00), -- Pesanan Andi (Beli komponen panel)
(2, 'PAID', 175000.00),    -- Pesanan Citra (Beli cokelat bar)
(1, 'SHIPPED', 520000.00);  -- Pesanan Budi (Beli truffle dan komponen)

-- 5. Insert Order Items (Junction Table)
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
-- Item untuk Order 1 (Total: (2 * 155000) + (1 * 450000) = 760000 + biaya lain-lain fiktif = 1060000)
(1, 1, 4, 155000.00),
(1, 2, 1, 440000.00), -- Contoh harga diskon/negosiasi saat transaksi

-- Item untuk Order 2 (Total: 5 * 35000 = 175000)
(2, 3, 5, 35000.00),

-- Item untuk Order 3 (Total: (10 * 45000) + (2 * 35000) = 520000)
(3, 4, 10, 45000.00),
(3, 3, 2, 35000.00);