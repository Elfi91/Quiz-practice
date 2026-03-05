import json
import os
import datetime
from datetime import timedelta
from typing import List, Dict, Any


class DataManager:
    """Manages the reading and writing of error data to a JSON file."""

    def __init__(self, file_path: str = "errori.json"):
        self.file_path = file_path

    def load_errors(self) -> List[Dict[str, Any]]:
        """Loads errors from the JSON file."""
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_error(self, error_data: Dict[str, Any]) -> None:
        """Saves a new error entry to the JSON file, preventing duplicates."""
        errors = self.load_errors()
        
        # Check if error with same question already exists
        existing_index = next((i for i, e in enumerate(errors) if e.get("question") == error_data.get("question")), None)
        
        if existing_index is not None:
            # Update existing entry (e.g. update timestamp, keep other fields)
            errors[existing_index] = error_data
        else:
            # Append new entry
            errors.append(error_data)
        
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(errors, f, ensure_ascii=False, indent=4)

    def load_local_questions(self, path: str = "domande_locali.json") -> List[Dict[str, Any]]:
        """Loads fallback questions from a local JSON file."""
        if not os.path.exists(path):
            return []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def load_level_questions(self, filename: str) -> List[Dict[str, Any]]:
        """
        Loads questions from a specific level file in the data/ directory.
        READ-ONLY: This method only reads files. There are no methods to write to level files,
        ensuring immutability of the educational content.
        """
        path = os.path.join("data", filename)
        if not os.path.exists(path):
             return []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_progress(self, session_data: Dict[str, Any]) -> None:
        """Saves session statistics to progress.json."""
        progress_file = "progress.json"
        history = []
        
        if os.path.exists(progress_file):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = [] # Reset if corrupted
        
        history.append(session_data)
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    def remove_error(self, question_text: str) -> None:
        """Removes an error from the JSON file by matching the question text."""
        errors = self.load_errors()
        # Filter out the error with the matching question
        new_errors = [e for e in errors if e.get("question") != question_text]
        
        if len(new_errors) < len(errors):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(new_errors, f, ensure_ascii=False, indent=4)

    def get_weekly_stats(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns a dictionary with dates (last 7 days) mapped to a list of session dictionaries.
        Keys are 'YYYY-MM-DD'.
        Values are Lists of session dicts (from progress.json).
        """
        progress_file = "progress.json"
        if not os.path.exists(progress_file):
             return {}
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except json.JSONDecodeError:
            return {}

        today = datetime.date.today()
        stats = {} 
        
        # Initialize last 7 days with empty list
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            stats[d.isoformat()] = []
            
        for entry in history:
            ts = entry.get("timestamp")
            if ts:
                try:
                    dt = datetime.datetime.fromisoformat(ts).date()
                    iso_date = dt.isoformat()
                    if iso_date in stats:
                        stats[iso_date].append(entry)
                except ValueError:
                    continue
                    
        return stats

    def get_errors_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Returns a list of errors for a specific date (YYYY-MM-DD).
        """
        all_errors = self.load_errors()
        filtered = []
        
        for err in all_errors:
            ts = err.get("timestamp")
            if ts:
                try:
                    dt = datetime.datetime.fromisoformat(ts).date()
                    if dt.isoformat() == date_str:
                        filtered.append(err)
                except ValueError:
                    continue
        
        return filtered
