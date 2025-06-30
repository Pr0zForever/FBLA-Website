from app import app, db, User
from werkzeug.security import generate_password_hash

def create_user(username, password, role, name, email, school, bio=None, company_name=None, skills=None):
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User {username} already exists.")
        return

    hashed_password = generate_password_hash(password)
    user = User(
        username=username,
        password=hashed_password,
        role=role,
        name=name,
        email=email,
        bio=bio,
        school=school,
        company_name=company_name,
        skills=skills,
        approved=True  # Automatically approve these users
    )
    db.session.add(user)
    db.session.commit()
    print(f"User {username} created successfully!")

if __name__ == "__main__":
    with app.app_context():
        # Creating VamsiStudent
        create_user(
            username="VamsiStudent",
            password="student123",
            role="student",
            name="Vamsi Student",
            email="vamsi.student@example.com",
            school="Tompkins High School",
            bio="Enthusiastic student passionate about AI, robotics, and software development.",
            skills="Python, C++, Machine Learning, Robotics"
        )

        # Creating VamsiEmployer
        create_user(
            username="VamsiEmployer",
            password="employer123",
            role="employer",
            name="Vamsi Employer",
            email="vamsi.employer@example.com",
            school="Tompkins High School",
            bio="Experienced tech entrepreneur looking for talented students.",
            company_name="Tech Innovators LLC"
        )
