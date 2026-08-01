[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoShop Database Architecture

Repositori ini berisi rancangan skema basis data, data sampel (seeding), dan kueri operasional untuk sistem e-commerce RevoShop. Proyek ini mendemonstrasikan implementasi *Data Definition Language* (DDL) dan *Data Manipulation Language* (DML) menggunakan PostgreSQL.

## 📊 Dokumentasi Visual & Skema

Berikut adalah hasil eksekusi dan visualisasi dari basis data RevoShop:

**1. Diagram Relasi Tabel (Bagian 1)**
![Diagram Tabel 1](./assets/diagramtable1.png)

**2. Diagram Relasi Tabel (Bagian 2)**
![Diagram Tabel 2](./assets/diagramtable2.png)

**3. Diagram Relasi Tabel (Bagian 3)**
![Diagram Tabel 3](./assets/diagramtable3.png)

## 🗄️ Struktur Tabel
Skema ini mengimplementasikan desain relasional yang dinormalisasi dengan 5 tabel utama:

1. **`users`**: Entitas pengguna yang menggunakan kredensial email (dilindungi dengan algoritma *hash password*).
2. **`categories`**: Tabel *master* (referensi) untuk hierarki klasifikasi produk.
3. **`products`**: Entitas barang dagangan, dihubungkan secara spesifik ke tabel `categories` (Relasi 1:N). Menggunakan *constraint* `CHECK` untuk memastikan harga dan stok tidak bernilai negatif.
4. **`orders`**: Tabel *header* transaksi (Relasi 1:N dari `users`), memanfaatkan *custom type* ENUM untuk integritas status pesanan (`PENDING`, `PAID`, `SHIPPED`, `CANCELED`).
5. **`order_items`**: *Junction table* (Relasi M:N antara `orders` dan `products`). Menggunakan *Composite Primary Key* untuk mencegah duplikasi pemuatan produk yang sama dalam satu ID pesanan, serta menangkap data harga historis (*unit_price*) pada saat transaksi terjadi.

## ⚙️ Local Database Setup (PostgreSQL)
Untuk menjalankan dan menguji skema ini secara lokal pada komputer Anda, ikuti langkah berikut:

1. Buka aplikasi *database client* (seperti DBeaver atau pgAdmin).
2. Buat database lokal baru bernama `revoshop`.
3. Buka *SQL Editor* pada database `revoshop` tersebut.
4. Eksekusi file SQL dengan urutan yang ketat berikut:
   - Jalankan `schema.sql` untuk membangun seluruh tabel, *custom type*, dan batasan (*constraint*).
   - Jalankan `seed.sql` untuk memuat data sampel yang realistis ke dalam tabel.
5. Gunakan `queries.sql` untuk memverifikasi fungsionalitas dan logika ekstraksi data, yang secara khusus mendemonstrasikan hierarki penggunaan klausa `WHERE`, `ORDER BY`, dan `LIMIT`.