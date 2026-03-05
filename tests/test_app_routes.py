import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, QUIZ_SESSIONS
import uuid

class QuizAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_status_code(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Start New Quiz', result.data)

    def test_start_quiz(self):
        # Simulate starting a quiz
        result = self.app.post('/start', data={
            'source': '2', # Quiz 2
            'count': '25',
            'timer': 'none'
        }, follow_redirects=True)
        
        # Should redirect to /quiz, which renders quiz.html
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Question 1 / 25', result.data)
        self.assertIn(b'Submit Answer', result.data)

    def test_submit_answer(self):
        # Create a mock session
        sid = str(uuid.uuid4())
        
        # Populate global session store
        QUIZ_SESSIONS[sid] = {
            'questions': [{'question': 'Test Q', 'correct_answers': ['a'], 'explanation': 'exp', 'keywords': []}],
            'total_questions': 1,
            'current_index': 0,
            'score': 0,
            'errors': [],
            'start_time': 0,
            'end_timestamp': None,
            'time_limit_minutes': None
        }
        
        # Set session cookie
        with self.app.session_transaction() as sess:
            sess['session_id'] = sid
        
        # Submit answer
        result = self.app.post('/submit', data={'answer': 'a'}, follow_redirects=True)
        
        # After answering last question, should redirect to result
        self.assertEqual(result.status_code, 200)
        self.assertIn(b'Quiz Complete', result.data)

if __name__ == '__main__':
    unittest.main()
