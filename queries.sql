-- Query: Menampilkan 2 produk dengan harga tertinggi yang stoknya masih di atas 20 unit.
-- Mendemonstrasikan filter data (WHERE), pengurutan (ORDER BY), dan pembatasan hasil (LIMIT).

SELECT 
    id, 
    name, 
    price, 
    stock
FROM 
    products
WHERE 
    stock > 20
ORDER BY 
    price DESC
LIMIT 2;

-----------------------------------------------------------------------------------------------------------
-- Untuk CheckPoint 2, DROP tabel terlebih dahulu agar riwayat migrasi terbaca dari awal

DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TYPE IF EXISTS order_status CASCADE;