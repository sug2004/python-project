# Placement Management System

A Flask-based web application for managing campus placement drives, student applications, and company registrations.

## ✅ Project Status: 100% Complete

All 6 core milestones have been successfully implemented!

## Project Structure

```
python project/
├── templates/              # HTML templates (17 files)
├── static/                 # CSS, JS, uploads
│   ├── css/
│   │   └── style.css
│   └── uploads/
├── routes/                 # Route modules
│   ├── __init__.py
│   ├── auth.py            # Authentication routes
│   ├── admin.py           # Admin routes
│   ├── student.py         # Student routes
│   ├── company.py         # Company routes
│   └── api.py             # REST API routes (15 endpoints)
├── models/                 # Database models
│   ├── __init__.py
│   └── database.py        # Database connection & init
├── utils/                  # Helper functions
│   ├── __init__.py
│   └── helpers.py         # Utility functions
├── app.py                  # Main application
├── config.py               # Configuration
├── init_db.py              # Database initialization
├── requirements.txt        # Dependencies
├── README.md               # This file
├── API_DOCUMENTATION.md    # API endpoints documentation
├── MILESTONE_COMPLETION.md # Detailed milestone tracking
└── .gitignore              # Git ignore rules
```

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python init_db.py
```

3. Run the application:
```bash
python app.py
```

4. Access the application at `http://localhost:5000`

## Default Admin Credentials

- Email: admin@placement.com
- Password: admin123

## Features

### Core Features (100% Complete)

✅ **Authentication & Authorization**
- Student and Company registration/login
- Admin login (predefined)
- Role-based access control
- Company approval workflow

✅ **Admin Dashboard**
- View total students, companies, drives, applications
- Approve/Reject company registrations
- Approve/Reject placement drives
- Search students by name, ID, contact
- Search companies by name
- Blacklist/Unblacklist users
- Delete students and companies

✅ **Company Dashboard**
- Create placement drives (after approval)
- View all posted drives and applications
- Edit and delete drives
- Review student applications
- Update application status (Shortlisted/Selected/Rejected)
- View student profiles and resumes

✅ **Student Dashboard**
- Update profile and upload resume
- View approved placement drives
- Apply to drives (with CGPA validation)
- Track application status
- Receive notifications on status changes
- View application history

✅ **Placement Tracking**
- Complete application history
- Duplicate application prevention (UNIQUE constraint)
- Status flow: Applied → Shortlisted → Selected/Rejected
- Only approved companies can create drives
- Students can only view/apply to approved drives
- Automatic notifications on status changes

✅ **REST API**
- 15 API endpoints with full CRUD operations
- JSON-based responses
- 4 HTTP methods: GET, POST, PUT, DELETE
- See API_DOCUMENTATION.md for details

## Database Schema

- **users**: Authentication and role management
- **students**: Student profiles and academic details
- **companies**: Company profiles and approval status
- **drives**: Job postings/placement drives
- **applications**: Student applications with status tracking
- **notifications**: Status change notifications for students

## Key Features

1. **Duplicate Prevention**: UNIQUE constraint prevents duplicate applications
2. **Notification System**: Auto-notifications when application status changes
3. **Search Functionality**: Admin can search students and companies
4. **Blacklist System**: Admin can blacklist/unblacklist users
5. **Approval Workflow**: Companies and drives require admin approval
6. **CGPA Validation**: Students can only apply if they meet requirements
7. **Status Tracking**: Complete application lifecycle tracking
8. **Resume Management**: Students can upload and update resumes

## Git Commit Messages

Use these exact commit messages for each milestone:

- `Milestone-0 PPA-MAD-1` - GitHub Setup
- `Milestone-PPA DB-Relationship` - Database Models
- `Milestone-PPA Auth_RBAC` - Authentication
- `Milestone-PPA Admin-Dashboard-Management` - Admin Dashboard
- `Milestone-PPA Company-Dashboard-Management` - Company Dashboard
- `Milestone-PPA Student-Dashboard-Management` - Student Dashboard
- `Milestone-PPA Placement-Tracking` - Placement Tracking
- `Milestone-PPA Created-API` - API Integration

## Testing

### Web Interface
1. Start the application: `python app.py`
2. Open browser: `http://localhost:5000`
3. Login as admin to approve companies and drives
4. Register as student/company to test workflows

### API Testing
See `API_DOCUMENTATION.md` for complete API documentation and cURL examples.

## Technologies Used

- **Backend**: Flask 2.3.0
- **Database**: SQLite3
- **Security**: Werkzeug password hashing
- **Frontend**: Bootstrap 5, Font Awesome
- **File Upload**: Resume management with validation

## Project Completion

**Progress: 100%** ✅

All 6 core milestones completed:
1. ✅ Database Models (18%)
2. ✅ Authentication & RBAC (10%)
3. ✅ Admin Dashboard (20%)
4. ✅ Company Dashboard (17%)
5. ✅ Student Dashboard (15%)
6. ✅ Placement Tracking (15%)

Bonus: ✅ API Integration (Optional Enhancement)

See `MILESTONE_COMPLETION.md` for detailed milestone breakdown.
