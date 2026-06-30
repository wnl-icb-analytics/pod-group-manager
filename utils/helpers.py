# =============================================================================
# POD Group Manager - Helpers
# =============================================================================

import pandas as pd


def format_time_ago(timestamp):
    """Friendly 'time ago' string for a timestamp."""
    if pd.isnull(timestamp):
        return "Unknown"
    try:
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        diff = pd.Timestamp.now() - timestamp
        days, secs = diff.days, diff.seconds
        if days >= 365:
            n = days // 365
            return f"{n} year{'s' if n != 1 else ''} ago"
        if days >= 30:
            n = days // 30
            return f"{n} month{'s' if n != 1 else ''} ago"
        if days >= 7:
            n = days // 7
            return f"{n} week{'s' if n != 1 else ''} ago"
        if days > 0:
            return f"{days} day{'s' if days != 1 else ''} ago"
        if secs >= 3600:
            n = secs // 3600
            return f"{n} hour{'s' if n != 1 else ''} ago"
        if secs >= 60:
            n = secs // 60
            return f"{n} minute{'s' if n != 1 else ''} ago"
        return "Just now"
    except Exception:
        return "Unknown"


def format_number(num):
    if pd.isnull(num) or num == "":
        return "0"
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)


def display_component(value):
    """Render a component field, showing '∅' for missing (NULL) values."""
    if value is None or (isinstance(value, float) and pd.isnull(value)):
        return "∅"
    if value == "?":
        return "∅"
    return str(value)
