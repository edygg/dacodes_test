from datetime import datetime, UTC


get_utc_timestamp = lambda: datetime.now(tz=UTC)