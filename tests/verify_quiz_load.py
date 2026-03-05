import json
import os
import sys

# Add parent directory to path so we can import data_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_manager import DataManager

def verify_file(filename):
    print(f"Verifying {filename}...")
    dm = DataManager()
    
    # We load relative to the script execution
    full_path = os.path.join(os.getcwd(), filename)
    
    if not os.path.exists(full_path):
         print(f"❌ File not found: {full_path}")
         return False

    load_func = getattr(dm, 'load_local_questions', None)
    if not load_func:
        print("❌ DataManager.load_local_questions method not found.")
        return False

    try:
        questions = load_func(full_path)
    except Exception as e:
        print(f"❌ Exception loading {filename}: {e}")
        return False
    
    if not questions:
        print(f"❌ Failed to load questions from {filename} or file is empty.")
        return False
        
    print(f"✅ Loaded {len(questions)} questions.")
    
    if len(questions) > 0:
        first_q = questions[0]
        required_fields = ['question', 'correct_answers', 'explanation']
        missing = [field for field in required_fields if field not in first_q]
        
        if missing:
            print(f"❌ Missing fields in first question: {missing}")
            return False
            
        print("✅ Structure check passed for first question.")
    
    return True

if __name__ == "__main__":
    files_to_check = [
        'data/quiz_1.json', 
        'data/quiz_2.json', 
        'data/quiz_6.json'
    ]
    
    all_passed = True
    for f in files_to_check:
        if not verify_file(f):
            all_passed = False
            print(f"⚠️ Check failed for {f}\n")
        else:
            print(f"Test passed for {f}\n")
            
    if all_passed:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("⚠️ Some checks failed.")
        sys.exit(1)
