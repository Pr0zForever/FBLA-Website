from app import app, db
from app import JobPosting, JobApplication, User

# Enable Flask app context for database queries
with app.app_context():


    # 🔎 Fetch all employers
    employers = User.query.filter_by(role="employer").all()
    print(f"📢 Found {len(employers)} employers")
    
    for employer in employers:
        print(f"👤 Employer: {employer.username} (ID: {employer.id})")

        # 🔎 Get all jobs posted by this employer
        employer_jobs = JobPosting.query.filter_by(posted_by=employer.id).all()
        print(f"📌 Jobs posted by {employer.username}: {[job.id for job in employer_jobs]}")

        for job in employer_jobs:
            print(f"🔹 Job ID: {job.id}, Title: {job.title}")

            # 🔎 Get applicants for each job
            applications = JobApplication.query.filter_by(job_id=job.id).all()
            print(f"📝 Applicants for Job {job.id}: {len(applications)}")

            for application in applications:
                student = User.query.get(application.student_id)
                print(f"    ✅ Student: {student.username}, Applied with Resume: {bool(application.resume_filename)}")

    print("✅ Test completed!")
