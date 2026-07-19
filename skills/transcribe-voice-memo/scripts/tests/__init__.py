"""Test suite for transcribe-voice-memo skill.

Run all tests:
    python -m unittest discover -s tests -v
    # or IF YOU IMPORT pytest
    python -m pytest tests/ 

Run specific test module:
    python -m unittest tests.test_voice_memo -v
    python -m unittest tests.test_mode_selection -v
"""

import sys
from pathlib import Path

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))
