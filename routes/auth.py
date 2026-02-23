from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from models.database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if role == 'admin':
            flash('Admin registration not allowed')
            return redirect(url_for('auth.register'))
        
        db = get_db()
        
        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            flash('Email already registered')
            return redirect(url_for('auth.register'))
        
        hashed_password = generate_password_hash(password)
        cursor = db.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                          (email, hashed_password, role))
        user_id = cursor.lastrowid
        
        if role == 'student':
            db.execute('INSERT INTO students (user_id, name, roll_number, branch, cgpa, contact) VALUES (?, ?, ?, ?, ?, ?)',
                      (user_id, request.form['name'], request.form['roll_number'], 
                       request.form['branch'], request.form['cgpa'], request.form.get('contact', '')))
        elif role == 'company':
            db.execute('INSERT INTO companies (user_id, name, description, hr_contact, website) VALUES (?, ?, ?, ?, ?)',
                      (user_id, request.form['company_name'], request.form.get('description', ''),
                       request.form.get('hr_contact', ''), request.form.get('website', '')))
        
        db.commit()
        flash('Registration successful. Please wait for admin approval.' if role == 'company' else 'Registration successful')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            if user['is_blacklisted']:
                flash('Account is blacklisted')
                return redirect(url_for('auth.login'))
            
            if user['role'] == 'company':
                company = db.execute('SELECT status FROM companies WHERE user_id = ?', (user['id'],)).fetchone()
                if company['status'] != 'approved':
                    flash('Company not approved yet')
                    return redirect(url_for('auth.login'))
            
            session['user_id'] = user['id']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'company':
                return redirect(url_for('company.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        
        flash('Invalid credentials')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))
