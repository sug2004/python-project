from flask import jsonify, request, Blueprint
from models.database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    if role == 'admin':
        return jsonify({'error': 'Admin registration not allowed'}), 403
    
    db = get_db()
    
    if db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return jsonify({'error': 'Email already registered'}), 400
    
    hashed_password = generate_password_hash(password)
    cursor = db.execute('INSERT INTO users (email, password, role) VALUES (?, ?, ?)',
                      (email, hashed_password, role))
    user_id = cursor.lastrowid
    
    if role == 'student':
        db.execute('INSERT INTO students (user_id, name, roll_number, branch, cgpa, contact) VALUES (?, ?, ?, ?, ?, ?)',
                  (user_id, data.get('name'), data.get('roll_number'), 
                   data.get('branch'), data.get('cgpa'), data.get('contact', '')))
    elif role == 'company':
        db.execute('INSERT INTO companies (user_id, name, description, hr_contact, website) VALUES (?, ?, ?, ?, ?)',
                  (user_id, data.get('company_name'), data.get('description', ''),
                   data.get('hr_contact', ''), data.get('website', '')))
    
    db.commit()
    return jsonify({'message': 'Registration successful', 'user_id': user_id}), 201

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if user['is_blacklisted']:
        return jsonify({'error': 'Account is blacklisted'}), 403
    
    if user['role'] == 'company':
        company = db.execute('SELECT status FROM companies WHERE user_id = ?', (user['id'],)).fetchone()
        if company['status'] != 'approved':
            return jsonify({'error': 'Company not approved yet'}), 403
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user['id'],
        'email': user['email'],
        'role': user['role']
    }), 200

@api_bp.route('/students', methods=['GET'])
def get_students():
    db = get_db()
    students = db.execute('SELECT s.*, u.email FROM students s JOIN users u ON s.user_id = u.id').fetchall()
    return jsonify([dict(s) for s in students]), 200

@api_bp.route('/companies', methods=['GET'])
def get_companies():
    db = get_db()
    companies = db.execute('SELECT c.*, u.email FROM companies c JOIN users u ON c.user_id = u.id').fetchall()
    return jsonify([dict(c) for c in companies]), 200

@api_bp.route('/drives', methods=['GET'])
def get_drives():
    db = get_db()
    drives = db.execute('SELECT d.*, c.name as company_name FROM drives d JOIN companies c ON d.company_id = c.id').fetchall()
    return jsonify([dict(d) for d in drives]), 200

@api_bp.route('/drives', methods=['POST'])
def create_drive():
    data = request.get_json()
    db = get_db()
    
    company = db.execute('SELECT * FROM companies WHERE user_id = ?', (data.get('user_id'),)).fetchone()
    if not company or company['status'] != 'approved':
        return jsonify({'error': 'Company not approved'}), 403
    
    cursor = db.execute('''INSERT INTO drives (company_id, title, description, eligibility_criteria, min_cgpa, deadline) 
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (company['id'], data.get('title'), data.get('description'),
               data.get('eligibility_criteria'), data.get('min_cgpa', 0),
               data.get('deadline', '')))
    db.commit()
    return jsonify({'message': 'Drive created', 'drive_id': cursor.lastrowid}), 201

@api_bp.route('/applications', methods=['POST'])
def apply():
    data = request.get_json()
    db = get_db()
    
    student = db.execute('SELECT * FROM students WHERE user_id = ?', (data.get('user_id'),)).fetchone()
    drive = db.execute('SELECT * FROM drives WHERE id = ?', (data.get('drive_id'),)).fetchone()
    
    if not student or not drive:
        return jsonify({'error': 'Invalid student or drive'}), 400
    
    if drive['min_cgpa'] and student['cgpa'] < drive['min_cgpa']:
        return jsonify({'error': 'CGPA requirement not met'}), 400
    
    existing = db.execute('SELECT id FROM applications WHERE student_id = ? AND drive_id = ?',
                         (student['id'], data.get('drive_id'))).fetchone()
    
    if existing:
        return jsonify({'error': 'Already applied'}), 400
    
    cursor = db.execute('INSERT INTO applications (student_id, drive_id) VALUES (?, ?)', 
                       (student['id'], data.get('drive_id')))
    db.commit()
    return jsonify({'message': 'Application submitted', 'application_id': cursor.lastrowid}), 201

@api_bp.route('/stats', methods=['GET'])
def stats():
    db = get_db()
    stats = {
        'total_students': db.execute('SELECT COUNT(*) as count FROM students').fetchone()['count'],
        'total_companies': db.execute('SELECT COUNT(*) as count FROM companies').fetchone()['count'],
        'total_drives': db.execute('SELECT COUNT(*) as count FROM drives').fetchone()['count'],
        'total_applications': db.execute('SELECT COUNT(*) as count FROM applications').fetchone()['count']
    }
    return jsonify(stats), 200

@api_bp.route('/applications/<int:drive_id>', methods=['GET'])
def get_applications(drive_id):
    db = get_db()
    applications = db.execute('''SELECT a.*, s.name, s.roll_number, s.branch, s.cgpa 
                                FROM applications a 
                                JOIN students s ON a.student_id = s.id 
                                WHERE a.drive_id = ?''', (drive_id,)).fetchall()
    return jsonify([dict(a) for a in applications]), 200

@api_bp.route('/applications/<int:application_id>/status', methods=['PUT'])
def update_status(application_id):
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['applied', 'shortlisted', 'selected', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    db = get_db()
    app = db.execute('SELECT student_id FROM applications WHERE id = ?', (application_id,)).fetchone()
    
    if not app:
        return jsonify({'error': 'Application not found'}), 404
    
    db.execute('UPDATE applications SET status = ? WHERE id = ?', (status, application_id))
    
    # Create notification
    message = f'Your application status has been updated to: {status.upper()}'
    db.execute('INSERT INTO notifications (student_id, message) VALUES (?, ?)', (app['student_id'], message))
    
    db.commit()
    return jsonify({'message': 'Status updated', 'status': status}), 200

@api_bp.route('/companies/<int:company_id>/approve', methods=['PUT'])
def approve_company(company_id):
    db = get_db()
    db.execute('UPDATE companies SET status = "approved" WHERE id = ?', (company_id,))
    db.commit()
    return jsonify({'message': 'Company approved'}), 200

@api_bp.route('/companies/<int:company_id>/reject', methods=['PUT'])
def reject_company(company_id):
    db = get_db()
    db.execute('UPDATE companies SET status = "rejected" WHERE id = ?', (company_id,))
    db.commit()
    return jsonify({'message': 'Company rejected'}), 200

@api_bp.route('/drives/<int:drive_id>/approve', methods=['PUT'])
def approve_drive(drive_id):
    db = get_db()
    db.execute('UPDATE drives SET status = "approved" WHERE id = ?', (drive_id,))
    db.commit()
    return jsonify({'message': 'Drive approved'}), 200

@api_bp.route('/drives/<int:drive_id>', methods=['DELETE'])
def delete_drive(drive_id):
    db = get_db()
    db.execute('DELETE FROM applications WHERE drive_id = ?', (drive_id,))
    db.execute('DELETE FROM drives WHERE id = ?', (drive_id,))
    db.commit()
    return jsonify({'message': 'Drive deleted'}), 200

@api_bp.route('/users/<int:user_id>/blacklist', methods=['PUT'])
def blacklist(user_id):
    db = get_db()
    db.execute('UPDATE users SET is_blacklisted = 1 WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({'message': 'User blacklisted'}), 200
