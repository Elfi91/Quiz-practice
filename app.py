from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
import random
import datetime
import time
from data_manager import DataManager

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_quiz_app' # Change this for production

data_manager = DataManager()

def normalize_text(text):
    """Normalizes text for answer checking."""
    if not text:
        return ""
    text = text.lower().strip()
    for char in ['.', '!', '?']:
        text = text.replace(char, "")
    return text

import uuid

QUIZ_SESSIONS = {} # Server-side session storage

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_quiz():
    source = request.form.get('source')
    count_option = request.form.get('count')
    timer_option = request.form.get('timer')
    custom_count = request.form.get('custom_count')

    # ... (Load Questions Logic - Same as before) ...
    # 1. Load Questions
    questions = []
    quiz_files = [f"quiz_{i}.json" for i in range(1, 7)]
    selected_files = []

    if source == 'all':
        selected_files = quiz_files
        for f in selected_files:
            path = os.path.abspath(os.path.join("data", f))
            file_qs = data_manager.load_local_questions(path)
            if file_qs:
                questions.extend(file_qs)

    elif source == 'errors':
        questions = data_manager.load_errors()
        if not questions:
            return "No errors found to practice! Great job! 🎉", 200

    elif source == 'retry_current':
        prev_session_id = request.form.get('prev_session_id')
        if prev_session_id and prev_session_id in QUIZ_SESSIONS:
            # Reconstruct questions from errors
            prev_errors = QUIZ_SESSIONS[prev_session_id].get('errors', [])
            questions = prev_errors # Errors are stored in compatible format
        
        if not questions:
             return "No errors to retry from that session.", 200

    elif source == 'errors_by_date':
        date_str = request.form.get('date')
        if date_str:
            questions = data_manager.get_errors_by_date(date_str)
            if not questions:
                return f"No errors found for {date_str}.", 200
        else:
            return "Date missing for error practice.", 400

    elif source and source.isdigit():
        idx = int(source) - 1
        if 0 <= idx < len(quiz_files):
            selected_files = [quiz_files[idx]]
            path = os.path.abspath(os.path.join("data", selected_files[0])) # Only one file
            questions = data_manager.load_local_questions(path)
    
    if not questions:
        return "Error: No questions loaded.", 400

    random.shuffle(questions)

    # 2. Slice Count
    session_length = 25 # default
    if count_option == '25': session_length = 25
    elif count_option == '50': session_length = 50
    elif count_option == '65': session_length = 65
    elif count_option == 'custom':
        try:
            session_length = int(custom_count)
            if session_length < 1: session_length = 1 # Minimum 1 question
        except (ValueError, TypeError):
            session_length = 25
    
    if len(questions) > session_length:
        questions = questions[:session_length]
    else:
        session_length = len(questions)

    # 3. Timer Setup
    time_limit = None # Minutes
    if timer_option == 'auto' or timer_option == '90': # keep '90' for backward compatibility or if user didn't refresh
        # Calculate roughly 1.38 minutes per question (90 mins / 65 questions)
        # Using math.ceil to be generous or round? User said "calculate... starting from this one"
        # 65 questions -> 90 mins.
        # Ratio = 90 / 65
        ratio = 90 / 65
        time_limit = int(session_length * ratio)
        if time_limit < 1: time_limit = 1 # Minimum 1 minute
    
    end_timestamp = None
    if time_limit:
        end_timestamp = time.time() + (time_limit * 60)

    # 4. Initialize Server-Side Session
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id # Store ID in cookie
    
    QUIZ_SESSIONS[session_id] = {
        'questions': questions,
        'total_questions': session_length,
        'current_index': 0,
        'score': 0,
        'errors': [],
        'start_time': time.time(),
        'end_timestamp': end_timestamp,
        'time_limit_minutes': time_limit,
        'user_answers': {}
    }

    return redirect(url_for('quiz'))

@app.route('/quiz')
def quiz():
    session_id = session.get('session_id')
    if not session_id or session_id not in QUIZ_SESSIONS:
        return redirect(url_for('index'))
    
    quiz_data = QUIZ_SESSIONS[session_id]
    idx = quiz_data['current_index']
    total = quiz_data['total_questions']
    
    if idx >= total:
        return redirect(url_for('result'))
    
    question = quiz_data['questions'][idx]
    
    # Parse options ... (Same logic)
    text_content = question.get('question', '')
    lines = text_content.split('\n')
    main_text = []
    options = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        if len(line) > 2 and line[0].isalpha() and line[1] in [')', '.']:
             options.append({'id': line[0].lower(), 'text': line})
        elif options: 
             pass 
        else:
             main_text.append(line)
             
    display_question = "\n".join(main_text)
    if not options:
        display_question = text_content
    
    check_result = quiz_data.pop('last_check_result', None)
    
    user_answers = quiz_data.get('user_answers', {}).get(str(idx), [])
    if isinstance(user_answers, str):
        user_answers = [user_answers]
        
    return render_template('quiz.html', 
                           question=question, 
                           display_question=display_question,
                           options=options,
                           index=idx + 1, 
                           total=total,
                           end_timestamp=quiz_data.get('end_timestamp'),
                           user_answer=user_answers,
                           check_result=check_result)

