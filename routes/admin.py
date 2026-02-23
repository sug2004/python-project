from flask import render_template, request, redirect, url_for, session, flash, Blueprint
from models.database import get_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
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

@admin_bp.route('/students')
def students():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
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

@admin_bp.route('/companies')
def companies():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
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

@admin_bp.route('/drives')
def drives():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    drives = db.execute('''SELECT d.*, c.name as company_name, COUNT(a.id) as applicant_count 
                          FROM drives d 
                          JOIN companies c ON d.company_id = c.id 
                          LEFT JOIN applications a ON d.id = a.drive_id 
                          GROUP BY d.id''').fetchall()
    return render_template('admin_drives.html', drives=drives)

@admin_bp.route('/approve_company/<int:company_id>')
def approve_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('UPDATE companies SET status = "approved" WHERE id = ?', (company_id,))
    db.commit()
    flash('Company approved')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject_company/<int:company_id>')
def reject_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('UPDATE companies SET status = "rejected" WHERE id = ?', (company_id,))
    db.commit()
    flash('Company rejected')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/approve_drive/<int:drive_id>')
def approve_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('UPDATE drives SET status = "approved" WHERE id = ?', (drive_id,))
    db.commit()
    flash('Drive approved')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/reject_drive/<int:drive_id>')
def reject_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('UPDATE drives SET status = "rejected" WHERE id = ?', (drive_id,))
    db.commit()
    flash('Drive rejected')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/blacklist/<int:user_id>')
def blacklist_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('UPDATE users SET is_blacklisted = 1 WHERE id = ?', (user_id,))
    db.commit()
    flash('User blacklisted')
    return redirect(request.referrer)

@admin_bp.route('/unblacklist/<int:user_id>')
def unblacklist_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    db.execute('UPDATE users SET is_blacklisted = 0 WHERE id = ?', (user_id,))
    db.commit()
    flash('User unblacklisted')
    return redirect(request.referrer)

@admin_bp.route('/delete_student/<int:student_id>')
def delete_student(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    student = db.execute('SELECT user_id FROM students WHERE id = ?', (student_id,)).fetchone()
    db.execute('DELETE FROM applications WHERE student_id = ?', (student_id,))
    db.execute('DELETE FROM students WHERE id = ?', (student_id,))
    db.execute('DELETE FROM users WHERE id = ?', (student['user_id'],))
    db.commit()
    flash('Student deleted')
    return redirect(url_for('admin.students'))

@admin_bp.route('/delete_company/<int:company_id>')
def delete_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    db = get_db()
    company = db.execute('SELECT user_id FROM companies WHERE id = ?', (company_id,)).fetchone()
    db.execute('DELETE FROM applications WHERE drive_id IN (SELECT id FROM drives WHERE company_id = ?)', (company_id,))
    db.execute('DELETE FROM drives WHERE company_id = ?', (company_id,))
    db.execute('DELETE FROM companies WHERE id = ?', (company_id,))
    db.execute('DELETE FROM users WHERE id = ?', (company['user_id'],))
    db.commit()
    flash('Company deleted')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/drive/<int:drive_id>')
def drive_detail(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    
    db = get_db()
    drive = db.execute('''SELECT d.*, c.name as company_name, c.description as company_description, 
                         c.website, c.hr_contact, c.id as company_id FROM drives d 
                         JOIN companies c ON d.company_id = c.id 
                         WHERE d.id = ?''', (drive_id,)).fetchone()
    
    if not drive:
        flash('Drive not found')
        return redirect(url_for('admin.drives'))
    
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
