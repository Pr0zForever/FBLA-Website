import random
from datetime import datetime, timedelta
from faker import Faker
from app import db, User, JobPosting, JobApplication, Message, Notification, EmployerNote, UserConnection
from werkzeug.security import generate_password_hash
import json
from flask import Flask

fake = Faker()

schools = ["Jordan High School", "Seven Lakes High School", "Tompkins High School"]

def create_admins():
    admins = [
        {"username": "j_admin", "school": "Jordan High School"},
        {"username": "s_admin", "school": "Seven Lakes High School"},
        {"username": "t_admin", "school": "Tompkins High School"},
    ]
    for admin in admins:
        user = User(
            username=admin["username"],
            email=f"{admin['username']}@jobconnect.com",
            password=generate_password_hash("Admin"),
            role="admin",
            name=f"{admin['school']} Admin",
            school=admin["school"],
            approved=True
        )
        db.session.add(user)
    db.session.commit()

def create_employers(n=30):
    employers = []
    for _ in range(n):
        employer = User(
            username=fake.unique.user_name(),
            email=fake.unique.company_email(),
            password=generate_password_hash("Employer"),
            role="employer",
            name=fake.name(),
            company_name=fake.company(),
            company_website=fake.url(),
            bio=fake.text(max_nb_chars=200),
            school=random.choice(schools),
            approved=True
        )
        employers.append(employer)
        db.session.add(employer)

    # Add VamsiEmployer with rich content
    vamsi_employer = User(
        username="VamsiEmployer",
        email="vamsi@company.com",
        password=generate_password_hash("Vamsi"),
        role="employer",
        name="Vamsi G",
        company_name="NextGen Robotics",
        company_website="https://nextgenrobotics.ai",
        bio="We specialize in building autonomous AI-driven robots for education, defense, and healthcare industries.",
        school="Tompkins High School",
        approved=True
    )
    employers.append(vamsi_employer)
    db.session.add(vamsi_employer)
    db.session.commit()
    return employers

def create_students(n=50):
    students = []
    for _ in range(n):
        student = User(
            username=fake.unique.user_name(),
            email=fake.unique.email(),
            password=generate_password_hash("Student"),
            role="student",
            name=fake.name(),
            bio=fake.text(max_nb_chars=200),
            skills=", ".join(fake.words(nb=random.randint(3, 7))),
            resume_link=fake.url(),
            school=random.choice(schools),
            approved=True
        )
        students.append(student)
        db.session.add(student)

    # Add VamsiStudent with rich content
    vamsi_student = User(
        username="VamsiStudent",
        email="vamsi@student.com",
        password=generate_password_hash("Vamsi"),
        role="student",
        name="Vamsi Yada",
        bio="Aspiring AI and robotics engineer. I’ve built autonomous robots using Python, ROS, and TensorFlow. Passionate about innovation and impact.",
        skills="Python, TensorFlow, PyTorch, ROS, Leadership, Public Speaking, Machine Learning, Robotics",
        resume_link="https://vamsi-resume.ai/resume.pdf",
        school="Tompkins High School",
        approved=True
    )
    students.append(vamsi_student)
    db.session.add(vamsi_student)
    db.session.commit()
    return students

