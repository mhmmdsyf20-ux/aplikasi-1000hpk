@echo off
cd /d "D:\Program\project web"
set DATABASE_URL=sqlite:///hpk1000-local.db
python -m flask --app "app:create_app()" run --host 0.0.0.0 --port 5000
pause