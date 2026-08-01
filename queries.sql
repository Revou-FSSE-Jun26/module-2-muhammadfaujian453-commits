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