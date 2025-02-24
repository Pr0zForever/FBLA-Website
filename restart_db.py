from app import app
from db import db

with app.app_context():
    db.drop_all()  # Deletes all tables
    db.create_all()  # Recreates the tables
    print("Database schema updated successfully!")