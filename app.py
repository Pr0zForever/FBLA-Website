import random
from flask import Flask, flash, json, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from db import db  # Reuse shared db instance
from flask import Flask, jsonify, request
import joblib
import os
from flask import flash, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
print(joblib.__version__)


app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_postings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'admin123'


ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

# Initialize Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'



# Models

from db import db

class EmployerNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)  # ✅ Ensure ForeignKey exists
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    employer = db.relationship('User', foreign_keys=[employer_id])
    student = db.relationship('User', foreign_keys=[student_id])
    job = db.relationship('JobPosting', backref=db.backref('employer_notes', lazy=True))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Role: 'admin', 'employer', 'student'

    # New Profile Fields
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)

    # Fields for Employers
    company_name = db.Column(db.String(100), nullable=True)
    company_website = db.Column(db.String(200), nullable=True)

    # Fields for Students
    resume_link = db.Column(db.String(200), nullable=True)
    skills = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'
    
@app.before_request
def create_tables():
    db.create_all()

@app.before_request
def ensure_admin_user():
    existing_admin = User.query.filter_by(username="admin").first()
    if not existing_admin:
        admin_user = User(
            username="admin",
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            role="admin",
            name="Admin",  # Add name field
            email="admin@example.com",  # Add email field
            bio="Administrator account",  # Add bio field
            company_name=None,  # No company for admin
            company_website=None,
            resume_link=None,
            skills=None
        )
        db.session.add(admin_user)
        db.session.commit()

