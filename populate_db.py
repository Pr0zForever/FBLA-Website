from faker import Faker
from db import db
from app import app, JobPosting, User
import random

# Initialize Faker
fake = Faker()

# Number of job postings to generate
NUM_POSTINGS = 100

# Ensure we run in the app context
with app.app_context():
    # Ensure at least one employer exists before adding job postings
    employer = User.query.filter_by(role="employer").first()
    if not employer:
        employer = User(username="test_employer", password="test123", role="employer")
        db.session.add(employer)
        db.session.commit()

    # Generate job postings
    job_postings = []
    for _ in range(NUM_POSTINGS):
        job = JobPosting(
            title=fake.job(),
            location=fake.city(),
            description=fake.paragraph(nb_sentences=3),
            qualifications=fake.sentence(nb_words=8),
            deadline=fake.date_this_year(),
            posted_by=employer.id,  # Assign jobs to the test employer
            approved=random.choice([True, False])  # Randomly approve some jobs
        )
        job_postings.append(job)

    # Add to database
    db.session.bulk_save_objects(job_postings)
    db.session.commit()

    print(f"✅ Successfully added {NUM_POSTINGS} job postings to the database!")
