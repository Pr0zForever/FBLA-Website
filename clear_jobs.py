from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from db import db  # Import your existing db instance from db.py
from app import app  # Import Flask app to get the correct context
from app import app, JobPosting, JobApplication

def clear_jobs():
    with app.app_context():
        try:
            # Delete all job applications first (to avoid foreign key conflicts)
            db.session.query(JobApplication).delete()
            
            # Delete all job postings
            db.session.query(JobPosting).delete()
            
            db.session.commit()
            print("✅ Successfully cleared all job postings and applications.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing jobs: {e}")

if __name__ == "__main__":
    clear_jobs()
