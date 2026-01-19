import os
import sys
import datetime
from dotenv import load_dotenv
from gemini_client import GeminiClient
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
 🇮🇹  Italian Tutor for German Speakers 🇩🇪
    """
    print(art)

def main():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("❌ Error: GEMINI_API_KEY is missing or invalid in .env file.")
        print("Please set your API key in the .env file.")
        sys.exit(1)

    try:
        # Initialize components
        client = GeminiClient(api_key=api_key)
        data_manager = DataManager()
        engine = QuizEngine(client, data_manager)

        # Start App
        print_welcome_art()
        
        while True:
            # Mode Selection
            print("\n--- Main Menu (v2.0 - Detailed Stats) ---")
            print("1. Online (AI Generated)")
            print("2. Offline (Local Questions)")
            print("3. Review Errors (Personalized)")
            print("4. View Statistics")
            print("q. Quit")
            mode_choice = input("Choice: ").strip().lower()
            
            if mode_choice in ['q', 'quit', 'exit']:
                print("Arrivederci! / Auf Wiedersehen! 👋")
                sys.exit(0)
            
            if mode_choice == "4":
                stats = data_manager.get_weekly_stats()
                if not stats:
                    print("\nNo statistics available yet.")
                    input("\nPress Enter to return to menu...")
                    continue

                print("\n📊 Activity (Last 7 Days):")
                # Store valid days for quick lookup
                valid_days = {}
                
                for date_iso in sorted(stats.keys()):
                    sessions_list = stats[date_iso]
                    
                    # Aggregate daily totals
                    daily_sessions = len(sessions_list)
                    daily_questions = sum(s.get('total', 0) for s in sessions_list)
                    daily_score = sum(s.get('score', 0) for s in sessions_list)
                    daily_errors = daily_questions - daily_score
                    
                    dt = datetime.date.fromisoformat(date_iso)
                    day_name = dt.strftime("%a")
                    day_num = str(dt.day)
                    valid_days[day_num] = date_iso
                    
                    # Summary Line
                    bar = "▀" * daily_sessions
                    if daily_sessions > 0:
                        print(f"{day_name} {dt.day:02d}: {bar} [{daily_sessions} sess] | {daily_questions} Qs | {daily_score} OK | {daily_errors} NO")
                    else:
                        print(f"{day_name} {dt.day:02d}: -")
                
                print("-" * 40)
                detail_choice = input("Enter day number (e.g. 19) to view details, or Enter to go back: ").strip()
                
                if detail_choice in valid_days:
                    target_date = valid_days[detail_choice]
                    target_sessions = stats[target_date]
                    
                    print(f"\n📅 Details for {target_date}:")
                    
                    session_timestamps = []
                    if not target_sessions:
                         print("   No sessions recorded.")
                    else:
                        for sess in target_sessions:
                            ts = sess.get('timestamp', '')
                            time_str = "??"
                            if ts:
                                try:
                                    dt_sess = datetime.datetime.fromisoformat(ts)
                                    time_str = dt_sess.strftime("%H:%M")
                                    session_timestamps.append(dt_sess)
                                except ValueError:
                                    pass
                            
                            mode = "Online" if sess.get('mode') == 'online' else "Offline"
                            s_score = sess.get('score', 0)
                            s_total = sess.get('total', 0)
                            print(f"   - {time_str} {mode}: {s_score}/{s_total}")

                    # Error Review for this specific day (Smart Filter)
                    # Only show errors if they match the visible sessions (time window heuristic)
                    if session_timestamps:
                        # Strict Check: If visible stats show 0 errors, don't look for ghosts.
                        visible_total_errors = sum((s.get('total', 0) - s.get('score', 0)) for s in target_sessions)
                        
                        if visible_total_errors == 0:
                            print("\n✨ Perfect score! No errors to review for these sessions.")
                            input("\nPress Enter to return...")
                        else:
                            all_errors = data_manager.load_errors()
                            day_errors = []
                            
                            for e in all_errors:
                                e_ts = e.get('timestamp', '')
                                if not e_ts: continue
                                
                                try:
                                    e_dt = datetime.datetime.fromisoformat(e_ts)
                                    # Check if it's the same day
                                    if e_dt.date() != datetime.date.fromisoformat(target_date):
                                        continue
                                    
                                    # Check time proximity to ANY session of that day (within 10 mins before session end)
                                    # Session timestamp is usually "End Time" of session.
                                    is_relevant = False
                                    for s_dt in session_timestamps:
                                        # If error is within [SessionTime - 10min, SessionTime + 5min] (buffer)
                                        # Reduced window to avoid "ghost" errors from deleted past sessions
                                        diff = (s_dt - e_dt).total_seconds()
                                        # If diff is positive, error happened before session save.
                                        # 10 mins = 600 seconds
                                        if -300 <= diff <= 600: 
                                            is_relevant = True
                                            break
                                    
                                    if is_relevant:
                                        day_errors.append(e)

                                except ValueError:
                                    continue
                            
                            if day_errors:
                                print(f"\n⚠️  Found {len(day_errors)} errors linked to these sessions.")
                                do_practice = input("Practice these errors? (y/n): ").strip().lower()
                                if do_practice in ['y', 'yes', 's', 'si']:
                                     print(f"\n🚀 Starting Quick Review for {target_date}...")
                                     engine.run(offline_mode=True, custom_questions=day_errors, session_length=len(day_errors), silent_start=True)
                                     input("\nReview complete. Press Enter to return to stats...")
                            else:
                                print("\n✨ No errors recorded for these sessions!")
                                input("\nPress Enter to return...")
                    else:
                         input("\nPress Enter to return...")

                continue

            offline_mode = mode_choice == "2" or mode_choice == "3"
            custom_questions = []

            # REVIEW ERRORS MODE
            if mode_choice == "3":
                saved_errors = data_manager.load_errors()
                if not saved_errors:
                    print("🎉 Great news! You have no saved errors to review.")
                    print("Try a normal quiz to practice more!")
                    continue
                
                print(f"📂 Found {len(saved_errors)} errors to review.")
                action = input("Type 'p' to practice immediately, 'v' to view list, or 'b' to back: ").strip().lower()
                
                if action == 'v':
                    # Print the list of errors
                    print(f"\n--- Error List ---")
                    for i, err in enumerate(saved_errors, 1):
                        q_text = err.get('question', '').split('\n')[0]
                        u_ans = err.get('user_answer', '-')
                        c_ans = ', '.join(err.get('correct_answers', [])) if 'correct_answers' in err else 'N/A'
                        exp = err.get('explanation', '')
                        
                        print(f"{i}. {q_text}")
                        print(f"   ❌ Errore: {u_ans}")
                        print(f"   ✅ Corretto: {c_ans}")
                        
                        if exp:
                            print(f"   📖 Spiegazione:")
                            exp_lines = exp.split('\n')
                            for line in exp_lines:
                                print(f"      {line}")
                        print("-" * 30)
                    
                    # Option to Practice after viewing
                    print("\n")
                    practice = input("Ready to practice these errors? (y/n): ").strip().lower()
                    if practice not in ['s', 'si', 'y', 'yes']:
                        continue
                
                elif action == 'p':
                    # Practice immediately
                    pass
                else:
                    # Cancel or Invalid
                    continue
                
                # Filter valid questions for the engine
                valid_questions = []
                for q in saved_errors:
                    if 'question' in q:
                         # Ensure minimal fields for engine execution
                         if 'correct_answers' not in q:
                              # If missing, we can't really grade it, but filtering avoids crash.
                              pass
                         valid_questions.append(q)

                custom_questions = valid_questions
                offline_mode = True
                
                if not custom_questions:
                     print("⚠️  No valid questions to review.")
                     continue

            # Level Selection (Online Mode)
            selected_level = "A1" # Default
            if mode_choice == "1":
                print("\nSelect Difficulty Level:")
                print("1. A1")
                print("2. A2")
                print("3. B1")
                print("4. B2")
                print("5. C1")
                print("6. C2")
                
                lvl_map = {"1": "A1", "2": "A2", "3": "B1", "4": "B2", "5": "C1", "6": "C2"}
                lvl_choice = input("Choice [Default A1]: ").strip()
                if lvl_choice in lvl_map:
                    selected_level = lvl_map[lvl_choice]
                else:
                    print("Defaulting to A1.")


            # OFFLINE LEVEL SELECTION
            elif mode_choice == "2":
                back_to_menu = False
                while True:
                    print("\nSelect Level:")
                    print("1. A1.1")
                    print("2. A1.2")
                    print("3. A2.1")
                    print("4. A2.2")
                    print("b. Back to Main Menu")
                    
                    level_choice = input("Choice: ").strip().lower()
                    
                    level_map = {
                        "1": "a1_1.json",
                        "2": "a1_2.json",
                        "3": "a2_1.json",
                        "4": "a2_2.json"
                    }

                    if level_choice == 'b':
                         back_to_menu = True
                         break

                    if level_choice in level_map:
                        filename = level_map[level_choice]
                        custom_questions = data_manager.load_level_questions(filename)
                        if not custom_questions:
                            print(f"❌ Error: Could not load questions from 'data/{filename}'. File missing or empty.")
                            continue 
                        
                        break 
                    else:
                        print("❌ Invalid choice. Please try again.")

                if back_to_menu:
                    continue

# ... 

                # OFFLINE SUB-MENU: Random or Category
                while True:
                    print("\nChoose Question Type:")
                    print("1. Random Questions")
                    print("2. By Category (In Progress)")
                    
                    sub_choice = input("Choice: ").strip()
                    
                    if sub_choice == "1":
                        break # Proceed to session length
                    elif sub_choice == "2":
                        print("\n🚧  Feature in progress. Please choose 'Random Questions' for now.")
                        # Loop back to ask again
                    else:
                        print("Invalid choice.")

            # Ask for Session Length (Skip for Review Mode, Mode 3)
            silent_start = False
            if mode_choice == "3":
                 session_length = len(custom_questions)
                 silent_start = True
            elif mode_choice == "2": # OFFLINE MODE
                print("\nHow many questions do you want to answer? (15 / 30 / 50)")
                length_input = input("Number [Default 15]: ").strip()
                session_length = 15
                if length_input in ["30", "50"]:
                    session_length = int(length_input)
                elif length_input and length_input != "15":
                    print("Invalid number. Using default: 15.")
            else: # ONLINE MODE
                print("\nHow many questions do you want to answer? (10 or 20)")
                length_input = input("Number [Default 10]: ").strip()
                
                session_length = 10
                if length_input:
                     if length_input == "20":
                         session_length = 20
                     elif length_input != "10":
                         print("Invalid number. Using default: 10.")

            engine.run(offline_mode=offline_mode, custom_questions=custom_questions, session_length=session_length, silent_start=silent_start, level=selected_level)
            
            # Prompt to return to menu
            print("\n" + "-"*40)
            cont = input("Vuoi tornare al menu principale? (s/n) / Back to menu? (y/n): ").strip().lower()
            if cont not in ['s', 'y', 'si', 'yes']:
                print("Arrivederci! / Auf Wiedersehen! 👋")
                break
            print("\n")
        
    except ValueError as e:
        print(f"Initialization Error: {e}")
    except ValueError as e:
        print(f"Initialization Error: {e}")
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
