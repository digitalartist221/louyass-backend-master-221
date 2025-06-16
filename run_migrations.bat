@echo off
python -m pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
python app/main.py
