import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'placement-portal-secret-key')
    DATABASE = 'placement.db'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
