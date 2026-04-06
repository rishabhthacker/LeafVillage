from flask import Flask, Blueprint, flash, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # Create the Flask app instance
app.secret_key = "your_secret_key"  # Set a secret key for session management

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Rudra28@localhost/your_database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)  # Initialize the database

# Define the models
class HeadAdmin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Subadmin(db.Model):
    __tablename__ = 'subadmins'  # Match this to your database table name
    subadmin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Create the database tables (run this once to initialize the table)
with app.app_context():
    db.create_all()

# Define Blueprint for HeadAdmin routes
headadmin_bp = Blueprint('headadmin', __name__, template_folder='templates')

@headadmin_bp.route('/headadmin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Query the database for the admin
        admin = HeadAdmin.query.filter_by(email=email, password=password).first()
        if admin:
            session['headadmin'] = admin.email
            return redirect('/headadmin/dashboard')
        flash("Invalid Credentials", "danger")
        return redirect('/headadmin/login')
    return render_template('headadmin_login.html')

@headadmin_bp.route('/headadmin/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Check if the email already exists
        existing_admin = HeadAdmin.query.filter_by(email=email).first()
        if existing_admin:
            flash("Email already registered", "danger")
            return redirect('/headadmin/register')
        # Add the new headadmin to the database
        new_admin = HeadAdmin(username=username, email=email, password=password)
        db.session.add(new_admin)
        db.session.commit()
        flash("Registration successful!", "success")
        return redirect('/headadmin/login')
    return render_template('headadmin_register.html')

@headadmin_bp.route('/headadmin/dashboard')
def dashboard():
    if 'headadmin' not in session:
        return redirect('/headadmin/login')
    return render_template('headadmin_dashboard.html')

@headadmin_bp.route('/headadmin/users')
def manage_users():
    if 'headadmin' not in session:
        return redirect('/headadmin/login')
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@headadmin_bp.route('/headadmin/subadmins')
def manage_subadmins():
    if 'headadmin' not in session:
        return redirect('/headadmin/login')
    subadmins = Subadmin.query.all()  # Fetch all subadmins
    return render_template('manage_subadmins.html', subadmins=subadmins)

@headadmin_bp.route('/headadmin/logout')
def logout():
    session.pop('headadmin', None)
    return redirect('/headadmin/login')

# Register the Blueprint with the Flask app
app.register_blueprint(headadmin_bp)

if __name__ == "__main__":
    app.run(debug=True)
