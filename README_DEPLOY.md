# Deploy Aplikasi 1000 HPK

Aplikasi ini sudah siap untuk di-deploy online dengan host yang mendukung WSGI atau `gunicorn`.

## 1. Deploy ke Railway

Aplikasi sudah siap untuk deploy ke Railway.

Agar lebih mudah, Railway akan membaca `railway.toml` dan menjalankan perintah start otomatis.

Aplikasi ini sudah memiliki:

- `Procfile` untuk menjalankan `gunicorn`
- `requirements.txt` dengan `gunicorn`
- `railway.toml` dengan perintah start dan healthcheck
- `runtime.txt` untuk Python 3.11

### Langkah cepat Railway

1. Push repository ini ke GitHub.
2. Buka https://railway.app dan login.
3. Pilih `New Project` → `Deploy from GitHub`.
4. Pilih repository ini.
5. Di Railway Dashboard, buka `Variables` dan tambahkan:
   - `DATABASE_URL` atau `MYSQL_URL`
   - `SECRET_KEY`
   - `WA_GATEWAY`, `WA_API_KEY`, `WA_SENDER` jika fitur WhatsApp aktif
   - `NAMA_FASILITAS` (misal `Puskesmas`)
6. Deploy.

Railway akan menggunakan konfigurasi berikut dari `railway.toml`:

```toml
[deploy]
startCommand = "gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 1 --threads 2 --max-requests 1000 --max-requests-jitter 100 \"app:create_app()\""
healthcheckPath = "/auth/login"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Tips Railway

- Gunakan database Railway bawaan jika Anda tidak punya database sendiri.
- Jika pakai MySQL, Railway biasanya menyediakan `MYSQL_URL`.
- Jika pakai Postgres, gunakan `DATABASE_URL`.
- Pastikan `SECRET_KEY` diisi agar session aman.

## 2. Deploy ke Heroku / Platform serupa

Aplikasi ya sudah siap juga di platform lain karena `Procfile` dan `gunicorn` sudah ada.

### Langkah Heroku

1. Push repo ke GitHub.
2. Buat app baru di Heroku.
3. Hubungkan GitHub repo.
4. Tambahkan config vars yang sama:
   - `DATABASE_URL` atau `MYSQL_URL`
   - `SECRET_KEY`
   - `WA_GATEWAY`, `WA_API_KEY`, `WA_SENDER`
   - `NAMA_FASILITAS`
5. Deploy.

Jika menggunakan Heroku, Anda juga bisa menggunakan `Procfile` langsung untuk menjalankan `gunicorn`.

## 3. Deploy di PythonAnywhere

File `passenger_wsgi.py` telah diperbarui agar bekerja dari folder proyek secara generik.

Gunakan PythonAnywhere Web tab, dan arahkan WSGI file ke `passenger_wsgi.py`.

## 4. Jalankan secara nonstop di server Linux sendiri

Jalankan perintah ini di server:

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8000 "app:create_app()"
```

Untuk menjaga agar tidak berhenti setelah logout, gunakan `screen`, `tmux`, atau systemd.

Contoh unit systemd:

```ini
[Unit]
Description=1000 HPK Flask app
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

## 5. Akses online

Setelah deploy sukses:

- `http://<your-domain>/auth/login` — login admin/petugas
- `http://<your-domain>/portal/login` — login ibu/user

## 6. Perlu diperhatikan

- `gunicorn` tidak cocok dijalankan natively di Windows untuk production.
- Untuk development lokal, jalankan `python app.py`.
- Untuk online production, gunakan host Linux atau platform cloud.

## 2. Deploy di PythonAnywhere

File `passenger_wsgi.py` telah diperbarui agar bekerja dari folder proyek secara generik.

Gunakan PythonAnywhere Web tab, dan arahkan WSGI file ke `passenger_wsgi.py`.

## 3. Jalankan secara nonstop di server Linux sendiri

Jalankan perintah ini di server:

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8000 "app:create_app()"
```

Untuk menjaga agar tidak berhenti setelah logout, gunakan `screen`, `tmux`, atau systemd.

Contoh unit systemd:

```ini
[Unit]
Description=1000 HPK Flask app
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
Environment="FLASK_ENV=production"
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

## 4. Akses online

Setelah deploy sukses:

- `http://<your-domain>/auth/login` — login admin/petugas
- `http://<your-domain>/portal/login` — login ibu/user

## 5. Perlu diperhatikan

- `gunicorn` tidak cocok dijalankan natively di Windows untuk production.
- Untuk development lokal, jalankan `python app.py`.
- Untuk online production, gunakan host Linux atau platform cloud.
