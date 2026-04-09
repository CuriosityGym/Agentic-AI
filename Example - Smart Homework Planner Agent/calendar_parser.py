"""Parse .ics calendar files and extract events."""
from datetime import date, datetime, time

import pytz
from icalendar import Calendar


def parse_ics(file_path: str) -> list:
    try:
        with open(file_path, "rb") as fh:
            cal = Calendar.from_ical(fh.read())
    except Exception as exc:
        raise ValueError(f"Cannot parse .ics file: {exc}") from exc

    if not isinstance(cal, Calendar):
        raise ValueError("Uploaded file does not appear to be a valid iCalendar (.ics) file.")

    events = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        dtstart_prop = component.get("DTSTART")
        dtend_prop   = component.get("DTEND")
        if dtstart_prop is None or dtend_prop is None:
            continue

        try:
            dtstart = _to_aware_datetime(dtstart_prop.dt)
            dtend   = _to_aware_datetime(dtend_prop.dt)
        except Exception:
            continue

        events.append({
            "summary": str(component.get("SUMMARY", "No Title")),
            "start":   dtstart,
            "end":     dtend,
            "uid":     str(component.get("UID", "")),
        })

    events.sort(key=lambda e: e["start"])
    return events


def _to_aware_datetime(dt) -> datetime:
    if isinstance(dt, datetime):
        return dt if dt.tzinfo is not None else pytz.utc.localize(dt)
    return pytz.utc.localize(datetime.combine(dt, time(0, 0)))