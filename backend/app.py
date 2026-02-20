from flask import Flask
import os
from database import init_db

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'placement-portal-secret-key')
app.config['DATABASE'] = 'placement.db'
app.config['UPLOAD_FOLDER'] = '../frontend/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

init_db(app)

from routes import *
from api import *

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
