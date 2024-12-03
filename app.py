from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_postings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Role: 'admin', 'employer', or 'student'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Predefined admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = generate_password_hash("admin123", method="pbkdf2:sha256")
# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')  # 'employer' or 'student'

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Admin login
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD, password):
            admin_user = User(username=ADMIN_USERNAME, password="", role="admin")
            login_user(admin_user)
            return redirect(url_for('admin_panel'))

        # Regular user login
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for(f"{user.role}_dashboard"))

        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Admin Panel
@app.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('admin_panel.html')

# Employer Dashboard
@app.route('/employer-dashboard')
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    return render_template('employer_dashboard.html')

# Student Dashboard
@app.route('/student-dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    return render_template('student_dashboard.html')

# Job Posting Model
class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.String(50), nullable=False)

# Submit Postings
@app.route('/submit-postings', methods=['GET', 'POST'])
def submit_posting():
    if request.method == 'POST':
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
            deadline=deadline
        )
        db.session.add(new_job)
        db.session.commit()
        return redirect(url_for('confirmation', job_title=job_title))

    return render_template('submit_postings.html')

# Confirmation Page
@app.route('/confirmation')
def confirmation():
    job_title = request.args.get('job_title', 'Your job posting')
    return render_template('confirmation.html', job_title=job_title)

# Approved Postings
@app.route('/approved-postings')
def approved_postings():
    job_postings = JobPosting.query.all()
    return render_template('approved_postings.html', job_postings=job_postings)

# Create tables
with app.app_context():
    db.create_all()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
