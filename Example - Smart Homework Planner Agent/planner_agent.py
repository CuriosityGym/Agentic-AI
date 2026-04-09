"""Planner Agent – extract free slots and schedule homework tasks."""
from datetime import date
from config import MIN_SLOT_MINUTES
from scheduler import schedule_homework

def run_planner_agent(events: list, tasks: list, constraints: dict,
                      start_date: date, end_date: date) -> dict:
    """Schedule homework tasks into free calendar slots.
    
    Returns dict with: scheduled (list), unscheduled (list)
    """
    max_sessions = int(constraints.get("max_sessions_per_day", 2))
    max_duration  = int(constraints.get("max_session_minutes", 60))
    timezone      = str(constraints.get("timezone", "UTC"))

    scheduled, unscheduled = schedule_homework(
        events=events,
        tasks=tasks,
        start_date=start_date,
        end_date=end_date,
        max_sessions_per_day=max_sessions,
        max_session_minutes=max_duration,
        timezone=timezone,
    )
    return {"scheduled": scheduled, "unscheduled": unscheduled}