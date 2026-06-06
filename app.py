from flask import Flask
from config import supabase

from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.dashboard import dashboard_bp
from routes.journal import journal_bp
from routes.schedule import schedule_bp

app = Flask(__name__)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(journal_bp, url_prefix='/journals')
app.register_blueprint(schedule_bp, url_prefix='/schedules')

@app.route('/')
def home():
    return "Pendar API is running!"

if __name__ == '__main__':
    app.run(debug=True)