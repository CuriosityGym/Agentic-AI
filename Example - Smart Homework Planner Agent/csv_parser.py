"""Parse homework task CSV files."""
from datetime import date

import pandas as pd

_REQUIRED_COLUMNS = {"name", "duration_minutes", "due_date"}


def parse_homework_csv(file_path: str) -> list:
    try:
        df = pd.read_csv(file_path)
    except Exception as exc:
        raise ValueError(f"Cannot read CSV file: {exc}") from exc

    df.columns = df.columns.str.strip().str.lower()

    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
            "Expected columns: name, duration_minutes, due_date"
        )

    if df.empty:
        raise ValueError("CSV file contains no task rows.")

    tasks  = []
    errors = []

    for idx, row in df.iterrows():
        row_label = f"Row {idx + 2}"
        try:
            name = str(row["name"]).strip()
            if not name or name.lower() == "nan":
                raise ValueError("task name is empty")

            duration = int(row["duration_minutes"])
            if duration <= 0:
                raise ValueError(f"duration_minutes must be > 0, got {duration}")

            due = pd.to_datetime(row["due_date"]).date()

            tasks.append({
                "name":               name,
                "duration_minutes":   duration,
                "due_date":           due,
                "remaining_minutes":  duration,
            })
        except ValueError as exc:
            errors.append(f"{row_label}: {exc}")

    if errors:
        raise ValueError("CSV validation errors:\n" + "\n".join(errors))

    tasks.sort(key=lambda t: t["due_date"])
    return tasks