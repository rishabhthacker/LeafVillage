from flask import Blueprint, render_template, request, redirect, url_for, session

headadmin_bp = Blueprint('headadmin', __name__, template_folder='templates')

# In-memory mock database for demonstration
headadmins = []

@headadmin_bp.route('/headadmin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        for admin in headadmins:
            if admin['email'] == email and admin['password'] == password:
                session['headadmin'] = email
                return redirect('/headadmin/dashboard')
        return "Invalid Credentials"
    return render_template('headadmin_login.html')

@headadmin_bp.route('/headadmin/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        headadmins.append({'username': username, 'email': email, 'password': password})
        return redirect('/headadmin/login')
    return render_template('headadmin_register.html')

@headadmin_bp.route('/headadmin/dashboard')
def dashboard():
    if 'headadmin' not in session:
        return redirect('/headadmin/login')
    return render_template('headadmin_dashboard.html')

@headadmin_bp.route('/headadmin/logout')
def logout():
    session.pop('headadmin', None)
    return redirect('/headadmin/login')
