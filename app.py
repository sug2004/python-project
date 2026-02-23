from flask import Flask
from config import Config
from models.database import init_db

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.student import student_bp
from routes.company import company_bp
from routes.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(company_bp)
app.register_blueprint(api_bp)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
