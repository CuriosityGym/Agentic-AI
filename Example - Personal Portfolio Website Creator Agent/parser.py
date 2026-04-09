"""
Parsing utilities for user input collected from the chat interface.

Handles:
  - Social link extraction from labeled text (e.g. "Github: https://...")
  - Comma/newline-separated list splitting (hobbies, skills, etc.)
"""

import re
from typing import Union


def parse_links(raw_input: str) -> list[dict]:
    """
    Parse labeled social / website links from free-form text.

    Accepted formats (one per line):
        Github: https://github.com/user
        Instagram: https://instagram.com/user
        Portfolio: https://mysite.com

    Returns:
        [{"name": "github", "url": "https://github.com/user"}, ...]
    """
    links = []
    if not raw_input or not raw_input.strip():
        return links

    # URL regex – intentionally permissive for common HTTP(S) URLs
    url_pattern = re.compile(
        r"https?://[^\s\"'<>]+"
    )

    for line in raw_input.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # Try "Label: URL" format
        if ":" in line:
            # Split only on first colon that is followed by "//" (part of URL)
            # Label may contain a colon itself, so split carefully
            match = re.match(r"^([^:]+?):\s*(https?://.+)$", line, re.IGNORECASE)
            if match:
                label = match.group(1).strip().lower()
                url = match.group(2).strip()
                links.append({"name": label, "url": url})
                continue

        # Fallback: extract any bare URL on the line
        url_match = url_pattern.search(line)
        if url_match:
            links.append({"name": "link", "url": url_match.group()})

    return links


def parse_list(raw_input: str) -> list[str]:
    """
    Parse a comma or newline-separated list into a cleaned Python list.

    Example input:  "Python, JavaScript\nReact, Node.js"
    Returns:        ["Python", "JavaScript", "React", "Node.js"]
    """
    if not raw_input or not raw_input.strip():
        return []

    # Replace newlines with commas, then split
    normalised = raw_input.replace("\n", ",")
    items = [item.strip() for item in normalised.split(",")]
    return [item for item in items if item]


def parse_name_school_grade(raw_input: str) -> tuple[str, str, str]:
    """
    Try to extract Name, School, and Grade from a multi-line or
    comma-separated response.

    Expected format (flexible):
        Name: Alice
        School: MIT High School
        Grade: 10

    Falls back to positional splitting if labels are absent.

    Returns:
        (name, school, grade)  – any missing field is returned as "".
    """
    name = school = grade = ""

    lines = [l.strip() for l in raw_input.strip().splitlines() if l.strip()]

    label_map = {
        "name": "",
        "school": "",
        "grade": "",
    }

    for line in lines:
        lower = line.lower()
        for key in label_map:
            if lower.startswith(key + ":"):
                value = line[len(key) + 1:].strip()
                label_map[key] = value
                break

    name = label_map["name"]
    school = label_map["school"]
    grade = label_map["grade"]

    # Positional fallback when labels were not used
    if not name and len(lines) >= 1:
        name = lines[0]
    if not school and len(lines) >= 2:
        school = lines[1]
    if not grade and len(lines) >= 3:
        grade = lines[2]

    return name, school, grade
