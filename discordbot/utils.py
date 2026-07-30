from datetime import datetime, timezone
def log(msg: str):
    now = datetime.now(timezone.utc).strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")