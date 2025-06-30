from faker import Faker
from db import db
from app import app, JobPosting, JobApplication, User, EmployerNote
from werkzeug.security import generate_password_hash
from io import BytesIO
import json
import random
from datetime import datetime, timedelta

# Config
NUM_EMPLOYERS = 10
NUM_STUDENTS = 20
NUM_POSTINGS = 300
APPLICATIONS_PER_JOB = 10
SCHOOL = "Jordan High School"

# Setup
fake = Faker()
Faker.seed(1234)

with app.app_context():
    print("🔄 Starting full seeding...")

    db.drop_all()
    db.create_all()

    # ✅ Create VamsiEmployer
    vamsi_employer = User(
        username="VamsiEmployer",
        password=generate_password_hash("Employer"),
        role="employer",
        name="Vamsi Employer",
        email="vamsi.employer@example.com",
        company_name="Vamsi Tech Inc.",
        company_website="https://vamsitech.com",
        job_title="Senior AI Engineer",
        request_reason="To support student hiring",
        school=SCHOOL,
        bio="Employer passionate about mentoring young tech talent.",
        profile_pic_url=fake.image_url(),
        phone=fake.phone_number(),
        approved=True
    )

    # ✅ Create VamsiStudent
    vamsi_student = User(
        username="VamsiStudent",
        password=generate_password_hash("Student"),
        role="student",
        name="Vamsi Student",
        email="vamsi.student@example.com",
        resume_link="https://vamsistudent.com/resume.pdf",
        grade_level="12",
        skills="Python, Machine Learning, Data Analysis, SQL",
        bio="Aspiring data scientist with a strong foundation in Python and ML.",
        profile_pic_url=fake.image_url(),
        phone=fake.phone_number(),
        school=SCHOOL,
        approved=True
    )

    db.session.add_all([vamsi_employer, vamsi_student])
    db.session.commit()

    employers = [vamsi_employer]
    students = [vamsi_student]

    # ✅ Generate Employers
    for _ in range(NUM_EMPLOYERS):
        emp = User(
            username=fake.user_name(),
            password=generate_password_hash("password123"),
            role="employer",
            name=fake.name(),
            email=fake.unique.email(),
            company_name=fake.company(),
            company_website=fake.url(),
            job_title=fake.job(),
            request_reason=fake.text(50),
            school=random.choice([SCHOOL]),
            bio=fake.text(100),
            profile_pic_url=fake.image_url(),
            phone=fake.phone_number(),
            # weighted cboice for approved status
            approved=random.choice([True, True, True, False])  # 75% approved
        )
        employers.append(emp)
        db.session.add(emp)

    # ✅ Generate Students
    for _ in range(NUM_STUDENTS):
        stu = User(
            username=fake.user_name(),
            password=generate_password_hash("password123"),
            role="student",
            name=fake.name(),
            email=fake.unique.email(),
            resume_link=fake.url(),
            grade_level=random.choice(["9", "10", "11", "12"]),
            skills=", ".join(fake.words(nb=6)),
            school=SCHOOL,
            bio=fake.text(100),
            profile_pic_url=fake.image_url(),
            phone=fake.phone_number(),
            approved=True
        )
        students.append(stu)
        db.session.add(stu)

    db.session.commit()

    # ✅ Generate Job Postings
    job_postings = []
    application_questions = json.dumps([
        "Why are you interested in this position?",
        "Describe a challenging project you've worked on.",
        "What relevant skills do you bring to this role?"
    ])

    for _ in range(NUM_POSTINGS):
        emp = random.choice(employers)
        job = JobPosting(
            title=fake.job(),
            location=fake.city(),
            description=fake.paragraph(nb_sentences=4) + "\n\nResponsibilities:\n- " +
                        "\n- ".join(fake.sentences(nb=3)),
            qualifications=", ".join(fake.words(10)),
            deadline=(datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d'),
            posted_by=emp.id,
            approved=False,  # 75% approved,
            flagged=random.choice([False, False, False, True]),  # 25% flagged,   
            school=emp.school,
            application_questions=application_questions
        )
        job_postings.append(job)

    db.session.bulk_save_objects(job_postings)
    db.session.commit()

    # ✅ Create Applications
    all_jobs = JobPosting.query.all()
    applications = []

    for job in all_jobs:
        applicants = random.sample(students, min(APPLICATIONS_PER_JOB, len(students)))
        for stu in applicants:
            resume_text = f"Resume for {stu.name}"
            app = JobApplication(
                job_id=job.id,
                user_id=stu.id,
                cover_letter=fake.paragraph(nb_sentences=3),
                resume_url=stu.resume_link,
                resume_filename=f"{stu.username}_resume.pdf",
                resume_data=BytesIO(resume_text.encode()).read(),
                status=random.choice(["Pending", "Reviewed", "Accepted", "Rejected"]),
                created_at=datetime.utcnow()
            )
            applications.append(app)

    db.session.bulk_save_objects(applications)
    db.session.commit()

    # ✅ Create Employer Notes
    employer_notes = []
    all_apps = JobApplication.query.all()
    for app in all_apps:
        note = EmployerNote(
            application_id=app.id,
            employer_id=app.job.posted_by,
            student_id=app.user_id,
            job_id=app.job_id,
            note=fake.sentence()
        )
        employer_notes.append(note)

    db.session.bulk_save_objects(employer_notes)
    db.session.commit()

    flagged_jobs_count = sum(1 for job in job_postings if job.flagged)

    print("\n✅ Database Seeded with:")
    print(f"  - {len(employers)} Employers")
    print(f"  - {len(students)} Students")
    print(f"  - {len(job_postings)} Job Postings")
    print(f"  - {flagged_jobs_count} Flagged Jobs 🚩")
    print(f"  - {len(applications)} Applications")
    print(f"  - {len(employer_notes)} Employer Notes")
    print("  - VamsiStudent and VamsiEmployer fully set up.")



    from app import UserConnection  # Make sure this is imported at the top


    print("🔗 Generating user connections...")

    # Retrieve seeded users
    vamsi_student = User.query.filter_by(username="VamsiStudent").first()
    vamsi_employer = User.query.filter_by(username="VamsiEmployer").first()

    # Create connections for VamsiStudent with random students and employers
    student_peers = random.sample([s for s in students if s.id != vamsi_student.id], min(5, len(students)-1))
    employer_peers = random.sample(employers, min(3, len(employers)))

    for peer in student_peers:
        db.session.add(UserConnection(requester_id=vamsi_student.id, recipient_id=peer.id))
        db.session.add(UserConnection(requester_id=peer.id, recipient_id=vamsi_student.id))  # optional reciprocal

    for emp in employer_peers:
        db.session.add(UserConnection(requester_id=vamsi_student.id, recipient_id=emp.id))

    # Create connections for VamsiEmployer with students and employers
    connected_students = random.sample(students, min(5, len(students)))
    connected_employers = random.sample([e for e in employers if e.id != vamsi_employer.id], min(3, len(employers)-1))

    for stu in connected_students:
        db.session.add(UserConnection(requester_id=vamsi_employer.id, recipient_id=stu.id))
        db.session.add(UserConnection(requester_id=stu.id, recipient_id=vamsi_employer.id))  # optional reciprocal

    for peer_emp in connected_employers:
        db.session.add(UserConnection(requester_id=vamsi_employer.id, recipient_id=peer_emp.id))

    db.session.commit()

    print(f"  - {len(student_peers)*2 + len(employer_peers)} connections created for VamsiStudent")
    print(f"  - {len(connected_students)*2 + len(connected_employers)} connections created for VamsiEmployer")
