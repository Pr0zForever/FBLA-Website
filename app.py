from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from db import db  # Reuse shared db instance

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_postings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'admin123'

# Initialize Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'



# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Role: 'admin', 'employer', 'student'

@app.before_request
def create_tables():
    db.create_all()

@app.before_request
def ensure_admin_user():
    if not User.query.filter_by(username="admin").first():
        admin_user = User(
            username="admin",
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            role="admin"
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
    approved = db.Column(db.Boolean, default=False)  # New field to track approval status

    # Relationship to User table
    employer = db.relationship('User', backref='job_postings', lazy=True)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)  # Link to the job
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to the student
    cover_letter = db.Column(db.Text, nullable=False)
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

with app.app_context():
    # Check if the admin user already exists
    existing_admin = User.query.filter_by(username="admin").first()
    if existing_admin:
        print("Admin user already exists. Skipping creation.")
    else:
        # Create the admin user if it doesn't exist
        admin_user = User(
            username="admin",
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully.")


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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
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
    
    # Ensure the job exists and belongs to the logged-in employer
    job = JobPosting.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('You do not have permission to view applicants for this job.', 'error')
        return redirect(url_for('employer_dashboard'))
    
    # Get all applications for this job
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
    
    # Fetch applications submitted by the current user
    applications = JobApplication.query.filter_by(student_id=current_user.id).all()
    return render_template('student_dashboard.html', applications=applications)

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


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    if current_user.role != 'student':
        flash('Only students can apply for jobs.', 'error')
        return redirect(url_for('index'))

    job = JobPosting.query.get_or_404(job_id)

    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')

        new_application = JobApplication(
            job_id=job.id,
            student_id=current_user.id,
            cover_letter=cover_letter
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

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
