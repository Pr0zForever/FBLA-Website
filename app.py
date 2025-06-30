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
from flask_mail import Mail, Message
from flask_mail import Message as MailMessage



print(joblib.__version__)


app = Flask(__name__)

mail = Mail(app)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_postings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'admin123'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jobconnectfbla@gmail.com'
app.config['MAIL_PASSWORD'] = 'AdvayArashanapali'  # Use App Passwords if Gmail
app.config['MAIL_DEFAULT_SENDER'] = 'jobconnectfbla@gmail.com'


def send_notification_email(to_email, subject, body):
    try:
        if to_email:
            msg = Message(subject=subject, recipients=[to_email])
            msg.body = body
            mail.send(msg)
    except Exception as e:
        print(f"Email failed to send: {e}")


ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

# Initialize Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'



# Models

from db import db
from datetime import datetime
class EmployerNote(db.Model):
    __tablename__ = 'employer_note'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Add this line

    employer = db.relationship('User', foreign_keys=[employer_id])
    student = db.relationship('User', foreign_keys=[student_id])
    job = db.relationship('JobPosting', backref=db.backref('employer_notes', lazy=True))



from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Login credentials
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)

    # Roles & School
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'employer', 'student'
    approved = db.Column(db.Boolean, default=False)
    school = db.Column(db.String(120), nullable=True)

    # Profile fields
    name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic_url = db.Column(db.String(300), nullable=True)
    phone = db.Column(db.String(20), nullable=True)

    # Student-specific
    grade_level = db.Column(db.String(10), nullable=True)
    resume_link = db.Column(db.String(200), nullable=True)
    skills = db.Column(db.Text, nullable=True)

    # Employer-specific
    company_name = db.Column(db.String(100), nullable=True)
    company_website = db.Column(db.String(200), nullable=True)
    job_title = db.Column(db.String(120), nullable=True)
    request_reason = db.Column(db.Text, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'




class UserConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    requester = db.relationship('User', foreign_keys=[requester_id], backref='connections_made')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='connections_received')
   
@app.before_request
def create_tables():
    db.create_all()

from flask import request
from werkzeug.security import generate_password_hash

@app.before_request
def ensure_school_admins():
    if request.endpoint and not request.endpoint.startswith('static'):
        school_admins = [
            {
                "username": "admin_jordan",
                "password": "admin123",
                "email": "jordan_admin@example.com",
                "school": "Jordan High School"
            },

        ]

        for admin in school_admins:
            existing_admin = User.query.filter_by(username=admin["username"]).first()
            if not existing_admin:
                new_admin = User(
                    username=admin["username"],
                    password=generate_password_hash(admin["password"], method='pbkdf2:sha256'),
                    role="admin",
                    name=f"{admin['school']} Admin",
                    email=admin["email"],
                    bio=f"Administrator for {admin['school']}",
                    school=admin["school"],
                    approved=True
                )
                db.session.add(new_admin)
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
    application_questions = db.Column(db.Text, nullable=True)
    flagged = db.Column(db.Boolean, default=False)

    # 🔧 Add this line:
    school = db.Column(db.String(100), nullable=True)

    # Relationship to User table
    employer = db.relationship('User', backref='job_postings', lazy=True)
    
    def set_questions(self, questions):
        self.application_questions = json.dumps(questions)

    def get_questions(self):
        return json.loads(self.application_questions) if self.application_questions else []
    

    # Your model
class Message(db.Model):
    __tablename__ = 'user_message'  # you can keep or change this
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    resume_url = db.Column(db.String(300), nullable=True)
    resume_filename = db.Column(db.String(100), nullable=True) # ✅ Add this line
    resume_data = db.Column(db.LargeBinary, nullable=True)  # ✅ Add this line

    status = db.Column(db.String(50), default='pending')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ Add this line

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


