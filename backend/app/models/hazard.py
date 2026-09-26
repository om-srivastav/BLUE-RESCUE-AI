from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mission import Mission, utc_now


class Hazard(Base):
    __tablename__ = "hazards"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), index=True)
    row: Mapped[int]
    col: Mapped[int]
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    hazard_type: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(120))
    severity: Mapped[str] = mapped_column(String(12))
    severity_factor: Mapped[float]
    confidence: Mapped[float]
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_cells: Mapped[float]
    source_type: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(12), default="ACTIVE")
    notes: Mapped[str] = mapped_column(Text, default="")
    client_request_id: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)
    last_action: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    mission: Mapped[Mission] = relationship(back_populates="hazards")
