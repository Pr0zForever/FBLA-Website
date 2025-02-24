from faker import Faker 
from db import db
from app import app, JobPosting, JobApplication, User, EmployerNote
import random
import json
from werkzeug.security import generate_password_hash

# Initialize Faker
fake = Faker()

# Configuration
NUM_EMPLOYERS = 10     
NUM_STUDENTS = 20      
NUM_POSTINGS = 100     
APPLICATIONS_PER_JOB = 10  

with app.app_context():
    print("🔄 Initializing Database Seeding...")

    # ✅ Ensure Database Tables Exist
    db.create_all()

    # ✅ Create a Fixed Employer
    vamsi_employer = User(
        username="VamsiEmployer",
        password=generate_password_hash("Employer", method='pbkdf2:sha256'),
        role="employer",
        name="Vamsi Employer",
        email="vamsi.employer@example.com",
        company_name="Vamsi Tech Inc.",
        company_website="https://vamsitech.com"
    )
    db.session.add(vamsi_employer)

    # ✅ Create a Fixed Student
    vamsi_student = User(
        username="VamsiStudent",
        password=generate_password_hash("Student", method='pbkdf2:sha256'),
        role="student",
        name="Vamsi Student",
        email="vamsi.student@example.com",
        resume_link="https://vamsistudent.com/resume.pdf",
        skills="Python, Machine Learning, Data Analysis, SQL"
    )
    db.session.add(vamsi_student)

    # ✅ Create Additional Employers
    employers = [vamsi_employer]  
    for _ in range(NUM_EMPLOYERS):
        employer = User(
            username=fake.user_name(),
            password=generate_password_hash("password123", method='pbkdf2:sha256'),
            role="employer",
            name=fake.name(),
            email=fake.unique.email(),
            company_name=fake.company(),
            company_website=fake.url()
        )
        db.session.add(employer)
        employers.append(employer)

    # ✅ Create Additional Students
    students = [vamsi_student]  
    for _ in range(NUM_STUDENTS):
        student = User(
            username=fake.user_name(),
            password=generate_password_hash("password123", method='pbkdf2:sha256'),
            role="student",
            name=fake.name(),
            email=fake.unique.email(),
            resume_link=fake.url(),
            skills=", ".join(fake.words(nb=8))
        )
        db.session.add(student)
        students.append(student)

    # ✅ Commit Users Before Proceeding
    db.session.commit()

    # ✅ Generate Job Postings
    job_postings = []
    for _ in range(NUM_POSTINGS):
        employer = random.choice(employers)

        description = f"""
        {fake.paragraph(nb_sentences=3)}

        Responsibilities:
        - {fake.sentence()}  
        - {fake.sentence()}  
        - {fake.sentence()}  
        - {fake.sentence()}  

        About {employer.company_name}:  
        {fake.paragraph(nb_sentences=3)}

        Culture & Benefits:
        - {fake.sentence()}  
        - {fake.sentence()}  
        - {fake.sentence()}  
        """

        qualifications = ", ".join(fake.words(nb=10))

        application_questions = json.dumps([
            "Why are you interested in this position?",
            "Describe a challenging project you've worked on.",
            "What relevant skills do you bring to this role?"
        ])

        job = JobPosting(
            title=fake.job(),
            location=fake.city(),
            description=description.strip(),
            qualifications=qualifications,
            deadline=fake.date_this_year(),
            posted_by=employer.id,  
            approved=True,  
            application_questions=application_questions  
        )
        job_postings.append(job)

    # ✅ Commit Job Postings Before Assigning Applications
    db.session.bulk_save_objects(job_postings)
    db.session.commit()

    # ✅ Retrieve Committed Jobs
    all_jobs = JobPosting.query.all()

    # ✅ Generate 10 Applications for Each Job Posting (with application_id)
    applications = []
    for job in all_jobs:
        applied_students = random.sample(students, min(APPLICATIONS_PER_JOB, len(students)))

        for student in applied_students:
            application = JobApplication(
                job_id=job.id,
                student_id=student.id,
                cover_letter=f"""
                Dear Hiring Manager,

                I am excited to apply for the {job.title} position at {job.employer.company_name}. 
                My background in {student.skills} aligns well with the job requirements. 

                I am eager to contribute to {job.employer.company_name} and look forward to discussing how my skills can add value. 
                
                Thank you for your time and consideration.

                Best regards,  
                {student.name}
                """.strip()
            )
            applications.append(application)

    # ✅ Commit Applications & Retrieve IDs
    db.session.bulk_save_objects(applications)
    db.session.commit()

    # ✅ Retrieve Applications with their IDs
    all_applications = JobApplication.query.all()

    # ✅ Assign Employer Notes (with application_id)
    employer_notes = []
    for app in all_applications:
        note = EmployerNote(
            employer_id=app.job.employer.id,  # The employer who posted the job
            student_id=app.student_id,
            job_id=app.job_id,
            application_id=app.id,  # ✅ Ensure this is correctly stored
            note=f"Employer feedback: {fake.sentence()}"
        )
        employer_notes.append(note)

    # ✅ Commit Employer Notes
    db.session.bulk_save_objects(employer_notes)
    db.session.commit()

    # ✅ Final Log
    print("\n✅ Successfully Seeded Database:")
    print(f"  - {NUM_EMPLOYERS + 1} employers (including VamsiEmployer)")
    print(f"  - {NUM_STUDENTS + 1} students (including VamsiStudent)")
    print(f"  - {NUM_POSTINGS} job postings")
    print(f"  - {len(all_applications)} job applications")
    print(f"  - {len(employer_notes)} employer notes")