@app.route('/submit', methods=['POST'])
def submit_answer():
    session_id = session.get('session_id')
    if not session_id or session_id not in QUIZ_SESSIONS:
        return redirect(url_for('index'))
    
    quiz_data = QUIZ_SESSIONS[session_id]
    idx = quiz_data['current_index']
    questions = quiz_data['questions']
    
    if idx >= len(questions):
        return redirect(url_for('result'))

    action = request.form.get('action')
    user_answer_list = request.form.getlist('answer')
    # filter out empty strings
    user_answer_list = [ans.strip() for ans in user_answer_list if ans.strip()]
    
    # Save the current answer if provided
    if user_answer_list:
        if 'user_answers' not in quiz_data:
            quiz_data['user_answers'] = {}
        quiz_data['user_answers'][str(idx)] = user_answer_list

    # Navigation logic
    if action == 'prev':
        quiz_data['current_index'] = max(0, idx - 1)
        return redirect(url_for('quiz'))
    elif action == 'next':
        quiz_data['current_index'] = min(len(questions) - 1, idx + 1)
        return redirect(url_for('quiz'))
    elif action == 'check':
        current_q = questions[idx]
        raw_correct = current_q.get("correct_answers", [])
        normalized_correct = [normalize_text(ans) for ans in raw_correct]
        cleaned_user_list = [normalize_text(ans) for ans in user_answer_list]
        
        is_correct = False
        if len(cleaned_user_list) > 0:
            # Check if user submitted letters and correct answers are letters
            user_letters = set(ans for ans in cleaned_user_list if len(ans) == 1 and ans.isalpha())
            correct_letters = set(ans.lower() for ans in raw_correct if len(ans) <= 2) # e.g. "a" or "a)"
            # also extract letters from normalized_correct if they are single letters
            correct_letters.update(ans for ans in normalized_correct if len(ans) == 1 and ans.isalpha())
            
            if len(user_letters) == len(cleaned_user_list) and len(raw_correct) > 0:
                # User provided only letter answers (like ['a', 'c'])
                is_correct = user_letters == correct_letters
            else:
                is_correct = set(cleaned_user_list) == set(normalized_correct)

        quiz_data['last_check_result'] = {
            'is_correct': is_correct,
            'correct_answers': raw_correct,
            'explanation': current_q.get('explanation')
        }
        return redirect(url_for('quiz'))
    elif action == 'finish':
        quiz_data['score'] = 0
        quiz_data['errors'] = []
        user_answers = quiz_data.get('user_answers', {})
        
        for i, q in enumerate(questions):
            ans_list = user_answers.get(str(i), [])
            if isinstance(ans_list, str):
                ans_list = [ans_list]
            ans_list = [ans.strip() for ans in ans_list if ans.strip()]
            
            raw_correct = q.get("correct_answers", [])
            normalized_correct = [normalize_text(c) for c in raw_correct]
            cleaned_user_list = [normalize_text(ans) for ans in ans_list]
            
            is_correct = False
            if len(cleaned_user_list) > 0:
                user_letters = set(ans for ans in cleaned_user_list if len(ans) == 1 and ans.isalpha())
                correct_letters = set(ans.lower() for ans in raw_correct if len(ans) <= 2)
                correct_letters.update(ans for ans in normalized_correct if len(ans) == 1 and ans.isalpha())
                if len(user_letters) == len(cleaned_user_list) and len(raw_correct) > 0:
                    is_correct = user_letters == correct_letters
                else:
                    is_correct = set(cleaned_user_list) == set(normalized_correct)
                
            if is_correct:
                quiz_data['score'] += 1
                data_manager.remove_error(q.get('question'))
            else:
                error_entry = {
                    "question": q.get('question'),
                    "user_answer": ", ".join(ans_list),
                    "correct_answers": raw_correct,
                    "explanation": q.get('explanation'),
                    "keywords": q.get('keywords', [])
                }
                quiz_data['errors'].append(error_entry)
                
                error_entry_save = error_entry.copy()
                error_entry_save['timestamp'] = datetime.datetime.now().isoformat()
                data_manager.save_error(error_entry_save)
        
        quiz_data['current_index'] = len(questions)
        return redirect(url_for('result'))
    
    # Fallback (e.g. submit without JS button)
    if idx < len(questions) - 1:
        quiz_data['current_index'] += 1
    return redirect(url_for('quiz'))

@app.route('/result')
def result():
    session_id = session.get('session_id')
    if not session_id or session_id not in QUIZ_SESSIONS:
        return redirect(url_for('index'))
        
    quiz_data = QUIZ_SESSIONS[session_id]
    score = quiz_data['score']
    total = quiz_data['total_questions']
    errors = quiz_data['errors']
    
    session_stats = {
        "timestamp": datetime.datetime.now().isoformat(),
        "mode": "web_timed" if quiz_data.get('time_limit_minutes') else "web_standard",
        "score": score,
        "total": total,
        "percentage": round((score / total * 100) if total > 0 else 0, 2)
    }
    data_manager.save_progress(session_stats)
    
    # Cleanup session logic could be added here (e.g. keep for 1 hour or clear on explicit exit)
    # For now, we leave it in memory.
    
    return render_template('result.html', score=score, total=total, errors=errors)

@app.route('/stats')
def stats():
    weekly_stats = data_manager.get_weekly_stats()
    return render_template('stats.html', weekly_stats=weekly_stats)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
