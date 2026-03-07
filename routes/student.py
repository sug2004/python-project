from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from models.database import get_db
from utils.helpers import allowed_file
from werkzeug.utils import secure_filename
import os

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    
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
    
    # Get unread notifications
    notifications = db.execute('''SELECT * FROM notifications WHERE student_id = ? AND is_read = 0 
                                 ORDER BY created_at DESC''', (student['id'],)).fetchall()
    
    return render_template('student_dashboard.html', student=student, drives=drives, 
                         applications=applications, notifications=notifications)

@student_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        resume_filename = student['resume']
        
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{student['roll_number']}_{file.filename}")
                file.save(os.path.join('static/uploads', filename))
                resume_filename = filename
        
        db.execute('''UPDATE students SET name = ?, branch = ?, cgpa = ?, contact = ?, resume = ? 
                     WHERE user_id = ?''',
                  (request.form['name'], request.form['branch'], request.form['cgpa'],
                   request.form['contact'], resume_filename, session['user_id']))
        db.commit()
        flash('Profile updated')
        return redirect(url_for('student.dashboard'))
    
    return render_template('student_profile.html', student=student)

@student_bp.route('/apply/<int:drive_id>')
def apply_drive(drive_id):
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ?', (drive_id,)).fetchone()
    
    if drive['min_cgpa'] and student['cgpa'] < drive['min_cgpa']:
        flash('CGPA requirement not met')
        return redirect(url_for('student.dashboard'))
    
    existing = db.execute('SELECT id FROM applications WHERE student_id = ? AND drive_id = ?',
                         (student['id'], drive_id)).fetchone()
    
    if existing:
        flash('Already applied to this drive')
        return redirect(url_for('student.dashboard'))
    
    db.execute('INSERT INTO applications (student_id, drive_id) VALUES (?, ?)', (student['id'], drive_id))
    db.commit()
    flash('Application submitted')
    return redirect(url_for('student.dashboard'))

@student_bp.route('/drive/<int:drive_id>')
def drive_detail(drive_id):
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    drive = db.execute('''SELECT d.*, c.name as company_name, c.description as company_description, 
                         c.website, c.hr_contact FROM drives d 
                         JOIN companies c ON d.company_id = c.id 
                         WHERE d.id = ?''', (drive_id,)).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('student.dashboard'))
    
    application = db.execute('SELECT * FROM applications WHERE student_id = ? AND drive_id = ?',
                            (student['id'], drive_id)).fetchone()
    
    applicant_count = db.execute('SELECT COUNT(*) as count FROM applications WHERE drive_id = ?',
                                (drive_id,)).fetchone()['count']
    
    return render_template('student_drive_detail.html', drive=drive, student=student, 
                         application=application, applicant_count=applicant_count)

@student_bp.route('/mark_notifications_read')
def mark_notifications_read():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.execute('UPDATE notifications SET is_read = 1 WHERE student_id = ?', (student['id'],))
    db.commit()
    return redirect(url_for('student.dashboard'))