def create_job_postings(employers, n=100):
    postings = []
    for _ in range(n):
        employer = random.choice(employers)
        job = JobPosting(
            title=fake.job(),
            location=fake.city(),
            description=fake.paragraph(nb_sentences=15),
            qualifications=fake.paragraph(nb_sentences=10),
            deadline=(datetime.now() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d"),
            posted_by=employer.id,
            approved=random.choice([True, False]),
            application_questions=json.dumps([fake.sentence() for _ in range(random.randint(1, 5))]),
            school=employer.school
        )
        postings.append(job)
        db.session.add(job)

    # Add a specific job by VamsiEmployer for VamsiStudent to apply
    vamsi_employer = User.query.filter_by(username="VamsiEmployer").first()
    ai_job = JobPosting(
        title="AI Robotics Intern",
        location="Houston, TX",
        description="We are looking for a high school intern interested in building AI-powered robotics platforms. You will work with Python, TensorFlow, microcontrollers, and simulation environments like Gazebo or Isaac Sim.",
        qualifications="Strong knowledge in Python and TensorFlow. Experience with ROS or microcontrollers is a plus. Must be passionate about robotics and AI research.",
        deadline=(datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
        posted_by=vamsi_employer.id,
        approved=True,
        application_questions=json.dumps([
            "What is your experience with robotics and machine learning?",
            "Describe a project where you built something innovative.",
            "Why do you want to join NextGen Robotics?"
        ]),
        school=vamsi_employer.school
    )
    postings.append(ai_job)
    db.session.add(ai_job)
    db.session.commit()
    return postings

def create_job_applications(students, postings, n=200):
    applications = []
    for _ in range(n):
        student = random.choice(students)
        job = random.choice(postings)
        if job.school != student.school:
            continue
        application = JobApplication(
            job_id=job.id,
            user_id=student.id,
            cover_letter=fake.paragraph(nb_sentences=10),
            resume_url=fake.url(),
            status=random.choice(["Pending", "Reviewed", "Rejected", "Accepted"]),
            timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        applications.append(application)
        db.session.add(application)

    # Ensure VamsiStudent applies to VamsiEmployer’s job
    vamsi_student = User.query.filter_by(username="VamsiStudent").first()
    ai_job = JobPosting.query.filter_by(title="AI Robotics Intern").first()
    if vamsi_student and ai_job:
        vamsi_application = JobApplication(
            job_id=ai_job.id,
            user_id=vamsi_student.id,
            cover_letter=(
                "Dear Hiring Team,\n\n"
                "I am excited to apply for the AI Robotics Intern position at NextGen Robotics. "
                "I’ve led multiple high school robotics projects using Python, OpenCV, and ROS. "
                "I’m eager to contribute and learn from your cutting-edge work in autonomous systems.\n\n"
                "Best regards,\nVamsi Yada"
            ),
            resume_url="https://vamsi-resume.ai/resume.pdf",
            status="Pending",
            timestamp=datetime.now()
        )
        applications.append(vamsi_application)
        db.session.add(vamsi_application)
    db.session.commit()
    return applications

def create_messages(users, n=150):
    for _ in range(n):
        sender, receiver = random.sample(users, 2)
        message = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content=fake.text(max_nb_chars=150),
            timestamp=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.session.add(message)
    db.session.commit()

def create_notifications(users, n=100):
    for _ in range(n):
        user = random.choice(users)
        notification = Notification(
            user_id=user.id,
            message=fake.sentence(),
            seen=random.choice([True, False])
        )
        db.session.add(notification)
    db.session.commit()

def create_employer_notes(applications, n=100):
    count = 0
    while count < n:
        app = random.choice(applications)
        job = JobPosting.query.get(app.job_id)
        student = User.query.get(app.user_id)
        if not job or not student:
            continue

        employer = User.query.get(job.posted_by)
        if not employer:
            continue

        note = EmployerNote(
            application_id=app.id,
            employer_id=employer.id,
            student_id=student.id,
            job_id=job.id,
            note=fake.paragraph(nb_sentences=6)
        )
        db.session.add(note)
        count += 1
    db.session.commit()

def create_user_connections(users, n=100):
    created = 0
    while created < n:
        user1, user2 = random.sample(users, 2)
        if user1.id == user2.id:
            continue

        exists = UserConnection.query.filter(
            ((UserConnection.requester_id == user1.id) & (UserConnection.recipient_id == user2.id)) |
            ((UserConnection.requester_id == user2.id) & (UserConnection.recipient_id == user1.id))
        ).first()
        if exists:
            continue

        connection = UserConnection(
            requester_id=user1.id,
            recipient_id=user2.id
        )
        db.session.add(connection)
        created += 1
    db.session.commit()

def populate_db():
    print("Creating admins...")
    create_admins()
    print("Creating employers...")
    employers = create_employers()
    print("Creating students...")
    students = create_students()
    print("Creating job postings...")
    postings = create_job_postings(employers)
    print("Creating job applications...")
    applications = create_job_applications(students, postings)
    all_users = employers + students
    print("Creating messages...")
    create_messages(all_users)
    print("Creating notifications...")
    create_notifications(all_users)
    print("Creating employer notes...")
    create_employer_notes(applications)
    print("Creating connections...")
    create_user_connections(all_users)
    print("✅ Database seeded successfully!")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        db.drop_all()
        db.create_all()
        populate_db()
