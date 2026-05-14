from datetime import datetime, date


def parse_time(t: str) -> datetime | None:
    if not t:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    try:
        time_obj = datetime.strptime(t, "%H:%M").time()
        return datetime.combine(date.today(), time_obj)
    except ValueError:
        return None
