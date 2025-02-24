from app import app
from db import db
from models import User

with app.app_context():
    users = User.query.all()
    for user in users:
        if user.name is None:
            user.name = user.username  # Default name to username
        if user.email is None:
            user.email = f"{user.username}@example.com"  # Assign a dummy email
        if user.bio is None:
            user.bio = "No bio provided."
        if user.role == 'employer':
            if user.company_name is None:
                user.company_name = "Unknown Company"
            if user.company_website is None:
                user.company_website = "https://example.com"
        elif user.role == 'student':
            if user.resume_link is None:
                user.resume_link = "Not Provided"
            if user.skills is None:
                user.skills = "No skills added yet."
    
    db.session.commit()
    print("Updated existing users with default profile values.")
