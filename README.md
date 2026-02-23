# Placement Management System

A Flask-based web application for managing campus placement drives, student applications, and company registrations.

## Project Structure

```
python project/
├── templates/              # HTML templates
├── static/                 # CSS, JS, uploads
│   ├── css/
│   └── uploads/
├── routes/                 # Route modules
│   ├── auth.py            # Authentication routes
│   ├── admin.py           # Admin routes
│   ├── student.py         # Student routes
│   ├── company.py         # Company routes
│   └── api.py             # REST API routes
├── models/                 # Database models
│   └── database.py        # Database connection & init
├── utils/                  # Helper functions
│   └── helpers.py         # Utility functions
├── app.py                  # Main application
├── config.py               # Configuration
├── init_db.py              # Database initialization
└── requirements.txt        # Dependencies
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

- Student registration and profile management
- Company registration with admin approval
- Placement drive creation and management
- Application tracking
- Admin dashboard with analytics
- REST API endpoints
