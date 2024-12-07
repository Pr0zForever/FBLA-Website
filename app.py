from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate


app = Flask(__name__)
app.secret_key = 'monkey'

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///job_postings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECRET_KEY'] = 'admin123'


login_manager = LoginManager(app)
login_manager.login_view = 'login'
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)
# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # Role: 'admin', 'employer', or 'student'

@login_manager.user_loader
def load_user(user_id):
    if not user_id:
        return None
    return User.query.get(int(user_id))


# Predefined admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # Ideally, use an environment variable for this


# User Registration
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



# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check for admin credentials
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
            if not admin_user:
                # Create admin user if not already in the database
                admin_user = User(
                    username=ADMIN_USERNAME,
                    password=generate_password_hash(ADMIN_PASSWORD, method='pbkdf2:sha256'),
                    role="admin"
                )
                db.session.add(admin_user)
                db.session.commit()

            login_user(admin_user)
            return redirect(url_for('admin_panel'))


        # Authenticate regular users
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'employer':
                return redirect(url_for('employer_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))

        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

# Logout
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

@app.route('/employer-dashboard')
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        flash('Access restricted to employers only.', 'error')
        return redirect(url_for('index'))
    
    # Fetch job postings by the logged-in employer
    job_postings = JobPosting.query.filter_by(posted_by=current_user.id).all()
    return render_template('employer_dashboard.html', job_postings=job_postings)

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
    
    # Fetch job postings from the database
    job_postings = JobPosting.query.all()
    return render_template('student_dashboard.html', job_postings=job_postings)



# Define a model for Job Postings
class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.String(50), nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key

    # Relationship to User table
    employer = db.relationship('User', backref='job_postings', lazy=True)

# Create the database tables (run this only once or when the schema changes)
@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-posting', methods=['POST'])
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

@app.route('/confirmation')
def confirmation():
    job_title = request.args.get('job_title', 'Your job posting')
    return render_template('confirmation.html', job_title=job_title)

# Approved Postings Page Route
@app.route('/approved-postings')
def approved_postings():
    job_postings = JobPosting.query.all()
    return render_template('approved_postings.html', job_postings=job_postings)
 
    
@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply(job_id):
    if current_user.role != 'student':
        flash('Only students can apply for jobs.', 'error')
        return redirect(url_for('index'))
    
    # Fetch the job posting
    job = JobPosting.query.get_or_404(job_id)

    if request.method == 'POST':
        # Logic to handle the job application
        flash(f'You have successfully applied for the job: {job.title}', 'success')
        return redirect(url_for('student-dashboard'))
    
    return render_template('apply.html', job=job)

@app.route('/about')
def about():
    return render_template('about.html')




if __name__ == '__main__':
    app.run(debug=True)
