from pydantic import BaseModel


class PostgresPersistenceConfig(BaseModel):
    dsn: str | None = None
    db_schema: str = "experiment"
    connect_timeout_seconds: int = 5
