# AWS Quiz Tutor & Quiz Engine

A versatile quiz application offering both a Command Line Interface (CLI) and a Web Interface (Flask) to practice and master technical topics. Currently configured with a comprehensive dataset for **AWS Cloud Practitioner** preparation, the engine is designed to be content-agnostic and can be extended to other subjects (e.g., Language Learning).

## 🚀 Features

### Core Functionality
- **Dual Interface**: Use the application via terminal (`main.py`) or a modern web browser (`app.py`).
- **Flexible Quiz Modes**:
  - **Standard Quiz**: Select specific problem sets or a random mix of all available questions.
  - **Custom Session Length**: Choose standard (25, 50, 65) or custom number of questions.
  - **Timed Mode**: Simulate exam conditions with a countdown timer (default 90 mins for full exams).
- **Smart Error Tracking**:
  - Automatically saves incorrect answers to `errori.json`.
  - **Review Mode**: Dedicated mode to practice only previously missed questions.
  - **Spaced Repetition**: Errors are removed from the review list only after they are answered correctly.

### Web-Specific Features
- **Progress Dashboard**: Visual statistics of your study sessions over the last 7 days.
- **Session History**: Tracks scores, completion times, and modes.
- **Responsive Design**: Clean interface for studying on desktop or mobile.


## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set up a Virtual Environment** (Recommended)
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory. While the core quiz doesn't strictly require it, it is recommended for future configurations.
   ```bash
   # Add environment variables here
   ```

## 📖 Usage

### Command Line Interface (CLI)
The CLI provides a fast, distraction-free studying environment.

```bash
python main.py
```
**Menu Options:**
1. **Start Quiz**: Choose question sets and session parameters.
2. **Review Errors**: Practice questions you've previously missed.
3. **View Statistics**: See a summary of your recent performance.

### Web Interface
The Web App offers a richer UI with detailed explanations and stats.

```bash
python app.py
```
- Open your browser and navigate to `http://127.0.0.1:8000`
- **Home**: Start new quiz, choose modes.
- **Quiz**: Interactive question interface with immediate feedback.
- **Stats**: View weekly progress charts.

## 📂 Project Structure

- **`main.py`**: Entry point for the CLI application.
- **`app.py`**: Flask application for the Web Interface.
- **`data_manager.py`**: Handles loading questions, saving errors, and tracking progress.
- **`quiz_engine.py`**: Core logic for the CLI quiz loop.
- **`data/`**: JSON files containing question banks (e.g., `quiz_1.json`).
- **`templates/` & `static/`**: HTML and CSS files for the web interface.

## 📝 Data Format

Questions are stored in JSON format in the `data/` directory. Example structure:

```json
[
    {
        "id": 12345,
        "question": "What is ...?",
        "correct_answers": ["A", "Full Answer Text"],
        "explanation": "Detailed explanation of why...",
        "keywords": ["Topic", "Category"]
    }
]
```

