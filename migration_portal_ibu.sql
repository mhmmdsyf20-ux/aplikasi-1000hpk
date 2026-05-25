-- =============================================================================
-- migration_portal_ibu.sql
-- Migrasi database untuk fitur Parent Portal (Portal Web untuk Ibu/Orang Tua)
-- =============================================================================
--
-- INSTRUKSI EKSEKUSI:
--   1. Jalankan script ini SEKALI sebelum men-deploy fitur portal ibu.
--   2. Script ini AMAN dijalankan pada database yang sudah berisi data —
--      semua perubahan bersifat additive (menambah kolom/nilai, tidak menghapus).
--   3. Kolom baru (email, no_whatsapp) bersifat NULL sehingga akun petugas
--      yang sudah ada tidak akan terpengaruh.
--   4. Cara menjalankan via MySQL CLI:
--        mysql -u <user> -p <nama_database> < migration_portal_ibu.sql
--      Atau dari dalam MySQL shell:
--        SOURCE /path/to/migration_portal_ibu.sql;
--   5. Pastikan Anda memiliki backup database sebelum menjalankan migrasi
--      pada lingkungan produksi.
--   6. Script ini TIDAK boleh dijalankan lebih dari satu kali. Jika dijalankan
--      ulang, MySQL akan mengembalikan error "Duplicate column name" yang dapat
--      diabaikan jika kolom sudah ada, atau gunakan IF NOT EXISTS (MySQL 8.0+).
--
-- PERUBAHAN YANG DILAKUKAN:
--   - Menambahkan kolom `email` (VARCHAR 100, NULL, UNIQUE) ke tabel `users`
--   - Menambahkan kolom `no_whatsapp` (VARCHAR 20, NULL) ke tabel `users`
--   - Memperluas enum `role` dengan menambahkan nilai 'user'
--
-- Requirements: 1.1, 1.2, 1.3
-- =============================================================================

-- 1. Tambahkan kolom email (nullable agar akun petugas existing tidak terpengaruh)
ALTER TABLE users
    ADD COLUMN email VARCHAR(100) NULL;

-- 2. Tambahkan unique index pada kolom email
--    (MySQL: constraint UNIQUE hanya berlaku untuk nilai non-NULL,
--     sehingga beberapa akun petugas tanpa email dapat coexist)
ALTER TABLE users
    ADD UNIQUE INDEX uq_users_email (email);

-- 3. Tambahkan kolom no_whatsapp (nullable, hanya untuk akun ibu)
ALTER TABLE users
    ADD COLUMN no_whatsapp VARCHAR(20) NULL;

-- 4. Perluas enum role dengan menambahkan nilai 'user'
--    (MySQL memerlukan MODIFY COLUMN untuk mengubah definisi enum)
ALTER TABLE users
    MODIFY COLUMN role ENUM('admin', 'petugas', 'user') NOT NULL;

-- =============================================================================
-- Selesai. Verifikasi perubahan dengan perintah berikut:
--   DESCRIBE users;
-- =============================================================================
