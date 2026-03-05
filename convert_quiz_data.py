import json
import os
import re
import shutil
import glob

DATA_DIR = 'data'
BACKUP_DIR = os.path.join(DATA_DIR, 'backup_original')

def clean_html(raw_html):
    """Remove HTML tags from a string."""
    if not isinstance(raw_html, str):
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def convert_quiz_file(file_path):
    filename = os.path.basename(file_path)
    print(f"Processing {filename}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error decoding {filename}, skipping.")
        return

    # Check if file is already converted (list of questions vs dict with 'results')
    if isinstance(data, list):
        print(f"{filename} seems to be already converted or in a different format. Skipping.")
        return
    
    if 'results' not in data:
        print(f"Key 'results' not found in {filename}. Skipping.")
        return

    transformed_data = []
    
    for item in data['results']:
        original_id = item.get('id')
        prompt = item.get('prompt', {})
        
        # 1. Extract and Clean Question Text
        # Use question_plain if available, otherwise strip HTML from prompt['question']
        question_text = item.get('question_plain')
        if not question_text:
            question_text = clean_html(prompt.get('question', ''))
            
        # 2. Process Options and Format Question
        # Embed options into the question text: "Question?\n\nA) Option A\nB) Option B..."
        options = prompt.get('answers', [])
        formatted_options = []
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        
        for idx, opt_html in enumerate(options):
            if idx >= len(letters):
                break
            opt_text = clean_html(opt_html)
            letter = letters[idx]
            formatted_options.append(f"{letter}) {opt_text}")
            
        if formatted_options:
            question_text += "\n\n" + "\n".join(formatted_options)
            
        # 3. Process Correct Answers
        # 'correct_response' is a list like ["a"] or ["b"] corresponding to index
        correct_indices_chars = item.get('correct_response', []) # e.g. ["a"]
        correct_answers = []
        
        for char in correct_indices_chars:
            char_lower = char.lower()
            # Convert 'a' to 0, 'b' to 1, etc.
            if len(char_lower) == 1 and 'a' <= char_lower <= 'z':
                idx = ord(char_lower) - ord('a')
                if 0 <= idx < len(options):
                    # Add the letter (uppercase preferred for display/matching)
                    correct_answers.append(letters[idx])
                    # Add the full text of the answer
                    full_text = clean_html(options[idx])
                    if full_text:
                        correct_answers.append(full_text)
        
        # 4. Extract Explanation
        explanation = clean_html(prompt.get('explanation', ''))
        
        # 5. Extract Keywords/Tags
        # Use 'section' as a keyword
        keywords = []
        section = item.get('section')
        if section:
            keywords.append(section)
            
        # Construct the new object
        new_item = {
            "id": original_id, # Keep ID for reference
            "question": question_text,
            "correct_answers": correct_answers,
            "explanation": explanation,
            "keywords": keywords
        }
        
        transformed_data.append(new_item)
        
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully converted {filename}. Saved {len(transformed_data)} questions.")

def main():
    # 1. Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")
    
    # 2. Find all quiz files
    quiz_files = glob.glob(os.path.join(DATA_DIR, 'quiz_*.json'))
    
    if not quiz_files:
        print("No quiz_*.json files found in data directory.")
        return

    # 3. Process each file
    for file_path in quiz_files:
        filename = os.path.basename(file_path)
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        # Copy to backup if not already there (to avoid overwriting backup with broken data if run multiple times)
        if not os.path.exists(backup_path):
            shutil.copy2(file_path, backup_path)
            print(f"Backed up {filename} to {BACKUP_DIR}")
        else:
            print(f"Backup for {filename} already exists. Skipping backup.")
            
        convert_quiz_file(file_path)

if __name__ == "__main__":
    main()
