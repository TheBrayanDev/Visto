from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class ScanHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    english_label: str
    translated_label: str
    target_language: str
    confidence: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
