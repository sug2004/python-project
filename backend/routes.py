from flask import render_template, request, redirect, url_for, session, flash
from app import app
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = '../frontend/static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        if role == 'admin':
            flash('Admin registration not allowed')
            return redirect(url_for('register'))
        
        db = get_db()
        
        if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            flash('Email already registered')
            return redirect(url_for('register'))
        
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
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            if user['is_blacklisted']:
                flash('Account is blacklisted')
                return redirect(url_for('login'))
            
            if user['role'] == 'company':
                company = db.execute('SELECT status FROM companies WHERE user_id = ?', (user['id'],)).fetchone()
                if company['status'] != 'approved':
                    flash('Company not approved yet')
                    return redirect(url_for('login'))
            
            session['user_id'] = user['id']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'company':
                return redirect(url_for('company_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    total_students = db.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    total_companies = db.execute('SELECT COUNT(*) as count FROM companies').fetchone()['count']
    total_drives = db.execute('SELECT COUNT(*) as count FROM drives').fetchone()['count']
    total_applications = db.execute('SELECT COUNT(*) as count FROM applications').fetchone()['count']
    pending_companies = db.execute('SELECT c.*, u.email FROM companies c JOIN users u ON c.user_id = u.id WHERE c.status = "pending"').fetchall()
    pending_drives = db.execute('SELECT d.*, c.name as company_name FROM drives d JOIN companies c ON d.company_id = c.id WHERE d.status = "pending"').fetchall()
    
    return render_template('admin_dashboard.html', 
                         total_students=total_students,
                         total_companies=total_companies,
                         total_drives=total_drives,
                         total_applications=total_applications,
                         pending_companies=pending_companies,
                         pending_drives=pending_drives)

@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    drives = db.execute('''SELECT d.*, COUNT(a.id) as applicant_count 
                          FROM drives d 
                          LEFT JOIN applications a ON d.id = a.drive_id 
                          WHERE d.company_id = ? 
                          GROUP BY d.id''', (company['id'],)).fetchall()
    return render_template('company_dashboard.html', company=company, drives=drives)

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    drives = db.execute('''SELECT d.*, c.name as company_name, 
                          (SELECT id FROM applications WHERE student_id = ? AND drive_id = d.id) as applied 
                          FROM drives d 
                          JOIN companies c ON d.company_id = c.id 
                          WHERE c.status = "approved" AND d.status = "approved"''', (student['id'],)).fetchall()
    applications = db.execute('''SELECT a.*, d.title, c.name as company_name 
                                FROM applications a 
                                JOIN drives d ON a.drive_id = d.id 
                                JOIN companies c ON d.company_id = c.id 
                                WHERE a.student_id = ?''', (student['id'],)).fetchall()
    return render_template('student_dashboard.html', student=student, drives=drives, applications=applications)


@app.route('/admin/approve_company/<int:company_id>')
def approve_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE companies SET status = "approved" WHERE id = ?', (company_id,))
    db.commit()
    flash('Company approved')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_company/<int:company_id>')
def reject_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE companies SET status = "rejected" WHERE id = ?', (company_id,))
    db.commit()
    flash('Company rejected')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_drive/<int:drive_id>')
def approve_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE drives SET status = "approved" WHERE id = ?', (drive_id,))
    db.commit()
    flash('Drive approved')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_drive/<int:drive_id>')
def reject_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE drives SET status = "rejected" WHERE id = ?', (drive_id,))
    db.commit()
    flash('Drive rejected')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/students')
def admin_students():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    search = request.args.get('search', '')
    if search:
        students = db.execute('''SELECT s.*, u.email, u.is_blacklisted 
                                FROM students s 
                                JOIN users u ON s.user_id = u.id 
                                WHERE s.name LIKE ? OR s.roll_number LIKE ? OR s.contact LIKE ?''',
                            (f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        students = db.execute('SELECT s.*, u.email, u.is_blacklisted FROM students s JOIN users u ON s.user_id = u.id').fetchall()
    return render_template('admin_students.html', students=students, search=search)

@app.route('/admin/companies')
def admin_companies():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    search = request.args.get('search', '')
    if search:
        companies = db.execute('''SELECT c.*, u.email, u.is_blacklisted 
                                 FROM companies c 
                                 JOIN users u ON c.user_id = u.id 
                                 WHERE c.name LIKE ?''', (f'%{search}%',)).fetchall()
    else:
        companies = db.execute('SELECT c.*, u.email, u.is_blacklisted FROM companies c JOIN users u ON c.user_id = u.id').fetchall()
    return render_template('admin_companies.html', companies=companies, search=search)

@app.route('/admin/blacklist/<int:user_id>')
def blacklist_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE users SET is_blacklisted = 1 WHERE id = ?', (user_id,))
    db.commit()
    flash('User blacklisted')
    return redirect(request.referrer)

@app.route('/admin/unblacklist/<int:user_id>')
def unblacklist_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute('UPDATE users SET is_blacklisted = 0 WHERE id = ?', (user_id,))
    db.commit()
    flash('User unblacklisted')
    return redirect(request.referrer)

@app.route('/admin/delete_student/<int:student_id>')
def delete_student(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    student = db.execute('SELECT user_id FROM students WHERE id = ?', (student_id,)).fetchone()
    db.execute('DELETE FROM applications WHERE student_id = ?', (student_id,))
    db.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.execute('DELETE FROM users WHERE id = ?', (student['user_id'],))
    db.commit()
    flash('Student deleted')
    return redirect(url_for('admin_students'))

@app.route('/admin/delete_company/<int:company_id>')
def delete_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    company = db.execute('SELECT user_id FROM companies WHERE id = ?', (company_id,)).fetchone()
    db.execute('DELETE FROM applications WHERE drive_id IN (SELECT id FROM drives WHERE company_id = ?)', (company_id,))
    db.execute('DELETE FROM drives WHERE company_id = ?', (company_id,))
    db.execute('DELETE FROM companies WHERE id = ?', (company_id,))
    db.execute('DELETE FROM users WHERE id = ?', (company['user_id'],))
    db.commit()
    flash('Company deleted')
    return redirect(url_for('admin_companies'))

@app.route('/admin/drives')
def admin_drives():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    drives = db.execute('''SELECT d.*, c.name as company_name, COUNT(a.id) as applicant_count 
                          FROM drives d 
                          JOIN companies c ON d.company_id = c.id 
                          LEFT JOIN applications a ON d.id = a.drive_id 
                          GROUP BY d.id''').fetchall()
    return render_template('admin_drives.html', drives=drives)

@app.route('/company/create_drive', methods=['GET', 'POST'])
def create_drive():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if company['status'] != 'approved':
        flash('Company not approved')
        return redirect(url_for('company_dashboard'))
    
    if request.method == 'POST':
        db.execute('''INSERT INTO drives (company_id, title, description, eligibility_criteria, min_cgpa, deadline) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (company['id'], request.form['title'], request.form['description'],
                   request.form['eligibility_criteria'], request.form.get('min_cgpa', 0),
                   request.form.get('deadline', '')))
        db.commit()
        flash('Drive created. Waiting for admin approval')
        return redirect(url_for('company_dashboard'))
    
    return render_template('create_drive.html')

@app.route('/company/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
def edit_drive(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ? AND company_id = ?', (drive_id, company['id'])).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('company_dashboard'))
    
    if request.method == 'POST':
        db.execute('''UPDATE drives SET title = ?, description = ?, eligibility_criteria = ?, 
                     min_cgpa = ?, deadline = ? WHERE id = ?''',
                  (request.form['title'], request.form['description'], request.form['eligibility_criteria'],
                   request.form.get('min_cgpa', 0), request.form.get('deadline', ''), drive_id))
        db.commit()
        flash('Drive updated')
        return redirect(url_for('company_dashboard'))
    
    return render_template('edit_drive.html', drive=drive)

@app.route('/company/delete_drive/<int:drive_id>')
def delete_drive(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.execute('DELETE FROM applications WHERE drive_id = ?', (drive_id,))
    db.execute('DELETE FROM drives WHERE id = ? AND company_id = ?', (drive_id, company['id']))
    db.commit()
    flash('Drive deleted')
    return redirect(url_for('company_dashboard'))

@app.route('/company/close_drive/<int:drive_id>')
def close_drive(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.execute('UPDATE drives SET status = "closed" WHERE id = ? AND company_id = ?', (drive_id, company['id']))
    db.commit()
    flash('Drive closed')
    return redirect(url_for('company_dashboard'))

@app.route('/company/applications/<int:drive_id>')
def view_applications(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ? AND company_id = ?', (drive_id, company['id'])).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('company_dashboard'))
    
    applications = db.execute('''SELECT a.*, s.name, s.roll_number, s.branch, s.cgpa, s.contact, s.resume 
                                FROM applications a 
                                JOIN students s ON a.student_id = s.id 
                                WHERE a.drive_id = ?''', (drive_id,)).fetchall()
    
    return render_template('view_applications.html', drive=drive, applications=applications)

@app.route('/company/update_status/<int:application_id>/<status>')
def update_application_status(application_id, status):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('UPDATE applications SET status = ? WHERE id = ?', (status, application_id))
    db.commit()
    flash(f'Application status updated to {status}')
    return redirect(request.referrer)

@app.route('/student/apply/<int:drive_id>')
def apply_drive(drive_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ?', (drive_id,)).fetchone()
    
    if drive['min_cgpa'] and student['cgpa'] < drive['min_cgpa']:
        flash('CGPA requirement not met')
        return redirect(url_for('student_dashboard'))
    
    existing = db.execute('SELECT id FROM applications WHERE student_id = ? AND drive_id = ?',
                         (student['id'], drive_id)).fetchone()
    
    if existing:
        flash('Already applied to this drive')
        return redirect(url_for('student_dashboard'))
    
    db.execute('INSERT INTO applications (student_id, drive_id) VALUES (?, ?)', (student['id'], drive_id))
    db.commit()
    flash('Application submitted')
    return redirect(url_for('student_dashboard'))

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        resume_filename = student['resume']
        
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{student['roll_number']}_{file.filename}")
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                resume_filename = filename
        
        db.execute('''UPDATE students SET name = ?, branch = ?, cgpa = ?, contact = ?, resume = ? 
                     WHERE user_id = ?''',
                  (request.form['name'], request.form['branch'], request.form['cgpa'],
                   request.form['contact'], resume_filename, session['user_id']))
        db.commit()
        flash('Profile updated')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student_profile.html', student=student)

@app.route('/company/profile', methods=['GET', 'POST'])
def company_profile():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        db.execute('''UPDATE companies SET name = ?, description = ?, hr_contact = ?, website = ? 
                     WHERE user_id = ?''',
                  (request.form['name'], request.form['description'], request.form['hr_contact'],
                   request.form['website'], session['user_id']))
        db.commit()
        flash('Profile updated')
        return redirect(url_for('company_dashboard'))
    
    return render_template('company_profile.html', company=company)

@app.route('/student/drive/<int:drive_id>')
def student_drive_detail(drive_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('''SELECT d.*, c.name as company_name, c.description as company_description, 
                         c.website, c.hr_contact FROM drives d 
                         JOIN companies c ON d.company_id = c.id 
                         WHERE d.id = ?''', (drive_id,)).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('student_dashboard'))
    
    application = db.execute('SELECT * FROM applications WHERE student_id = ? AND drive_id = ?',
                            (student['id'], drive_id)).fetchone()
    
    applicant_count = db.execute('SELECT COUNT(*) as count FROM applications WHERE drive_id = ?',
                                (drive_id,)).fetchone()['count']
    
    return render_template('student_drive_detail.html', drive=drive, student=student, 
                         application=application, applicant_count=applicant_count)

@app.route('/admin/drive/<int:drive_id>')
def admin_drive_detail(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    drive = db.execute('''SELECT d.*, c.name as company_name, c.description as company_description, 
                         c.website, c.hr_contact, c.id as company_id FROM drives d 
                         JOIN companies c ON d.company_id = c.id 
                         WHERE d.id = ?''', (drive_id,)).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('admin_drives'))
    
    applications = db.execute('''SELECT a.*, s.name, s.roll_number, s.branch, s.cgpa, s.contact 
                                FROM applications a 
                                JOIN students s ON a.student_id = s.id 
                                WHERE a.drive_id = ? 
                                ORDER BY a.applied_at DESC''', (drive_id,)).fetchall()
    
    stats = {
        'total': len(applications),
        'applied': len([a for a in applications if a['status'] == 'applied']),
        'shortlisted': len([a for a in applications if a['status'] == 'shortlisted']),
        'selected': len([a for a in applications if a['status'] == 'selected']),
        'rejected': len([a for a in applications if a['status'] == 'rejected'])
    }
    
    return render_template('admin_drive_detail.html', drive=drive, applications=applications, stats=stats)
