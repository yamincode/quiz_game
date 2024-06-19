import unittest

from src.app import create_app
from src.create_db import db
from src.models.trivia import Trivia
from src.models.user import User


class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_trivia_model(self):
        trivia = Trivia(question="What is the capital of France?", correct_answer="Paris")
        db.session.add(trivia)
        db.session.commit()

        retrieved_trivia = Trivia.query.first()
        self.assertEqual(retrieved_trivia.question, "What is the capital of France?")
        self.assertEqual(retrieved_trivia.correct_answer, "Paris")
        

    def test_user_model(self):
        user = User(username="testuser", password="hashed_password")
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.first()
        self.assertEqual(retrieved_user.username, "testuser")

if __name__ == '__main__':
    unittest.main()
