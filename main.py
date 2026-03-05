import os
import sys
import datetime
import random
from dotenv import load_dotenv
from data_manager import DataManager
from quiz_engine import QuizEngine

def print_welcome_art():
    art = r"""
  _      ______                  _
 | |    |  ____|                (_)
 | |    | |__   __ _ _ __ _ __   _ _ __   __ _
 | |    |  __| / _` | '__| '_ \ | | '_ \ / _` |
 | |____| |___| (_| | |  | | | || | | | | (_| |
 |______|______\__,_|_|  |_| |_||_|_| |_|\__, |
                                          __/ |
                                         |___/
   AWS Quiz Tutor 
    """
    print(art)

def main():
    # Load environment variables (mostly for data paths if needed)
    load_dotenv()
    
    try:
        # Initialize components
        data_manager = DataManager()
        engine = QuizEngine(data_manager)

        # Start App
        print_welcome_art()
        
        while True:
            # Main Menu
            print("\n--- Main Menu ---")
            print("1. Start Quiz")
            print("2. Review Errors")
            print("3. View Statistics")
            print("q. Quit")
            mode_choice = input("Choice: ").strip().lower()
            
            if mode_choice in ['q', 'quit', 'exit']:
                print("Goodbye! 👋")
                sys.exit(0)
            
            # --- START QUIZ ---
            if mode_choice == "1":
                # 1. Select Question Source
                questions = []
                print("\nSELECT QUESTION SET:")
                quiz_files = [f"quiz_{i}.json" for i in range(1, 7)] # quiz_1 to quiz_6
                for i, f in enumerate(quiz_files, 1):
                    print(f"{i}. Quiz {i}")
                print("a. All Questions (Mix)")
                
                src_choice = input("Choice: ").strip().lower()
                
                selected_files = []
                if src_choice == 'a':
                    selected_files = quiz_files
                elif src_choice.isdigit():
                    idx = int(src_choice) - 1
                    if 0 <= idx < len(quiz_files):
                        selected_files = [quiz_files[idx]]
                    else:
                        print("Invalid selection.")
                        continue
                else:
                    print("Invalid selection.")
                    continue

                # Load questions
                for f in selected_files:
                    path = os.path.join("data", f) # Use relative path for data_manager
                    # load_local_questions takes full path? data_manager implementation used os.path.exists(path)
                    # Let's ensure we pass correct path.
                    # DataManager.load_local_questions uses "domande_locali.json" default, but takes 'path' arg.
                    # We will use full path to be safe.
                    full_path = os.path.abspath(path)
                    file_qs = data_manager.load_local_questions(full_path)
                    if file_qs:
                        questions.extend(file_qs)
                    else:
                        print(f"⚠️  Warning: Could not load {f}")

                if not questions:
                    print("❌ No questions loaded. Returning to menu.")
                    continue
                
                print(f"✅ Loaded {len(questions)} questions total.")

                # 2. Select Question Count
                print("\nHOW MANY QUESTIONS?")
                print("1. 25")
                print("2. 50")
                print("3. 65")
                print("c. Custom")
                
                count_map = {"1": 25, "2": 50, "3": 65}
                count_choice = input("Choice: ").strip().lower()
                
                session_length = 25 # Default
                if count_choice in count_map:
                    session_length = count_map[count_choice]
                elif count_choice == 'c':
                    try:
                        session_length = int(input("Enter number: "))
                    except ValueError:
                        print("Invalid number. Using default 25.")
                else:
                    print("Invalid choice. Using default 25.")

                # 3. Timer Option
                print("\nENABLE TIMER?")
                print("1. Standard (90 minutes for 60 questions ratio)")
                print("2. No Timer")
                
                timer_choice = input("Choice: ").strip()
                time_limit = None
                
                if timer_choice == "1":
                    # Simple rule: If session length is around 60, give 90 mins.
                    # Let's verify user request: "Timer 60 questions in 90 minutes"
                    # We can proportionalize it: 1.5 minutes per question?
                    # 90 / 60 = 1.5 mins/question.
                    # 25 questions * 1.5 = 37.5 mins.
                    # Or just 90 mins fixed?
                    # "Aggiungi un timer 60 domande in 90 minuti" sounds like a standard exam format.
                    # Let's stick to 90 minutes if count is high, or just 90 minutes fixed.
                    # Actually, let's just use 90 minutes as the "Examination Mode".
                    time_limit = 90
                
                # RUN QUIZ
                engine.run(questions, session_length=session_length, time_limit_minutes=time_limit)
                
                # End of quiz pause
                input("\nPress Enter to return to menu...")
                
            # --- REVIEW ERRORS ---
            elif mode_choice == "2":
                saved_errors = data_manager.load_errors()
                if not saved_errors:
                    print("🎉 No errors to review.")
                    input("\nPress Enter to return...")
                    continue
                
                print(f"📂 Found {len(saved_errors)} errors.")
                action = input("Type 'p' to practice, 'v' to view list: ").strip().lower()
                
                if action == 'v':
                     for i, err in enumerate(saved_errors, 1):
                        q_text = err.get('question', '').split('\n')[0]
                        print(f"{i}. {q_text}")
                        print(f"   Correct: {err.get('correct_answers', 'N/A')}")
                        print("-" * 20)
                     action = input("Practice these errors? (y/n): ").strip().lower()
                     if action not in ['y', 'yes', 's', 'si']:
                         continue
                         
                if action == 'p' or action in ['y', 'yes', 's', 'si']:
                     engine.run(saved_errors, session_length=len(saved_errors), time_limit_minutes=None, silent_start=True)
                     input("\nPress Enter to return...")

            # --- STATISTICS ---
            elif mode_choice == "3":
                stats = data_manager.get_weekly_stats()
                if not stats:
                    print("\nNo statistics available.")
                else:
                     print("\n📊 Activity (Last 7 Days):")
                     for date_iso in sorted(stats.keys()):
                        sessions_list = stats[date_iso]
                        if not sessions_list:
                            continue
                        
                        daily_score = sum(s.get('score', 0) for s in sessions_list)
                        daily_total = sum(s.get('total', 0) for s in sessions_list)
                        print(f"{date_iso}: {len(sessions_list)} sessions | Score: {daily_score}/{daily_total}")
                
                input("\nPress Enter to return...")

            else:
                print("Invalid choice.")

        
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
