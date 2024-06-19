from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
import os
import random


app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'quiz.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

from models.trivia import Trivia
from models.user import User

# class User(db.Model,UserMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(150), unique=True, nullable=False)
#     password = db.Column(db.String(150), nullable=False)

# class Trivia(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     category = db.Column(db.String(200))
#     type = db.Column(db.String(50))
#     difficulty = db.Column(db.String(50))
#     question = db.Column(db.String(500))
#     correct_answer = db.Column(db.String(200))
#     incorrect_answers = db.Column(db.Text) 
    
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Login Manager user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/fetch_trivia', methods=['POST'])
@login_required
def fetch_trivia():
    url = "https://opentdb.com/api.php?amount=50"
    response = requests.get(url)
    data = response.json()

    for item in data['results']:
        category = item['category']
        type_ = item['type']
        difficulty = item['difficulty']
        question = item['question']
        correct_answer = item['correct_answer']
        incorrect_answers = json.dumps(item['incorrect_answers'])

        trivia = Trivia(
            category=category, type=type_, difficulty=difficulty, 
            question=question, correct_answer=correct_answer,
            incorrect_answers=incorrect_answers
        )
        db.session.add(trivia)

    db.session.commit()
    return jsonify({"message": "Trivia data fetched and stored successfully!"})

@app.route('/trivia', methods=['GET'])
@login_required
def get_trivia():
    trivia_data = Trivia.query.all()
    result = [
        {
            "id": item.id,
            "category": item.category,
            "type": item.type,
            "difficulty": item.difficulty,
            "question": item.question,
            "correct_answer": item.correct_answer,
            "incorrect_answers": json.loads(item.incorrect_answers)
        } for item in trivia_data
    ]
    return jsonify(result)

@app.route('/analyze', methods=['GET'])
@login_required
def analyze_trivia():
    difficulties = {"easy": 0, "medium": 0, "hard": 0}
    categories = {}
    types = {"multiple": 0, "boolean": 0}

    trivia_data = Trivia.query.all()
    for item in trivia_data:
        difficulties[item.difficulty] += 1
        categories[item.category] = categories.get(item.category, 0) + 1
        types[item.type] += 1

    avg_difficulty = sum([1 * difficulties['easy'], 2 * difficulties['medium'], 3 * difficulties['hard']]) / len(trivia_data)

    analysis_result = {
        "average_difficulty": avg_difficulty,
        "most_common_category": max(categories, key=categories.get),
        "questions_per_type": types
    }
    return jsonify(analysis_result)

@app.route('/add_trivia', methods=['POST'])
@login_required
def add_trivia():
    data = request.get_json()
    new_trivia = Trivia(
        category=data['category'],
        type=data['type'],
        difficulty=data['difficulty'],
        question=data['question'],
        correct_answer=data['correct_answer'],
        incorrect_answers=json.dumps(data['incorrect_answers'])
    )
    db.session.add(new_trivia)
    db.session.commit()
    return jsonify({"message": "New trivia question added successfully!"})


@app.route('/get_question', methods=['GET'])
@login_required
def get_question():
    trivia_data = Trivia.query.all()
    if not trivia_data:
        return jsonify({"error": "No trivia questions available"}), 404
    question = random.choice(trivia_data)
    result = {
        "id": question.id,
        "category": question.category,
        "type": question.type,
        "difficulty": question.difficulty,
        "question": question.question,
        "correct_answer": question.correct_answer,
        "incorrect_answers": json.loads(question.incorrect_answers)
    }
    return jsonify(result)

# @app.route('/check_answer', methods=['POST'])
# @login_required
# def check_answer():
#     data = request.get_json()
#     question_id = data['question_id']
#     user_answer = data['user_answer']
#     trivia_question = Trivia.query.get(question_id)
#     if trivia_question.correct_answer.lower() == user_answer.lower():
#         return jsonify({"result": "correct"})
#     else:
#         return jsonify({"result": "incorrect", "correct_answer": trivia_question.correct_answer})

@app.route('/check_answer', methods=['POST'])
@login_required
def check_answer():
    data = request.get_json()
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')

    question = Trivia.query.get(question_id)
    if not question:
        return jsonify({'error': 'Invalid question'})

    current_user.total_questions += 1
    if user_answer.lower() == question.correct_answer.lower():
        difficulty = question.difficulty.lower()
        if difficulty == 'easy':
            current_user.easy_correct += 1
        elif difficulty == 'medium':
            current_user.medium_correct += 1
        elif difficulty == 'hard':
            current_user.hard_correct += 1
        db.session.commit()
        return jsonify({'result': 'correct', 'correct_answer': question.correct_answer})
    else:
        db.session.commit()
        return jsonify({'result': 'incorrect', 'correct_answer': question.correct_answer})

@app.route('/progress')
@login_required
def progress():
    return render_template('progress.html', user=current_user)

@app.route('/ranking')
@login_required
def ranking():
    users = User.query.order_by(
        (User.easy_correct + User.medium_correct + User.hard_correct).desc()
    ).all()
    return render_template('ranking.html', users=users)

if __name__ == '__main__':
    app.run(debug=False)
    
