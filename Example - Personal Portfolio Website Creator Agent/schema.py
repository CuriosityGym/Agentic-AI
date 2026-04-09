"""
Data schema for student portfolio information.
Defines the structure of data collected through the chat interface.
"""

from copy import deepcopy


# Default empty student data schema
DEFAULT_STUDENT_DATA = {
    "name": "",
    "school": "",
    "grade": "",
    "introduction": "",
    "links": [],           # [{"name": "github", "url": "https://..."}]
    "hobbies": [],         # ["reading", "coding", ...]
    "interests": [],       # ["AI", "music", ...]
    "skills": [],          # ["Python", "HTML", ...]
    "courses": [],         # ["Computer Science", "Math", ...]
    "projects": [          # List of project dicts
        # {
        #   "name": "",
        #   "description": "",
        #   "file_path": ""
        # }
    ],
    "theme_preference": "" # e.g. "dark", "light", "colorful"
}


def new_student_data() -> dict:
    """Return a fresh deep copy of the default student data schema."""
    return deepcopy(DEFAULT_STUDENT_DATA)


def validate_student_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validate that required fields are populated.
    Returns (is_valid, list_of_missing_fields).
    """
    required_fields = ["name", "school", "grade", "introduction"]
    missing = [f for f in required_fields if not data.get(f, "").strip()]
    return (len(missing) == 0, missing)
