"""Calendar Agent – merge original events with homework sessions and emit .ics."""
from ics_generator import generate_ics

def run_calendar_agent(original_events: list, scheduled_sessions: list,
                       timezone: str = "UTC") -> str:
    """Generate a new .ics file with scheduled homework sessions.
    
    Returns the absolute path to the generated .ics file.
    """
    return generate_ics(
        original_events=original_events,
        scheduled_sessions=scheduled_sessions,
        timezone=timezone,
    )