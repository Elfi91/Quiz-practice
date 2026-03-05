import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import builtins
from unittest.mock import patch
import main

# Mock inputs for the flow:
# 1. "1" (Start Quiz)
# 2. "2" (Quiz 2)
# 3. "1" (25 questions)
# 4. "1" (Enable Timer)
# 5. "exit" (Quit quiz during question loop)
# 6. "q" (Quit main menu)

inputs = iter(["1", "2", "1", "1", "exit", "q"])

def mock_input(prompt=""):
    print(f"[MOCK INPUT] {prompt}", end="")
    try:
        val = next(inputs)
        print(val)
        return val
    except StopIteration:
        print("\n[MOCK] No more inputs")
        sys.exit(0)

def test_flow():
    print("🚀 Starting Menu Flow Test...")
    with patch('builtins.input', side_effect=mock_input):
        try:
            main.main()
        except SystemExit:
            print("\n✅ Test completed (SystemExit expected).")
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_flow()
