def duration_seconds_of(item: dict) -> int:
    raw = item.get("duration_seconds")
    if isinstance(raw, (int, float)) and int(raw) > 0:
        return int(raw)
    parts = str(item.get("duration_string") or "").split(":")
    if len(parts) < 2 or not all(part.isdigit() for part in parts):
        return 0
    total = 0
    for part in parts:
        total = total * 60 + int(part)
    return total
