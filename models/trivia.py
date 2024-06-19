# models/trivia.py

from app import db

class Trivia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200))
    type = db.Column(db.String(50))
    difficulty = db.Column(db.String(50))
    question = db.Column(db.String(500))
    correct_answer = db.Column(db.String(200))
    incorrect_answers = db.Column(db.Text) 

    def __repr__(self):
        return f'<Trivia {self.id}>'
