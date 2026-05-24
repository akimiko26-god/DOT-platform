from datetime import datetime, timedelta

ONLINE_WINDOW = timedelta(minutes=5)


def touch_last_seen(user) -> None:
    user.last_seen_at = datetime.utcnow()


def is_user_online(user) -> bool:
    if not user or not user.last_seen_at:
        return False
    return datetime.utcnow() - user.last_seen_at <= ONLINE_WINDOW
