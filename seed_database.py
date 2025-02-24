from faker import Faker 
from db import db
from app import app, JobPosting, JobApplication, User
import random
import json
from werkzeug.security import generate_password_hash

# Initialize Faker
fake = Faker()

# Configuration
NUM_EMPLOYERS = 10     # Number of employers (excluding VamsiEmployer)
NUM_STUDENTS = 20      # Number of students (excluding VamsiStudent)
NUM_POSTINGS = 100     # Number of job postings
NUM_APPLICATIONS = 200 # Number of applications

with app.app_context():
    print("🔄 Initializing Database Seeding...")

    # ✅ Ensure Database Tables Exist Before Adding Data
    db.create_all()

    # ✅ Create a Fixed Employer (VamsiEmployer)
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

    # ✅ Create a Fixed Student (VamsiStudent)
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
    employers = [vamsi_employer]  # Include VamsiEmployer in employer list
    for _ in range(NUM_EMPLOYERS):
        employer = User(
            username=fake.user_name(),
            password=generate_password_hash("password123", method='pbkdf2:sha256'),
            role="employer",
            name=fake.name(),
            email=fake.email(),
            company_name=fake.company(),
            company_website=fake.url()
        )
        db.session.add(employer)
        employers.append(employer)

    # ✅ Create Additional Students
    students = [vamsi_student]  # Include VamsiStudent in student list
    for _ in range(NUM_STUDENTS):
        student = User(
            username=fake.user_name(),
            password=generate_password_hash("password123", method='pbkdf2:sha256'),
            role="student",
            name=fake.name(),
            email=fake.email(),
            resume_link=fake.url(),
            skills=", ".join(fake.words(nb=8))  # Structured skills
        )
        db.session.add(student)
        students.append(student)

    # 🔹 Commit Users Before Assigning Jobs & Applications
    db.session.commit()

    # ✅ Print User Data
    print("\n🔍 All Users in Database:")
    all_users = User.query.all()
    for user in all_users:
        print(f"👤 Username: {user.username}, Role: {user.role}, Email: {user.email}, Company: {user.company_name or 'N/A'}")

    # ✅ Generate Job Postings (Assign Some to VamsiEmployer)
    job_postings = []
    for _ in range(NUM_POSTINGS):
        employer = random.choice(employers)  # Assign random employer (including VamsiEmployer)

        # 🔹 Generate a detailed job description with responsibilities
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

        # 🔹 Generate structured qualifications
        qualifications = ", ".join(fake.words(nb=10))

        # 🔹 Add employer-defined application questions
        application_questions = json.dumps([
            "Why are you interested in this position?",
            "Describe a challenging project you've worked on.",
            "What relevant skills do you bring to this role?"
        ])

        job = JobPosting(
            title=fake.job(),
            location=fake.city(),
            description=description.strip(),  # Clean up formatting
            qualifications=qualifications,
            deadline=fake.date_this_year(),
            posted_by=employer.id,  # Assign job to a random employer (including VamsiEmployer)
            approved=random.choice([True, False]),  # Random approval status
            application_questions=application_questions  # Store questions as JSON
        )
        job_postings.append(job)

    # 🔹 Commit Job Postings
    db.session.bulk_save_objects(job_postings)
    db.session.commit()

    # ✅ Retrieve Committed Jobs
    all_jobs = JobPosting.query.all()

    # ✅ Generate Job Applications (Assign Some to VamsiStudent)
    applications = []
    for _ in range(NUM_APPLICATIONS):
        student = random.choice(students)  # Assign random student (including VamsiStudent)
        job = random.choice(all_jobs)

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

    # 🔹 Commit Applications
    db.session.bulk_save_objects(applications)
    db.session.commit()

    # ✅ Final Log
    print("\n✅ Successfully added:")
    print(f"  - {NUM_EMPLOYERS + 1} employers (including VamsiEmployer)")
    print(f"  - {NUM_STUDENTS + 1} students (including VamsiStudent)")
    print(f"  - {NUM_POSTINGS} job postings")
    print(f"  - {NUM_APPLICATIONS} job applications")


    
