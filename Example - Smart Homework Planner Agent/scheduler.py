"""Core scheduling algorithm: fit homework tasks into free calendar slots."""
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from typing import Any

import pytz

from config import WORK_START_HOUR, WORK_END_HOUR, MIN_SLOT_MINUTES

WORK_START = time(WORK_START_HOUR, 0)
WORK_END   = time(WORK_END_HOUR, 0)


def schedule_homework(
    events: list,
    tasks: list,
    start_date: date,
    end_date: date,
    max_sessions_per_day: int = 2,
    max_session_minutes: int = 60,
    timezone: str = "UTC",
) -> tuple:
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        tz = pytz.utc

    tasks = deepcopy(tasks)
    tasks.sort(key=lambda t: t["due_date"])

    scheduled = []

    current = start_date
    while current <= end_date:
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        backlog = [t for t in tasks if t["remaining_minutes"] > 0 and t["due_date"] >= current]
        if not backlog:
            break

        sessions_today = 0
        free_slots = _get_free_slots(events, current, tz)

        for slot_start, slot_end in free_slots:
            if sessions_today >= max_sessions_per_day:
                break

            cursor = slot_start
            slot_available = _minutes(slot_start, slot_end)

            while slot_available >= MIN_SLOT_MINUTES and sessions_today < max_sessions_per_day:
                next_task = next((t for t in backlog if t["remaining_minutes"] > 0), None)
                if next_task is None:
                    break

                session_min = min(
                    float(max_session_minutes),
                    float(next_task["remaining_minutes"]),
                    slot_available,
                )
                if session_min < MIN_SLOT_MINUTES:
                    break

                session_end = cursor + timedelta(minutes=session_min)
                scheduled.append({
                    "task": next_task["name"],
                    "start": cursor.isoformat(),
                    "end": session_end.isoformat(),
                    "duration_minutes": int(session_min),
                })
                next_task["remaining_minutes"] -= int(session_min)
                cursor = session_end
                slot_available -= session_min
                sessions_today += 1

        current += timedelta(days=1)

    unscheduled = [t for t in tasks if t["remaining_minutes"] > 0]
    return scheduled, unscheduled


def _get_free_slots(events: list, day: date, tz: Any) -> list:
    work_start = tz.localize(datetime.combine(day, WORK_START))
    work_end   = tz.localize(datetime.combine(day, WORK_END))

    busy = []
    for ev in events:
        s = ev["start"].astimezone(tz)
        e = ev["end"].astimezone(tz)
        if e <= work_start or s >= work_end:
            continue
        busy.append((max(s, work_start), min(e, work_end)))

    busy.sort(key=lambda x: x[0])

    merged = []
    for s, e in busy:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])

    free = []
    cursor = work_start
    for s, e in merged:
        if _minutes(cursor, s) >= MIN_SLOT_MINUTES:
            free.append((cursor, s))
        cursor = max(cursor, e)

    if _minutes(cursor, work_end) >= MIN_SLOT_MINUTES:
        free.append((cursor, work_end))

    return free


def _minutes(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 60.0