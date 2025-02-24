from app import app, db  # Import your Flask app instance

with app.app_context():
    engine = db.engine
    inspector = db.inspect(engine)
    
    print("Existing Tables in Database:")
    print(inspector.get_table_names())  # Should include 'job_posting'
