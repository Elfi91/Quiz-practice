from data_manager import DataManager
import datetime
import time
import random

class QuizEngine:
    """Manages the main quiz loop and logic."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        # No longer loading default local questions here, better passed in run()

    def print_success_art(self):
        """Prints a celebratory ASCII art."""
        art = r"""
       ___________
      '._==_==_=_.'
      .-\:      /-.
     | (|:.     |) |
      '-|:.     |-'
        \::.    /
         '::. .'
           ) (
         _.' '._
        `"""""""`
        """
        print(art)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes text by lowercasing, stripping, and removing trailing punctuation."""
        if not text:
            return ""
        # Lowercase and strip whitespace
        text = text.lower().strip()
        # Aggressively remove punctuation
        for char in ['.', '!', '?']:
            text = text.replace(char, "")
        return text

    def run(self, questions: list, session_length: int = 15, time_limit_minutes: int = None, silent_start: bool = False):
        """
        Starts the quiz loop.
        
        Args:
            questions (list): List of question objects.
            session_length (int): Number of questions to answer.
            time_limit_minutes (int, optional): Time limit in minutes. None for no limit.
            silent_start (bool): If True, suppresses intro message.
        """
        if not questions:
            print("❌ Error: No questions provided.")
            return

        # Prepare questions
        # Randomize order
        random.shuffle(questions)
        
        # Limit number of questions
        if len(questions) > session_length:
            questions = questions[:session_length]
        else:
            session_length = len(questions) # Adjust if fewer available

        if not silent_start:
            print(f"🚀 Starting quiz with {session_length} questions.")
            if time_limit_minutes:
                print(f"⏱️  Time Limit: {time_limit_minutes} minutes.")
            print("Type 'exit' to quit at any time.\n")
        
        question_queue = questions[:]
        session_errors = []
        questions_answered = 0
        start_time = time.time()

        while question_queue:
            # Check Time Limit
            if time_limit_minutes:
                elapsed_seconds = time.time() - start_time
                elapsed_minutes = elapsed_seconds / 60
                if elapsed_minutes >= time_limit_minutes:
                    print("\n" + "!"*40)
                    print(f"⏰ TIME'S UP! The {time_limit_minutes} minute limit has been reached.")
                    print("!"*40 + "\n")
                    break

            # Check Session Limit (redundant with slicing but safe)
            if questions_answered >= session_length:
                break

            # Pop next question
            current_q = question_queue.pop(0)
            question_text = current_q.get("question")
            
            # Helper to get correct answer strings safely
            raw_correct = current_q.get("correct_answers", [])
            correct_answers = [ans.strip().lower() for ans in raw_correct]
            
            explanation = current_q.get("explanation")
            keywords = current_q.get("keywords", [])

            # Print Progress
            progress = questions_answered + 1
            
            # Time specific status bar
            time_info = ""
            if time_limit_minutes:
                elapsed_seconds = int(time.time() - start_time)
                remaining_seconds = (time_limit_minutes * 60) - elapsed_seconds
                rem_min = remaining_seconds // 60
                rem_sec = remaining_seconds % 60
                time_info = f" | ⏳ {rem_min}:{rem_sec:02d} left"
            
            bar_length = 10
            filled_len = int(bar_length * progress // session_length)
            bar = "#" * filled_len + "-" * (bar_length - filled_len)
            print(f"Question [{progress}/{session_length}] [{bar}]{time_info}")

            print(f"📝 {question_text}")

            # Get User Input
            user_answer = ""
            while True:
                # Check timer again inside input loop to avoid hanging if user waits too long
                if time_limit_minutes:
                     elapsed_now = time.time() - start_time
                     if elapsed_now >= time_limit_minutes * 60:
                         print("\n⏰ Time is up!")
                         user_answer = "TIME_UP" # specific flag
                         break

                try:
                    # Input with a prompt
                    # Note: Python's input() blocks. A true non-blocking input requires threading/select
                    # For simplicity, we check time before/after. If user sits in input() forever, functionality is limited.
                    # Given the constraints, we rely on checking before asking.
                    user_answer = input("\nYour answer: ").strip()
                except EOFError:
                    user_answer = "exit"
                
                if not user_answer:
                    continue
                break
            
            # Check timeout flag
            if user_answer == "TIME_UP":
                break

            if user_answer.lower() in ['exit', 'quit']:
                print("Exiting quiz...")
                break

            # Validation logic (Simple A/B/C/D check)
            # ... (retained from original)
            is_multiple_choice = "A)" in question_text and "B)" in question_text
            if is_multiple_choice:
                 cleaned_input = user_answer.lower()
                 valid_options = ['a', 'b', 'c', 'd', 'e']
                 if len(cleaned_input) == 1 and cleaned_input.isalpha() and cleaned_input not in valid_options:
                      print(f"⚠️  Please manually select one of valid options ({', '.join(valid_options[:4]).upper()}).")
                      # Ideally loop back, but for refactor simplicity/flow, we accept it as wrong or let it slide to check.
                      # To keep logic simple:
                      pass 

            # Verification
            print("Checking answer...")
            
            cleaned_user_answer = self.normalize_text(user_answer)
            normalized_correct_answers = [self.normalize_text(ans) for ans in correct_answers]
            
            is_correct = cleaned_user_answer in normalized_correct_answers
            
            if is_multiple_choice and len(cleaned_user_answer) == 1 and cleaned_user_answer.isalpha():
                 # Letter trap fix
                 is_correct = any(a.lower() == cleaned_user_answer for a in correct_answers)

            if is_correct:
                print("\n✅ Correct!")
                self.data_manager.remove_error(question_text)
            else:
                print("\n❌ Incorrect")
                print(f"   Expected: {', '.join(correct_answers)}")
                
                if explanation:
                    print(f"\n{explanation}\n")
                
                # Save Error
                error_entry = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "question": question_text,
                    "user_answer": user_answer,
                    "correct_answers": raw_correct,
                    "explanation": explanation,
                    "keywords": keywords
                }
                self.data_manager.save_error(error_entry)
                session_errors.append(error_entry)
            
            questions_answered += 1
            print("-" * 40)

        # End Session Report
        print("\n" + "="*40)
        
        score = questions_answered - len(session_errors)
        # Avoid division by zero
        percentage = (score / questions_answered * 100) if questions_answered > 0 else 0.0
        
        print(f"Final Score: {score}/{questions_answered} - {percentage:.0f}%")

        # Save Progress
        session_stats = {
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": "timed" if time_limit_minutes else "standard",
            "score": score,
            "total": questions_answered,
            "percentage": round(percentage, 2)
        }
        self.data_manager.save_progress(session_stats)

        if not session_errors:
            self.print_success_art()
            print("🏆 Perfect Score! 🏆")
        else:
            print(f"Good job! You made {len(session_errors)} errors.")
            print("\n" + "="*15 + " FOCUS ON WRONG ANSWERS " + "="*15 + "\n")
            
            for idx, err in enumerate(session_errors, 1):
                q_text = err['question'].split('\n')[0] 
                print(f"{idx}. {q_text}")
                print(f"   ❌ Your Answer: {err['user_answer']}")
                correct_str = ', '.join(err.get('correct_answers', []))
                print(f"   ✅ Correct Answer: {correct_str}")
                print("")
            
            print("Errors saved for review.")

        print("="*40 + "\n")