class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.String(50), nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved = db.Column(db.Boolean, default=False)
    
    # ✅ Add this missing column for application questions
    application_questions = db.Column(db.Text, nullable=True)

    # Relationship to User table
    employer = db.relationship('User', backref='job_postings', lazy=True)
    def set_questions(self, questions):
        """Save questions as a JSON string."""
        self.application_questions = json.dumps(questions)

    def get_questions(self):
        """Retrieve questions as a Python list."""
        return json.loads(self.application_questions) if self.application_questions else []

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    resume_data = db.Column(db.LargeBinary, nullable=True)  # Store the file as binary
    resume_filename = db.Column(db.String(255), nullable=True)  # Keep the filename
    created_at = db.Column(db.DateTime, default=db.func.now())

    # Relationships for easier access
    job = db.relationship('JobPosting', backref='applications', lazy=True)
    student = db.relationship('User', backref='applications', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        print("Debug: Received user_id=None in load_user function")
        return None  # Return None if user_id is invalid
    try:
        return User.query.get(int(user_id))
    except ValueError:
        print(f"Debug: Invalid user_id={user_id}")
        return None


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')  # 'employer' or 'student'

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_panel'))
            elif user.role == 'employer':
                return redirect(url_for('employer_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))

        flash('Invalid credentials', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/profile/<username>')
@login_required
def profile(username):
    """View profile of an employer or student."""
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Allow users to edit their profile."""
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')
        current_user.bio = request.form.get('bio')

        if current_user.role == 'employer':
            current_user.company_name = request.form.get('company_name')
            current_user.company_website = request.form.get('company_website')

        elif current_user.role == 'student':
            current_user.resume_link = request.form.get('resume_link')
            current_user.skills = request.form.get('skills')

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile', username=current_user.username))

    return render_template('edit_profile.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    """Log the user out and only show 'You have been logged out' message."""
    session.pop('_flashes', None)  # Clear all previous flash messages
    logout_user()
    flash('You have been logged out.', 'success')  # Only keep this message
    return redirect(url_for('login'))


@app.route('/admin-panel', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash("Access restricted to administrators only.", "error")
        return redirect(url_for('index'))

    unapproved_jobs = JobPosting.query.filter_by(approved=False).all()
    approved_jobs = JobPosting.query.filter_by(approved=True).all()

    return render_template('admin_panel.html', unapproved_jobs=unapproved_jobs, approved_jobs=approved_jobs)

@app.route('/approve-posting/<int:job_id>', methods=['POST'])
@login_required
def approve_posting(job_id):
    if current_user.role != 'admin':
        flash("Access restricted.", "error")
        return redirect(url_for('index'))

    job = JobPosting.query.get_or_404(job_id)
    job.approved = True
    db.session.commit()
    flash("Job posting approved successfully.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/employer-dashboard')
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        flash('Access restricted to employers only.', 'error')
        return redirect(url_for('index'))

    job_postings = JobPosting.query.filter_by(posted_by=current_user.id).all()
    return render_template('employer_dashboard.html', job_postings=job_postings)

@app.route('/view-applicants/<int:job_id>', methods=['GET'])
@login_required
def view_applicants(job_id):
    """View all applicants for a specific job posting."""
    if current_user.role != 'employer':
        flash('Access restricted to employers only.', 'error')
        return redirect(url_for('index'))
    
    # ✅ Get all jobs owned by the employer
    employer_jobs = JobPosting.query.filter_by(posted_by=current_user.id).all()
    job_ids = [job.id for job in employer_jobs]

    # ✅ Ensure job exists & belongs to employer
    job = JobPosting.query.get_or_404(job_id)
    if job.id not in job_ids:
        flash('You do not have permission to view applicants for this job.', 'error')
        return redirect(url_for('employer_dashboard'))
    
    # ✅ Retrieve applications
    applications = JobApplication.query.filter_by(job_id=job.id).all()

    return render_template('view_applicants.html', job=job, applications=applications)

@app.route('/edit-posting/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_posting(job_id):
    """Allows the employer to edit their own job posting."""
    if current_user.role != 'employer':
        flash('Access restricted to employers only.', 'error')
        return redirect(url_for('index'))

    job = JobPosting.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('You are not authorized to edit this job posting.', 'error')
        return redirect(url_for('employer_dashboard'))

    if request.method == 'POST':
        job.title = request.form.get('title')
        job.location = request.form.get('location')
        job.description = request.form.get('description')
        job.qualifications = request.form.get('qualifications')
        job.deadline = request.form.get('deadline')

        db.session.commit()
        flash('Job posting updated successfully!', 'success')
        return redirect(url_for('employer_dashboard'))

    return render_template('edit_posting.html', job=job)


@app.route('/delete-posting/<int:job_id>', methods=['POST'])
@login_required
def delete_posting(job_id):
    if current_user.role != 'employer':
        flash('Access restricted.', 'error')
        return redirect(url_for('index'))

    job = JobPosting.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('You are not authorized to delete this posting.', 'error')
        return redirect(url_for('employer_dashboard'))

    db.session.delete(job)
    db.session.commit()
    flash('Job posting deleted successfully.', 'success')
    return redirect(url_for('employer_dashboard'))

@app.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access restricted to students only.', 'error')
        return redirect(url_for('index'))

    # Fetch recommended jobs (e.g., latest approved jobs)
    recommended_jobs = JobPosting.query.filter_by(approved=True).order_by(JobPosting.id.desc()).limit(20).all()

    # Fetch applications submitted by the current user
    applications = JobApplication.query.filter_by(student_id=current_user.id).all()
    
    return render_template('student_dashboard.html', applications=applications, recommended_jobs=recommended_jobs)


@app.route('/edit-application/<int:application_id>', methods=['GET', 'POST'])
@login_required
def edit_application(application_id):
    application = JobApplication.query.get_or_404(application_id)

    if application.student_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        application.cover_letter = request.form.get('cover_letter')
        db.session.commit()
        flash('Application updated successfully!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('edit_application.html', application=application)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    if current_user.role != 'student':
        flash('Only students can apply for jobs.', 'error')
        return redirect(url_for('index'))

    job = JobPosting.query.get_or_404(job_id)

    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        resume_file = request.files.get('resume_upload')

        resume_data = None
        resume_filename = None

        if resume_file and allowed_file(resume_file.filename):
            resume_filename = secure_filename(resume_file.filename)
            resume_data = resume_file.read()  # Store file content as binary

        elif not cover_letter:
            flash('Please provide either a cover letter or upload a file.', 'error')
            return redirect(request.url)

        new_application = JobApplication(
            job_id=job.id,
            student_id=current_user.id,
            cover_letter=cover_letter if cover_letter else None,
            resume_filename=resume_filename,  # Store the filename
            resume_data=resume_data  # Store the actual file content
        )

        db.session.add(new_application)
        db.session.commit()

        flash('Your application has been submitted!', 'success')
        return redirect(url_for('confirmation', job_title=job.title))

    return render_template('apply.html', job=job)

@app.route('/approved-postings')
def approved_postings():
    job_postings = JobPosting.query.filter_by(approved=True).all()
    return render_template('approved_postings.html', job_postings=job_postings)

@app.route('/reject-applicant/<int:applicant_id>', methods=['POST'])
@login_required
def reject_applicant(applicant_id):
    """Allow employers to reject an applicant."""
    if current_user.role != 'employer':
        flash('Access restricted.', 'error')
        return redirect(url_for('index'))

    application = JobApplication.query.get_or_404(applicant_id)

    # Ensure the employer owns the job posting
    if application.job.posted_by != current_user.id:
        flash('You are not authorized to reject this applicant.', 'error')
        return redirect(url_for('employer_dashboard'))

    db.session.delete(application)
    db.session.commit()

    flash('Applicant has been rejected successfully.', 'success')
    return redirect(url_for('view_applicants', job_id=application.job_id))


@app.route('/confirmation')
def confirmation():
    job_title = request.args.get('job_title', 'Your job posting')
    return render_template('confirmation.html', job_title=job_title)

@app.route('/submit-postings', methods=['POST'])
@login_required
def submit_posting():
    if current_user.role != 'employer':
        flash('Only employers can submit job postings.', 'error')
        return redirect(url_for('index'))

    job_title = request.form.get('title')
    location = request.form.get('location')
    description = request.form.get('description')
    qualifications = request.form.get('qualifications')
    deadline = request.form.get('deadline')

    # Ensure current_user.id is passed to posted_by
    new_job = JobPosting(
        title=job_title,
        location=location,
        description=description,
        qualifications=qualifications,
        deadline=deadline,
        posted_by=current_user.id  # Assign the logged-in employer's ID
    )

    db.session.add(new_job)
    db.session.commit()

    flash('Job posting submitted successfully.', 'success')
    return redirect(url_for('employer_dashboard'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    
    if not query:
        flash("Please enter a search term.", "error")
        return redirect(url_for('index'))

    # Search for jobs matching the query in title or description
    job_results = JobPosting.query.filter(
        (JobPosting.title.ilike(f"%{query}%")) | (JobPosting.description.ilike(f"%{query}%"))
    ).all()

    # Search for employers and students
    user_results = User.query.filter(
        (User.username.ilike(f"%{query}%")) | (User.company_name.ilike(f"%{query}%")) | (User.skills.ilike(f"%{query}%"))
    ).all()

    return render_template('search_results.html', query=query, job_results=job_results, user_results=user_results)




@app.route("/search-suggestions")
def search_suggestions():
    query = request.args.get("q", "").lower()

    if not query:
        return jsonify({"suggestions": []})

    # Search for jobs that match the query (basic case-insensitive match)
    results = JobPosting.query.filter(JobPosting.title.ilike(f"%{query}%")).limit(5).all()
    
    # Extract job titles from search results
    suggestions = [job.title for job in results]

    return jsonify({"suggestions": suggestions})

@app.route('/popular-jobs')
def popular_jobs():
    # Fetch 5 most recent approved job postings
    jobs = JobPosting.query.filter_by(approved=True).order_by(JobPosting.id.desc()).limit(5).all()
    
    job_titles = [job.title for job in jobs]

# Load trained models (Placeholder for now)
relevance_model = joblib.load('models/job_relevance_model.pkl')
acceptance_model = joblib.load('models/acceptance_model.pkl')
salary_model = joblib.load('models/salary_model.pkl')
label_enc = joblib.load('models/label_encoder.pkl')

@app.route("/job/<int:job_id>")
def job_details(job_id):
    job = JobPosting.query.get(job_id)

    if not job:
        return "Job not found", 404

    # Fetch related jobs (same city or similar title)
    related_jobs = JobPosting.query.filter(
        (JobPosting.location == job.location) | (JobPosting.title.like(f"%{job.title[:5]}%"))
    ).limit(5).all()

    recommended_jobs = JobPosting.query.order_by(db.func.random()).limit(5).all()
    # Fetch previous applications for this job
    previous_applications = JobApplication.query.filter_by(job_id=job_id).all()

    # Generate AI insights (Replace with actual AI model predictions if available)
    ai_insights = {
        "relevance_score": round(random.uniform(50, 95), 2),
        "acceptance_chance": round(random.uniform(30, 80), 2),
        "estimated_salary": round(random.uniform(60000, 120000), 2),
        "market_growth": random.randint(23, 89),
        "market_demand": random.randint(20, 80),
        "market_salary": round(random.uniform(50000, 110000), 2),
        "market_competition": random.randint(5, 40),
        "popularity_trend": [random.randint(30, 100) for _ in range(7)],
        "insights": [
            "Tech industry jobs have grown 15% in the last year.",
            "Salaries in this sector are expected to rise by 10% in 2025."
        ]
    }

    return render_template("job_details.html", job=job, ai_insights=ai_insights, recommended_jobs=recommended_jobs)


   
@app.route("/job-predictions/<int:job_id>/<int:user_id>")
def predict_job_stats(job_id, user_id):
    print(f"🔍 Fetching AI insights for Job ID: {job_id}, User ID: {user_id}")  # Debug Log

    job = JobPosting.query.get(job_id)
    user = User.query.get(user_id)

    if not job or not user:
        print("❌ Job or User not found!")  # Debug Log
        return jsonify({"error": "Job or User not found"}), 404

    print("✅ Job and User found!")  # Debug Log

    # Placeholder values for now
    insights_data = {
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company_name if hasattr(job, "company_name") else "Unknown Company",
        "location": job.location,
        "description": job.description,
        "estimated_salary": round(random.uniform(60000, 120000), 2),
        "relevance_score": round(random.uniform(50, 95), 2),
        "acceptance_chance": round(random.uniform(30, 80), 2),
        "market_growth": random.randint(30, 50),
        "market_demand": random.randint(60, 80),
        "market_salary": round(random.uniform(50000, 110000), 2),
        "market_competition": random.randint(20, 40),
        "popularity_trend": [random.randint(30, 100) for _ in range(7)],
        "insights": [
            "Tech industry jobs have grown 15% in the last year.",
            "Salaries in this sector are expected to rise by 10% in 2025."
        ]
    }

    print(f"📊 AI Insights Generated: {insights_data}")  # Debug Log
    return jsonify(insights_data)
@app.route("/api/more-jobs")
def more_jobs():
    more_jobs = JobPosting.query.filter_by(approved=True).order_by(db.func.random()).limit(3).all()
    return jsonify([{"title": job.title, "company": job.employer.name if job.employer else "Unknown", "location": job.location} for job in more_jobs])

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'employer':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        location = request.form.get('location')
        description = request.form.get('description')
        qualifications = request.form.get('qualifications')
        deadline = request.form.get('deadline')
        questions = request.form.getlist('questions[]')  # Get all custom questions

        new_job = JobPosting(
            title=title,
            location=location,
            description=description,
            qualifications=qualifications,
            deadline=deadline,
            posted_by=current_user.id
        )
        new_job.set_questions(questions)  # Store questions in JSON format

        db.session.add(new_job)
        db.session.commit()

        flash('Job posting submitted successfully!', 'success')
        return redirect(url_for('employer_dashboard'))

    return render_template('post_job.html')

@app.route('/applicant-details/<int:application_id>')
@login_required
def applicant_details(application_id):
    """View detailed information about an applicant"""
    if current_user.role != 'employer':
        flash("Access restricted to employers only.", "error")
        return redirect(url_for('index'))

    application = JobApplication.query.get_or_404(application_id)

    # Ensure that the employer owns the job posting
    if application.job.posted_by != current_user.id:
        flash("You are not authorized to view this applicant.", "error")
        return redirect(url_for('employer_dashboard'))

    # AI Insights (Placeholder for now)
    ai_insights = {
        "market_growth": 75,
        "market_demand": 80,
        "relevance_score": 70,
        "acceptance_chance": 65,
    }

    # Fetch employer notes for this applicant
    notes = EmployerNote.query.filter_by(application_id=application_id).all()

    return render_template('applicant_details.html', application=application, ai_insights=ai_insights, notes=notes)




@app.route('/application/<int:application_id>')
def application_details(application_id):
    application = JobApplication.query.get_or_404(application_id)
    employer_notes = EmployerNote.query.filter_by(application_id=application_id).order_by(EmployerNote.created_at.desc()).all()

    return render_template('application_details.html', application=application, employer_notes=employer_notes)

@app.route('/add_employer_note/<int:application_id>', methods=['POST'])
def add_employer_note(application_id):
    note_text = request.form.get('note')

    if note_text:
        new_note = EmployerNote(
            application_id=application_id,
            employer_id=1,  # Replace with `current_user.id` if using authentication
            student_id=JobApplication.query.get(application_id).student_id,
            job_id=JobApplication.query.get(application_id).job_id,
            note=note_text,
            created_at=datetime.utcnow()
        )

        db.session.add(new_note)
        db.session.commit()

    return redirect(url_for('application_details', application_id=application_id))

@app.route('/download-resume/<int:application_id>')
@login_required
def download_resume(application_id):
    application = JobApplication.query.get_or_404(application_id)

    if not application.resume_data:
        flash('No resume found for this application.', 'error')
        return redirect(url_for('index'))

    return send_file(
        BytesIO(application.resume_data),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=application.resume_filename
    )

@app.route('/application/<int:application_id>')
def application_details(application_id):
    application = JobApplication.query.get_or_404(application_id)
    employer_notes = EmployerNote.query.filter_by(application_id=application_id).order_by(EmployerNote.created_at.desc()).all()

    return render_template('application_details.html', application=application, employer_notes=employer_notes)

@app.route('/application/<int:application_id>/add_note', methods=['POST'])
def add_employer_note(application_id):
    data = request.json
    note_text = data.get("note", "").strip()

    if note_text:
        new_note = EmployerNote(
            application_id=application_id,
            employer_id=1,  # Replace with `current_user.id` if using authentication
            student_id=JobApplication.query.get(application_id).student_id,
            job_id=JobApplication.query.get(application_id).job_id,
            note=note_text,
            created_at=datetime.utcnow()
        )

        db.session.add(new_note)
        db.session.commit()

        return jsonify({"success": True, "note": note_text})

    return jsonify({"success": False}), 400

@app.route('/about')
def about():
    return render_template('about.html')



if __name__ == '__main__':
    app.run(debug=True)
