from gemini_client import GeminiClient
from data_manager import DataManager
import datetime

class QuizEngine:
    """Manages the main quiz loop and logic."""

    def __init__(self, client: GeminiClient, data_manager: DataManager):
        self.client = client
        self.data_manager = data_manager
        self.local_questions = self.data_manager.load_local_questions()

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
        import string
        if not text:
            return ""
        # Lowercase and strip whitespace
        text = text.lower().strip()
        # Aggressively remove punctuation as requested user-side (especially . and !)
        # treating them as noise rather than meaningful for these quizzes.
        for char in ['.', '!', '?']:
            text = text.replace(char, "")
        return text

    def run(self, offline_mode: bool = False, custom_questions: list = None, session_length: int = 15, silent_start: bool = False, level: str = "A1"):
        """Starts the main quiz loop."""
        if not silent_start:
            print(f"Welcome! Starting a session of {session_length} questions. Type 'exit' to quit.\n")
        
        question_queue = []
        session_errors = []
        questions_answered = 0
        consecutive_failures = 0

        if offline_mode:
            if not silent_start:
                print("🚀 Starting in OFFLINE MODE.")
            import random
            
            # 1. Full Shuffle first
            all_questions = []
            if custom_questions:
                 all_questions = custom_questions[:]
            elif self.local_questions:
                 all_questions = self.local_questions[:]
            
            if not all_questions:
                 print("❌ Error: No questions available.")
                 return

            random.shuffle(all_questions)
            
            # 2. Slice based on session_length
            if len(all_questions) < session_length:
                 if not silent_start:
                     print(f"⚠️  Nota: il livello ha solo {len(all_questions)} domande. Inizieremo la sessione con quelle disponibili.")
                 question_queue = all_questions[:] # Take all
            else:
                 question_queue = all_questions[:session_length]
                 
            if not silent_start:
                print(f"✅ Loaded {len(question_queue)} questions for this session.")


        while True:
            try:
                # Check Session Limit
                if questions_answered >= session_length:
                    break

                # Refill queue if empty (Only for Online Mode, Offline is pre-filled)
                if not question_queue:
                    if offline_mode:
                         # If offline queue is empty, we are done (handled by session limit check usually, but just in case)
                         break
                    else:
                        print(f"Generating questions for level {level}...")
                        # Calculate how many needed
                        needed = session_length - questions_answered
                        # Important: Don't request too few if it's the start, but also max at session_length
                        # If session_length is 10, we just ask for 10.
                        # If session_length is 20, we ask for 20 (batch_size max is usually 20 in prompt logic anyway)
                        batch_size = needed 
                        
                        question_queue = self.client.generate_batch_questions(batch_size, level=level)
                    if not question_queue:
                        consecutive_failures += 1
                        if consecutive_failures >= 3:
                            print("\n⚠️  Too many failures (Rate Limit).")
                            if self.local_questions:
                                print(f"🔄 Switching to OFFLINE MODE using {len(self.local_questions)} local questions.")
                                import random
                                question_queue = random.sample(self.local_questions, min(needed, len(self.local_questions)))
                                consecutive_failures = 0 
                                print(f"✅ Loaded {len(question_queue)} offline questions.\n")
                                continue 
                            else:
                                print("No local questions found. Please try again in a few minutes.")
                                break

                        print(f"Failed to generate questions. Waiting before retry ({consecutive_failures}/3)... (Waiting 30s)")
                        import time
                        time.sleep(30)
                        continue
                    # Reset failures on success
                    consecutive_failures = 0
                    print(f"✅ Loaded {len(question_queue)} new questions.\n")

                # Pop next question
                current_q = question_queue.pop(0)
                question_text = current_q.get("question")
                correct_answers = [ans.strip().lower() for ans in current_q.get("correct_answers", [])]
                explanation = current_q.get("explanation")
                keywords = current_q.get("keywords", [])

                # Print Progress
                progress = questions_answered + 1
                bar_length = 10
                filled_len = int(bar_length * progress // session_length)
                bar = "#" * filled_len + "-" * (bar_length - filled_len)
                print(f"Domanda [{progress}/{session_length}] [{bar}]")

                print(f"📝 {question_text}")

                # Get User Input with Validation
                while True:
                    user_answer = input("\nYour answer: ").strip()

                    if user_answer.lower() in ['exit', 'quit']:
                        print("Goodbye!")
                        break # Break input loop to reach save logic
                    
                    if not user_answer:
                        continue

                    # Validation for Multiple Choice
                    # Check if question resembles multiple choice (contains "A)" and "B)")
                    is_multiple_choice = "A)" in question_text and "B)" in question_text
                    
                    if is_multiple_choice:
                         cleaned_input = user_answer.lower()
                         # If input is a single letter but NOT a, b, or c (assuming 3 options usually)
                         # We allow d if D) is present, etc. but simplistically:
                         valid_options = ['a', 'b', 'c']
                         if "D)" in question_text:
                             valid_options.append('d')
                         
                         if len(cleaned_input) == 1 and cleaned_input.isalpha() and cleaned_input not in valid_options:
                             print(f"⚠️  Please manually select one of valid options ({', '.join(valid_options).upper()}).")
                             continue # Ask for input again
                    
                    # If we get here, input is valid (or at least acceptable to check)
                    break

                # Local Verification
                print("Checking answer...")
                
                cleaned_user_answer = self.normalize_text(user_answer)
                normalized_correct_answers = [self.normalize_text(ans) for ans in correct_answers]
                
                is_correct = cleaned_user_answer in normalized_correct_answers
                
                # Special check for multiple choice single letters
                is_multiple_choice = "A)" in question_text and "B)" in question_text
                if is_multiple_choice and len(cleaned_user_answer) == 1 and cleaned_user_answer.isalpha():
                     # Fix Bug 2 ("Letter-Trap"): Only match if strict equality with a single-letter option
                     # e.g. if user says 'a', correct_answers must contain exactly 'a', not just something starting with 'a'
                     # We trust correct_answers are already stripped/lowered above, but let's be safe
                     # For MCQ, usually the correct answer list might be ["A", "The actual text"] or just ["A"]
                     # We check if the letter is in there.
                     is_correct = any(a.lower() == cleaned_user_answer for a in correct_answers)



                if is_correct:
                    print("\n✅ Corretto! / Richtig!")
                    # Feature: Remove from error list if correct
                    self.data_manager.remove_error(question_text)
                else:
                    print("\n❌ Sbagliato / Falsch")
                    print(f"   Risposta attesa: {', '.join(correct_answers)}")
                    
                    # Smart Explanation Lookup
                    past_errors = self.data_manager.load_errors()
                    for err in past_errors:
                         if any(k in err.get("question", "") for k in keywords):
                             pass 

                    print(f"\n{explanation}\n")
                    
                    # Save Error Persistent
                    error_entry = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "question": question_text,
                        "user_answer": user_answer,
                        "correct_answers": current_q.get("correct_answers", []), # Save correct answers for review mode
                        "explanation": explanation,
                        "keywords": keywords
                    }
                    self.data_manager.save_error(error_entry)

                    # Save Session Error for Report (Add correct answer for clarity)
                    session_error_entry = error_entry.copy()
                    session_error_entry['correct_answers'] = current_q.get("correct_answers", [])
                    session_errors.append(session_error_entry)
                
                questions_answered += 1
            
            except Exception:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print("\n⚠️  Too many failures (Rate Limit). Please try again in a few minutes.")
                    break
                
                print(f"\n⚠️  Rate limit reached. Waiting 60 seconds ({consecutive_failures}/3)...")
                import time
                time.sleep(60)
            
            print("-" * 40)

        # End of Session Report
        print("\n" + "="*40)
        
        score = questions_answered - len(session_errors)
        percentage = (score / questions_answered * 100) if questions_answered > 0 else 0
        print(f"Punteggio: {score}/{questions_answered} - {percentage:.0f}%")

        # Save Progress (Feature)
        session_stats = {
            "timestamp": datetime.datetime.now().isoformat(),
            "mode": "offline" if offline_mode else "online",
            "score": score,
            "total": questions_answered,
            "percentage": round(percentage, 2)
        }
        self.data_manager.save_progress(session_stats)

        if not session_errors:
            self.print_success_art()
            print("🏆 Perfetto! 🏆")
        else:
            print("Bravo! Continua così, la pratica rende migliori! 🍕")
            print(f"Hai commesso {len(session_errors)} errori.")
            
            print("\n" + "="*15 + " FOCUS ON WRONG ANSWERS " + "="*15 + "\n")
            print("Ecco le risposte su cui devi lavorare di più:\n")
            for idx, err in enumerate(session_errors, 1):
                q_text = err['question'].split('\n')[0] 
                print(f"{idx}. {q_text}")
                print(f"   ❌ Tua risposta: {err['user_answer']}")
                # Handle correct answers list properly
                correct_str = ', '.join(err.get('correct_answers', []))
                print(f"   ✅ Risposta corretta: {correct_str}")
                
                # Align multi-line explanation
                exp = err['explanation']
                if exp:
                    print(f"   📖 Spiegazione:")
                    for line in exp.split('\n'):
                        print(f"      {line}")
                print("")
            
            print("\n" + "-"*40 + "\n")
            print("Non ti preoccupare! Ho salvato questi errori nella tua lista di ripasso personalizzata.")
            print("Prova la modalità 3 per esercitarti di nuovo su questi concetti!")

        print("="*40 + "\n")