"""
🔍 All Users in Database:
👤 Username: admin, Role: admin, Email: admin@example.com, Company: N/A
👤 Username: robertgibson, Role: employer, Email: veronicarussell@example.net, Company: Liu, Gonzalez and Day
👤 Username: wturner, Role: employer, Email: asmith@example.net, Company: Atkinson, Clark and Gray
👤 Username: mahoneygail, Role: employer, Email: wilsonmichael@example.org, Company: Hunt Inc
👤 Username: madison74, Role: employer, Email: fosterbrianna@example.net, Company: Thomas, Fuentes and Fleming
👤 Username: brett53, Role: employer, Email: robin26@example.org, Company: Huynh, Rosario and Murillo
👤 Username: garrettjames, Role: employer, Email: dallison@example.net, Company: Sexton-Morgan
👤 Username: qgibbs, Role: employer, Email: carrie68@example.net, Company: Black, Russell and Weber
👤 Username: kevinmorris, Role: employer, Email: arios@example.org, Company: Mejia, Sawyer and Jones
👤 Username: jruiz, Role: employer, Email: kevincampbell@example.com, Company: Simpson-Collier
👤 Username: robertsonpamela, Role: employer, Email: jamespowell@example.org, Company: Cochran Ltd
👤 Username: bandrews, Role: student, Email: joseph17@example.com, Company: N/A
👤 Username: angelamacdonald, Role: student, Email: garciajennifer@example.com, Company: N/A
👤 Username: georgebrandon, Role: student, Email: haleykelsey@example.net, Company: N/A
👤 Username: andrewslaura, Role: student, Email: joseph41@example.org, Company: N/A
👤 Username: zimmermanjohn, Role: student, Email: amy11@example.net, Company: N/A
👤 Username: feliciagraham, Role: student, Email: sherrycox@example.net, Company: N/A
👤 Username: smithtasha, Role: student, Email: kenneth75@example.com, Company: N/A
👤 Username: jeffrey90, Role: student, Email: ericsalas@example.net, Company: N/A
👤 Username: bhickman, Role: student, Email: logan90@example.com, Company: N/A
👤 Username: bradleylaurie, Role: student, Email: nathaniel63@example.org, Company: N/A
👤 Username: carsonlisa, Role: student, Email: philip75@example.org, Company: N/A
👤 Username: kimberlyjohnson, Role: student, Email: yfoster@example.net, Company: N/A
👤 Username: benjamin10, Role: student, Email: peter91@example.org, Company: N/A
👤 Username: raymondclark, Role: student, Email: vsmith@example.net, Company: N/A
👤 Username: julie74, Role: student, Email: ntran@example.com, Company: N/A
👤 Username: jhart, Role: student, Email: smiller@example.net, Company: N/A
👤 Username: christianwalker, Role: student, Email: justin49@example.net, Company: N/A
👤 Username: banksvictor, Role: student, Email: yadams@example.net, Company: N/A
👤 Username: cking, Role: student, Email: mmeyers@example.net, Company: N/A
👤 Username: christine49, Role: student, Email: allenduane@example.org, Company: N/A
👤 Username: VamsiEmployer, Role: employer, Email: vamsi.employer@example.com, Company: Vamsi Tech Inc.
👤 Username: VamsiStudent, Role: student, Email: vamsi.student@example.com, Company: N/A
👤 Username: carterlaurie, Role: employer, Email: rmcdaniel@example.net, Company: Diaz-Johnson
👤 Username: sherrymendez, Role: employer, Email: ann22@example.org, Company: Washington Ltd
👤 Username: claudialara, Role: employer, Email: tammy77@example.org, Company: Cox and Sons
👤 Username: kennethholmes, Role: employer, Email: christina50@example.net, Company: Rodriguez, Willis and Mcclure
👤 Username: burkejulie, Role: employer, Email: watsonwilliam@example.org, Company: Knox-Rice
👤 Username: keithkelly, Role: employer, Email: douglas58@example.org, Company: Johnson-Sutton
👤 Username: bwright, Role: employer, Email: garrettcarson@example.org, Company: Soto Inc
👤 Username: ricardomartinez, Role: employer, Email: twhitaker@example.com, Company: Mcbride, Horne and Wilson
👤 Username: ramirezrobert, Role: employer, Email: melissa32@example.com, Company: Nelson-Lawrence
👤 Username: ymaxwell, Role: employer, Email: dmorris@example.com, Company: Olson Ltd
👤 Username: kcarrillo, Role: student, Email: aglover@example.com, Company: N/A
👤 Username: elizabethrodriguez, Role: student, Email: samantha90@example.com, Company: N/A
👤 Username: bward, Role: student, Email: christophercain@example.org, Company: N/A
👤 Username: cochrancynthia, Role: student, Email: amydiaz@example.org, Company: N/A
👤 Username: hawkinswayne, Role: student, Email: chapmanvincent@example.net, Company: N/A
👤 Username: jason35, Role: student, Email: robert54@example.org, Company: N/A
👤 Username: taylorshawn, Role: student, Email: jgraham@example.com, Company: N/A
👤 Username: tiffanydennis, Role: student, Email: elizabethelliott@example.net, Company: N/A
👤 Username: littlestephen, Role: student, Email: hthomas@example.org, Company: N/A
👤 Username: latoya11, Role: student, Email: charleskim@example.org, Company: N/A
👤 Username: johnsonwilliam, Role: student, Email: taylormartin@example.com, Company: N/A
👤 Username: mbrady, Role: student, Email: juanjones@example.net, Company: N/A
👤 Username: jessebradley, Role: student, Email: zanderson@example.net, Company: N/A
👤 Username: scottrhodes, Role: student, Email: schaefermaria@example.com, Company: N/A
👤 Username: mark58, Role: student, Email: joyce29@example.org, Company: N/A
👤 Username: carsongail, Role: student, Email: thompsonsamantha@example.net, Company: N/A
👤 Username: frank65, Role: student, Email: byrdpatricia@example.com, Company: N/A
👤 Username: jonesharry, Role: student, Email: sanchezmichael@example.com, Company: N/A
👤 Username: jbond, Role: student, Email: butlerkevin@example.com, Company: N/A
👤 Username: wongjames, Role: student, Email: shannon98@example.org, Company: N/A
"""