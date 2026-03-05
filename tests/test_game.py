import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from data_manager import DataManager
from quiz_engine import QuizEngine


def main():
    # Load environment variables
    load_dotenv()

    
    print("🧪 Test Game - Loading quiz_2.json...")
    
    # Initialize components
    # Initialize components
    data_manager = DataManager()
    engine = QuizEngine(data_manager)
    
    # Load specific file
    test_file = "data/quiz_2.json"
    if not os.path.exists(test_file):
        print(f"❌ File not found: {test_file}")
        return

    questions = data_manager.load_local_questions(path=test_file)
    
    if not questions:
        print("❌ Failed to load questions.")
        return
        
    print(f"✅ Loaded {len(questions)} questions from {test_file}.")
    print("🚀 Starting short test session (3 questions)...")
    
    # Run Engine in offline mode with custom questions
    try:
        engine.run(
            questions=questions, 
            session_length=3, 
            silent_start=True
        )
    except KeyboardInterrupt:
        print("\nTest interrupted.")

if __name__ == "__main__":
    main()
