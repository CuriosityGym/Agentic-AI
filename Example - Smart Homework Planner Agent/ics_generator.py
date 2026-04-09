"""Generate a new .ics calendar file from existing events and scheduled sessions."""
import tempfile
import uuid
from datetime import datetime

import pytz
from icalendar import Calendar, Event


def generate_ics(original_events: list, scheduled_sessions: list, timezone: str = "UTC") -> str:
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        tz = pytz.utc

    cal = Calendar()
    cal.add("prodid",     "-//Smart Homework Planner//EN")
    cal.add("version",    "2.0")
    cal.add("calscale",   "GREGORIAN")
    cal.add("x-wr-calname", "Smart Homework Schedule")

    for session in scheduled_sessions:
        start_dt = _parse_iso_aware(session["start"], tz)
        end_dt   = _parse_iso_aware(session["end"],   tz)

        vevent = Event()
        vevent.add("summary",     f"📚 Study: {session['task']}")
        vevent.add("dtstart",     start_dt)
        vevent.add("dtend",       end_dt)
        vevent.add("uid",         str(uuid.uuid4()))
        vevent.add("description", f"Homework session – {session['duration_minutes']} min\nTask: {session['task']}")
        vevent.add("categories",  ["Homework"])
        cal.add_component(vevent)

    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix="smart_homework_schedule_",
        suffix=".ics",
        delete=False,
    ) as fh:
        fh.write(cal.to_ical())
        return fh.name


def _parse_iso_aware(iso_str: str, tz) -> datetime:
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    else:
        dt = dt.astimezone(tz)
    return dt