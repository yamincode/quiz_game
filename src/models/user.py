# models/user.py

from src.app import db
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    easy_correct = db.Column(db.Integer, default=0)
    medium_correct = db.Column(db.Integer, default=0)
    hard_correct = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<User {self.username}>'
