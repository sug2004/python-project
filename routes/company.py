from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from models.database import get_db

company_bp = Blueprint('company', __name__, url_prefix='/company')

@company_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    drives = db.execute('''SELECT d.*, COUNT(a.id) as applicant_count 
                          FROM drives d 
                          LEFT JOIN applications a ON d.id = a.drive_id 
                          WHERE d.company_id = ? 
                          GROUP BY d.id''', (company['id'],)).fetchall()
    return render_template('company_dashboard.html', company=company, drives=drives)

@company_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        db.execute('''UPDATE companies SET name = ?, description = ?, hr_contact = ?, website = ? 
                     WHERE user_id = ?''',
                  (request.form['name'], request.form['description'], request.form['hr_contact'],
                   request.form['website'], session['user_id']))
        db.commit()
        flash('Profile updated')
        return redirect(url_for('company.dashboard'))
    
    return render_template('company_profile.html', company=company)

@company_bp.route('/create_drive', methods=['GET', 'POST'])
def create_drive():
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if company['status'] != 'approved':
        flash('Company not approved')
        return redirect(url_for('company.dashboard'))
    
    if request.method == 'POST':
        db.execute('''INSERT INTO drives (company_id, title, description, eligibility_criteria, min_cgpa, deadline) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (company['id'], request.form['title'], request.form['description'],
                   request.form['eligibility_criteria'], request.form.get('min_cgpa', 0),
                   request.form.get('deadline', '')))
        db.commit()
        flash('Drive created. Waiting for admin approval')
        return redirect(url_for('company.dashboard'))
    
    return render_template('create_drive.html')

@company_bp.route('/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
def edit_drive(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ? AND company_id = ?', (drive_id, company['id'])).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('company.dashboard'))
    
    if request.method == 'POST':
        db.execute('''UPDATE drives SET title = ?, description = ?, eligibility_criteria = ?, 
                     min_cgpa = ?, deadline = ? WHERE id = ?''',
                  (request.form['title'], request.form['description'], request.form['eligibility_criteria'],
                   request.form.get('min_cgpa', 0), request.form.get('deadline', ''), drive_id))
        db.commit()
        flash('Drive updated')
        return redirect(url_for('company.dashboard'))
    
    return render_template('edit_drive.html', drive=drive)

@company_bp.route('/delete_drive/<int:drive_id>')
def delete_drive(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.execute('DELETE FROM applications WHERE drive_id = ?', (drive_id,))
    db.execute('DELETE FROM drives WHERE id = ? AND company_id = ?', (drive_id, company['id']))
    db.commit()
    flash('Drive deleted')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/close_drive/<int:drive_id>')
def close_drive(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.execute('UPDATE drives SET status = "closed" WHERE id = ? AND company_id = ?', (drive_id, company['id']))
    db.commit()
    flash('Drive closed')
    return redirect(url_for('company.dashboard'))

@company_bp.route('/applications/<int:drive_id>')
def view_applications(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    company = db.execute('SELECT id FROM companies WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ? AND company_id = ?', (drive_id, company['id'])).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('company.dashboard'))
    
    applications = db.execute('''SELECT a.*, s.name, s.roll_number, s.branch, s.cgpa, s.contact, s.resume 
                                FROM applications a 
                                JOIN students s ON a.student_id = s.id 
                                WHERE a.drive_id = ?''', (drive_id,)).fetchall()
    
    return render_template('view_applications.html', drive=drive, applications=applications)

@company_bp.route('/update_status/<int:application_id>/<status>')
def update_application_status(application_id, status):
    if session.get('role') != 'company':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    app = db.execute('SELECT student_id FROM applications WHERE id = ?', (application_id,)).fetchone()
    db.execute('UPDATE applications SET status = ? WHERE id = ?', (status, application_id))
    
    # Create notification for student
    message = f'Your application status has been updated to: {status.upper()}'
    db.execute('INSERT INTO notifications (student_id, message) VALUES (?, ?)', (app['student_id'], message))
    
    db.commit()
    flash(f'Application status updated to {status}')
    return redirect(request.referrer)
