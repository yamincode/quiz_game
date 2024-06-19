import unittest
from flask import url_for
from src.app import create_app
from src.create_db import  db
import json
from src.models.user import User
from src.models.trivia import Trivia

class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_login(self):
        # Register a new user
        response = self.client.post('register', data={
            'username': 'testuser',
            'password': 'testpassword',
            'confirm_password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)  # Redirects to login

        # Login with the new user
        response = self.client.post('login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)  # Redirects to home

        # Check the user is logged in
        response = self.client.get('login')
        self.assertIn(b'Login', response.data)

   
        
if __name__ == '__main__':
    unittest.main()