from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    schools = ["Jordan High School", "Seven Lakes High School", "Tompkins High School"]

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        school = request.form.get('school')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'error')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        approved = role == 'student'

        # Extra fields by role
        extra_info = {}
        if role == 'student':
            grade_level = request.form.get('grade_level')
            extra_info = {
                "grade_level": grade_level
            }
        elif role == 'employer':
            org_name = request.form.get('organization_name')
            job_title = request.form.get('job_title')
            request_reason = request.form.get('request_reason')
            extra_info = {
                "organization_name": org_name,
                "job_title": job_title,
                "request_reason": request_reason
            }

        new_user = User(
            username=username,
            email=email,
            password=hashed_pw,
            role=role,
            school=school,
            approved=approved,
            full_name=full_name,
            phone=phone,
            **extra_info
        )

        db.session.add(new_user)
        db.session.commit()

        # Email
        subject = "Welcome to JobConnect"
        if role == 'student':
            body = f"Hi {full_name}, your student account has been approved!"
        else:
            body = f"Hi {full_name}, your employer request is under review by school officials."

        try:
            msg = Message(subject=subject, recipients=[email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email failed: {e}")

        flash('Account created successfully! Check your email for details.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', schools=schools)


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







class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='audit_logs')


@app.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('Access restricted to administrators only.', 'error')
        return redirect(url_for('index'))

    total_users = User.query.filter_by(school=current_user.school).count()
    total_jobs = JobPosting.query.filter_by(school=current_user.school).count()
    total_applications = JobApplication.query.join(JobPosting).filter(JobPosting.school == current_user.school).count()
    total_messages = Message.query.count()
    pending_jobs = JobPosting.query.filter_by(approved=False, school=current_user.school).all()
    recent_signups = User.query.filter_by(school=current_user.school).order_by(User.id.desc()).limit(10).all()
    results = db.session.query(JobPosting.location, db.func.count(JobPosting.id)).group_by(JobPosting.location).all()

    job_counts = {location: count for location, count in results}
    users = User.query.filter_by(school=current_user.school).all()
    email_summary = [{
        "username": user.username,
        "email": user.email,
        "role": user.role
    } for user in users]
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    flagged_jobs = JobPosting.query.filter_by(flagged=True).all()

    user_roles = db.session.query(User.role, db.func.count(User.id)).filter_by(school=current_user.school).group_by(User.role).all()
    from collections import defaultdict

    # Let's say you built it like this
    results = db.session.query(
        JobApplication.timestamp,
        db.func.count(JobApplication.id)
    ).group_by(db.func.date(JobApplication.timestamp)).all()

    # Convert it to a plain dictionary with stringified dates
    application_trends = [
        {"date": str(date), "count": count}
        for date, count in results
    ]

    unapproved_employers = User.query.filter_by(role='employer', approved=False).all()

        # Sample chart data (replace with real aggregation)
    school_labels = ['Jordan', 'Seven Lakes', 'Tompkins']
    school_applications = [45, 73, 60]

    user_growth_dates = ['2024-01', '2024-02', '2024-03', '2024-04']
    user_growth_counts = [10, 30, 80, 120]

    return render_template(
        'admin_panel.html',
        total_users=total_users,
        total_jobs=total_jobs,
        total_applications=total_applications,
        total_messages=total_messages,
        pending_jobs=pending_jobs,
        recent_signups=recent_signups,
        job_counts=job_counts,
        email_summary=email_summary,
        audit_logs=logs,
        flagged_jobs=flagged_jobs,
        user_roles=user_roles,
        application_trends=application_trends,
        school=current_user.school,
        unapproved_employers=unapproved_employers
    )


@app.route('/admin/approve-employer/<int:user_id>', methods=['POST'])
@login_required
def approve_employer(user_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)
    if user.role != 'employer':
        return jsonify({"error": "Not an employer"}), 400

    user.approved = True
    db.session.commit()

    if user.email:
        subject = "Your employer account has been approved"
        body = "You can now post jobs and interact with students on JobConnect."
        try:
            msg = Message(subject=subject, recipients=[user.email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    db.session.add(AuditLog(user_id=current_user.id, action=f"Approved employer {user.username}"))
    db.session.commit()
    return jsonify({"success": True})


@app.route('/admin/reject-employer/<int:user_id>', methods=['POST'])
@login_required
def reject_employer(user_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)
    if user.role != 'employer':
        return jsonify({"error": "Not an employer"}), 400

    user_email = user.email
    db.session.delete(user)
    db.session.commit()

    if user_email:
        subject = "Your employer account was rejected"
        body = "Your employer registration request was not approved by school officials."
        try:
            msg = Message(subject=subject, recipients=[user_email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    db.session.add(AuditLog(user_id=current_user.id, action=f"Rejected employer {user.username}"))
    db.session.commit()
    return jsonify({"success": True})

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)
    if user.school != current_user.school:
        return jsonify({"error": "You can only delete users from your school."}), 403

    user_email = user.email
    db.session.delete(user)
    db.session.commit()

    if user_email:
        subject = "Your account has been deleted"
        body = "Your JobConnect account has been removed by an administrator."
        try:
            msg = Message(subject=subject, recipients=[user_email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    db.session.add(AuditLog(user_id=current_user.id, action=f"Deleted user {user_id}"))
    db.session.commit()
    return jsonify({"success": True})


@app.route('/admin/delete-job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    job = JobPosting.query.get_or_404(job_id)
    if job.school != current_user.school:
        return jsonify({"error": "You can only delete jobs from your school."}), 403

    employer_email = job.employer.email if job.employer else None
    db.session.delete(job)
    db.session.commit()

    if employer_email:
        subject = f"Your job posting '{job.title}' was deleted"
        body = "An administrator has removed your job posting from the system."
        try:
            msg = Message(subject=subject, recipients=[employer_email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    db.session.add(AuditLog(user_id=current_user.id, action=f"Deleted job {job_id}"))
    db.session.commit()
    return jsonify({"success": True})


@app.route('/admin/update-role/<int:user_id>', methods=['POST'])
@login_required
def update_user_role(user_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    user = User.query.get_or_404(user_id)
    if user.school != current_user.school:
        return jsonify({"error": "You can only modify users from your school."}), 403

    new_role = request.json.get('role')
    if new_role not in ['admin', 'employer', 'student']:
        return jsonify({"error": "Invalid role"}), 400

    user.role = new_role
    db.session.commit()
    db.session.add(AuditLog(user_id=current_user.id, action=f"Updated user {user_id} role to {new_role}"))
    db.session.commit()
    return jsonify({"success": True, "new_role": new_role})


@app.route('/admin/send-email', methods=['POST'])
@login_required
def send_email():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    subject = data.get("subject")
    body = data.get("body")
    recipient_email = data.get("email")

    if not subject or not body or not recipient_email:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        msg = Message(subject=subject, recipients=[recipient_email], body=body)
        mail.send(msg)
        db.session.add(AuditLog(user_id=current_user.id, action=f"Sent email to {recipient_email}"))
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/admin/flag-job/<int:job_id>', methods=['POST'])
@login_required
def flag_job(job_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    job = JobPosting.query.get_or_404(job_id)
    if job.school != current_user.school:
        return jsonify({"error": "You can only flag jobs from your school."}), 403

    job.flagged = True
    db.session.commit()
    return jsonify({"success": True})


@app.route('/admin/unflag-job/<int:job_id>', methods=['POST'])
@login_required
def unflag_job(job_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    job = JobPosting.query.get_or_404(job_id)
    if job.school != current_user.school:
        return jsonify({"error": "You can only unflag jobs from your school."}), 403

    job.flagged = False
    db.session.commit()
    return jsonify({"success": True})


@app.route('/admin/flagged-jobs')
@login_required
def flagged_jobs():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    flagged_jobs = JobPosting.query.filter_by(flagged=True, school=current_user.school).all()
    return jsonify({"flagged_jobs": [job.to_dict() for job in flagged_jobs]})


@app.route('/admin/approve-job/<int:job_id>', methods=['POST'])
@login_required
def admin_approve_job(job_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    job = JobPosting.query.get_or_404(job_id)
    if job.school != current_user.school:
        return jsonify({"error": "You can only approve jobs for your school."}), 403

    job.approved = True
    db.session.commit()

    if job.employer and job.employer.email:
        subject = f"Your job posting '{job.title}' was approved"
        body = "Your job posting has been approved and is now live."
        try:
            msg = Message(subject=subject, recipients=[job.employer.email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    db.session.add(AuditLog(user_id=current_user.id, action=f"Approved job {job_id}"))
    db.session.commit()
    return jsonify({"success": True})

@app.route('/admin/reject-job/<int:job_id>', methods=['POST'])
@login_required    
def admin_reject_job(job_id):    
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    job = JobPosting.query.get_or_404(job_id)
    if job.school != current_user.school:
        return jsonify({"error": "You can only reject jobs for your school."}), 403

    job.approved = False
    db.session.commit()

    if job.employer and job.employer.email:
        subject = f"Your job posting '{job.title}' was rejected"
        body = "Your job posting has been rejected."
        try:
            msg = Message(subject=subject, recipients=[job.employer.email], body=body)
            mail.send(msg)
        except Exception as e:
            print(f"Email sending failed: {e}")

    db.session.add(AuditLog(user_id=current_user.id, action=f"Rejected job {job_id}"))
    db.session.commit()
    return jsonify({"success": True})

# Seed admin accounts for 3 schools (this should be run during initial DB seeding or Flask CLI setup)
def create_school_admins():
    from werkzeug.security import generate_password_hash
    schools = ["Jordan High School", "Seven Lakes High School", "Tompkins High School"]
    for school in schools:
        username = school.replace(" ", "_").lower() + "_admin"
        if not User.query.filter_by(username=username).first():
            admin = User(
                username=username,
                email=username + "@jobconnect.edu",
                password=generate_password_hash("admin123"),
                role="admin",
                school=school
            )
            db.session.add(admin)
    db.session.commit()
@app.route('/admin/manage-posts')
@login_required
def manage_posts():
    if current_user.role != 'admin':
        flash('Access restricted to administrators only.', 'error')
        return redirect(url_for('index'))
    
    approved_jobs = JobPosting.query.filter_by(approved=True, school=current_user.school).all()
    pending_jobs = JobPosting.query.filter_by(approved=False, school=current_user.school).all()

    return render_template('admin_manage_posts.html', approved_jobs=approved_jobs, pending_jobs=pending_jobs, school=current_user.school)


@app.route('/admin/audit-logs')
@login_required
def audit_logs_page():
    if current_user.role != 'admin':
        flash('Access restricted to administrators only.', 'error')
        return redirect(url_for('index'))

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin_audit_logs.html', logs=logs, school=current_user.school)



# Employer Dashboard Enhancements - Flask Routes

@app.route('/employer-dashboard')
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        flash('Access restricted to employers only.', 'error')
        return redirect(url_for('index'))

    job_postings = JobPosting.query.filter_by(posted_by=current_user.id).all()
    job_count = len(job_postings)
    applicant_count = sum(len(job.applications) for job in job_postings)

    connections = UserConnection.query.filter(
        (UserConnection.requester_id == current_user.id) |
        (UserConnection.recipient_id == current_user.id)
    ).all()

    connected_users = set()
    for c in connections:
        if c.requester_id == current_user.id:
            connected_users.add(c.recipient)
        else:
            connected_users.add(c.requester)

    notifications = Notification.query.filter_by(user_id=current_user.id, seen=False).all()
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).limit(10).all()

    return render_template(
        'employer_dashboard.html',
        job_postings=job_postings,
        job_count=job_count,
        applicant_count=applicant_count,
        connections=list(connected_users),
        notifications=notifications,
        messages=recent_messages
    )





@app.route('/clone-posting/<int:job_id>')
@login_required
def clone_posting(job_id):
    job = JobPosting.query.get_or_404(job_id)
    if job.posted_by != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('employer_dashboard'))

    cloned = JobPosting(
        title=job.title + " (Copy)",
        location=job.location,
        description=job.description,
        qualifications=job.qualifications,
        deadline=job.deadline,
        posted_by=current_user.id
    )
    db.session.add(cloned)
    db.session.commit()

    new_notification = Notification(user_id=current_user.id, message=f"Job '{job.title}' cloned successfully.")
    db.session.add(new_notification)
    db.session.commit()

    flash('Job cloned successfully.', 'success')
    return redirect(url_for('employer_dashboard'))

@app.route('/connect/<int:user_id>', methods=['POST'])
@login_required
def connect_user(user_id):
    if current_user.id == user_id:
        return jsonify({"error": "You cannot connect with yourself."}), 400

    existing = UserConnection.query.filter_by(
        requester_id=current_user.id,
        recipient_id=user_id
    ).first()

    if not existing:
        connection = UserConnection(requester_id=current_user.id, recipient_id=user_id)
        db.session.add(connection)
        db.session.commit()

        # Notification
        user = User.query.get(user_id)
        db.session.add(Notification(user_id=user_id, message=f"{current_user.username} has connected with you."))
        db.session.commit()

        # Email
        if user and user.email:
            send_notification_email(
                user.email,
                "New Connection",
                f"{current_user.username} has connected with you on JobConnect."
            )

        return jsonify({"success": True, "message": "Connection established."})
    else:
        return jsonify({"success": False, "message": "Already connected."})

@app.route('/disconnect/<int:user_id>', methods=['POST'])
@login_required
def disconnect_user(user_id):
    connection = UserConnection.query.filter_by(
        requester_id=current_user.id,
        recipient_id=user_id
    ).first()

    if connection:
        db.session.delete(connection)
        db.session.commit()
        return jsonify({"success": True, "message": "Connection removed."})
    else:
        return jsonify({"success": False, "message": "No connection found."})
@app.route('/stats-overview')
@login_required
def stats_overview():
    if current_user.role != 'employer':
        return jsonify({"error": "Unauthorized"}), 403

    job_postings = JobPosting.query.filter_by(posted_by=current_user.id).all()
    job_count = len(job_postings)
    applicant_count = sum(len(job.applications) for job in job_postings)
    
    return jsonify({
        "job_count": job_count,
        "applicant_count": applicant_count
    })

@app.route('/notifications/mark-seen', methods=['POST'])
@login_required
def mark_notifications_seen():
    notifications = Notification.query.filter_by(user_id=current_user.id, seen=False).all()
    for note in notifications:
        note.seen = True
    db.session.commit()
    return jsonify({"success": True})

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def __repr__(self):
        return f'<Notification for User {self.user_id}: {self.message}>'



@app.route('/view-applicants/<int:job_id>', methods=['GET'])
@login_required
def view_applicants(job_id):
    """View all applicants for a specific job posting."""
    if current_user.role != 'employer':
        flash('Access restricted to employers only.', 'error')
        return redirect(url_for('index'))

    employer_jobs = JobPosting.query.filter_by(posted_by=current_user.id).all()
    job_ids = [job.id for job in employer_jobs]

    job = JobPosting.query.get_or_404(job_id)
    if job.id not in job_ids:
        flash('You do not have permission to view applicants for this job.', 'error')
        return redirect(url_for('employer_dashboard'))
    

    applications = JobApplication.query.filter_by(job_id=job.id).all()

    # Include notes
    for app in applications:
        app.notes = EmployerNote.query.filter_by(application_id=app.id).order_by(EmployerNote.created_at.desc()).all()

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

    recommended_jobs = JobPosting.query.limit(20).all()
    applications = JobApplication.query.filter_by(user_id=current_user.id).all()

    connections = UserConnection.query.filter(
        (UserConnection.requester_id == current_user.id) |
        (UserConnection.recipient_id == current_user.id)
    ).all()

    connected_users = set()
    for c in connections:
        if c.requester_id == current_user.id:
            connected_users.add(c.recipient)
        else:
            connected_users.add(c.requester)

    notifications = Notification.query.filter_by(user_id=current_user.id, seen=False).all()
    recent_messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).limit(10).all()

    return render_template(
        'student_dashboard.html',
        applications=applications,
        recommended_jobs=recommended_jobs,
        connections=list(connected_users),
        notifications=notifications,
        messages=recent_messages
    )





@app.route('/application/<int:application_id>/update_status', methods=['POST'])
def update_application_status(application_id):
    data = request.get_json()
    status = data.get('status')

    if status not in ['accepted', 'rejected']:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    application = JobApplication.query.get_or_404(application_id)
    application.status = status.capitalize()  # Save as "Accepted" or "Rejected"
    db.session.commit()

    return jsonify({"success": True})

@app.route('/send-message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return jsonify({"error": "Missing receiver or content"}), 400

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({"error": "Recipient does not exist"}), 404

    message = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()

    return jsonify({"success": True, "message": "Message sent"})


@app.route('/messages/<int:user_id>')
@login_required
def get_conversation(user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    return jsonify([{"from": m.sender_id, "to": m.receiver_id, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in messages])

@app.route('/edit-application/<int:application_id>', methods=['GET', 'POST'])
@login_required
def edit_application(application_id):
    application = JobApplication.query.get_or_404(application_id)

    if application.user_id != current_user.id:
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
            resume_data = resume_file.read()
        elif not cover_letter:
            flash('Please provide either a cover letter or upload a file.', 'error')
            return redirect(request.url)

        new_application = JobApplication(
            job_id=job.id,
            user_id=current_user.id,
            cover_letter=cover_letter if cover_letter else None,
            resume_filename=resume_filename,
            resume_data=resume_data
        )

        db.session.add(new_application)
        db.session.commit()

        # ✅ Email notifications
        if job.employer and job.employer.email:
            send_notification_email(
                job.employer.email,
                "New Applicant",
                f"A student has applied for your job: {job.title}."
            )
        send_notification_email(
            current_user.email,
            "Application Submitted",
            f"You have successfully applied to {job.title}."
        )

        flash('Your application has been submitted!', 'success')
        return redirect(url_for('confirmation', job_title=job.title))

    return render_template('apply.html', job=job)


@app.route('/approved-postings')
def approved_postings():
    job_postings = JobPosting.query.all()
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

    new_job = JobPosting(
        title=job_title,
        location=location,
        description=description,
        qualifications=qualifications,
        deadline=deadline,
        posted_by=current_user.id
    )

    db.session.add(new_job)
    db.session.commit()

    # ✅ Send confirmation email to employer
    send_notification_email(
        current_user.email,
        "Job Submission Received",
        f"Your job '{job_title}' has been submitted and is awaiting approval."
    )

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

    results = JobPosting.query.filter(JobPosting.title.ilike(f"%{query}%")).limit(5).all()
    suggestions = [{"id": job.id, "title": job.title} for job in results]

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
        "estimated_salary": round(random.uniform(32000, 66000), 2),
        "market_growth": random.randint(23, 89),
        "market_demand": random.randint(20, 80),
        "market_salary": round(random.uniform(50000, 66000), 2),
        "market_competition": random.randint(5, 40),
        "popularity_trend": [random.randint(30, 100) for _ in range(7)],
        "insights": [
            "Tech industry jobs have grown 15% in the last year.",
            "Salaries in this sector are expected to rise by 10% in 2025."
        ]
    }

    return render_template("job_details.html", job=job, ai_insights=ai_insights, jobs=JobPosting.query.all())
    


   
@app.route("/job-predictions/<int:job_id>/<int:user_id>")
def predict_job_stats(job_id, user_id):
    print(f"🔍 Fetching AI insights for Job ID: {job_id}, User ID: {user_id}")  # Debug Log

    job = JobPosting.query.get(job_id)
    user = User.query.get(user_id)

    if not job or not user:
        print("❌ Job or User not found!")  # Debug Log
        return jsonify({"error": "Job or User not found"}), 404

    print(" Job and User found!")  # Debug Log

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
        "market_salary": round(random.uniform(50000, 66000), 2),
        "market_competition": random.randint(20, 40),
        "popularity_trend": [random.randint(30, 100) for _ in range(7)],
        "insights": [
            "Tech industry jobs have grown 15% in the last year.",
            "Salaries in this sector are expected to rise by 10% in 2025."
        ]
    }

    print(f" AI Insights Generated: {insights_data}")  # Debug Log
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


@app.route('/application/<int:application_id>/add_note', methods=['POST'])
@login_required
def add_employer_note(application_id):
    # Only allow employers
    if current_user.role != 'employer':
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json()
    note_text = data.get("note", "").strip()

    if not note_text:
        return jsonify({"success": False, "error": "Note is empty"}), 400

    # Validate application and ownership
    application = JobApplication.query.get_or_404(application_id)

    if application.job.posted_by != current_user.id:
        return jsonify({"success": False, "error": "You do not own this application"}), 403

    # Create note
    new_note = EmployerNote(
        application_id=application.id,
        employer_id=current_user.id,
        student_id=application.user_id,
        job_id=application.job_id,
        note=note_text,
        created_at=datetime.utcnow()
    )

    db.session.add(new_note)
    db.session.commit()

    return jsonify({"success": True, "note": note_text})

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/applicant/<int:application_id>')
def applicant_details(application_id):
    # Fetch application details
    application = JobApplication.query.get_or_404(application_id)

    # Ensure student data is loaded (prevents lazy loading issues)
    student = application.student  
    job = application.job  

    # Fetch employer notes for this application
    employer_notes = EmployerNote.query.filter_by(application_id=application_id).all()

    return render_template(
        "applicant_details.html",
        application=application,
        student=student,
        job=job,
        employer_notes=employer_notes
    )


import requests

@app.route("/ai-overview/<int:application_id>")
def ai_overview(application_id):
    application = JobApplication.query.get_or_404(application_id)
    text = f"Cover Letter: {application.cover_letter or ''}\nSkills: {application.student.skills or ''}"
    ai_response = get_llama_ai_overview(text)
    return jsonify(ai_response)


@app.route('/chat', methods=['POST'])
def chat():
    user_prompt = request.json.get("prompt", "")
    def generate():
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.2:1b", "prompt": user_prompt, "stream": True},
            stream=True
        )
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode('utf-8'))
                yield chunk['response']

    return Response(stream_with_context(generate()), content_type='text/plain')
from flask import Response, stream_with_context




if __name__ == "__main__":
    app.run(debug=True)




if __name__ == '__main__':
    app.run(debug=True)
