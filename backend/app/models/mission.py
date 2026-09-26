from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    mode: Mapped[str] = mapped_column(String(20), default="DEMO")
    status: Mapped[str] = mapped_column(String(20), default="PLANNING")
    source_type: Mapped[str] = mapped_column(String(40), default="UPLOADED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    aois: Mapped[list["MissionAOI"]] = relationship(back_populates="mission", cascade="all, delete-orphan")
    route_calculations: Mapped[list["RouteCalculation"]] = relationship(back_populates="mission", cascade="all, delete-orphan")
    hazards: Mapped[list["Hazard"]] = relationship(back_populates="mission", cascade="all, delete-orphan")


class MissionAOI(Base):
    __tablename__ = "mission_aois"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    min_latitude: Mapped[float]
    max_latitude: Mapped[float]
    min_longitude: Mapped[float]
    max_longitude: Mapped[float]
    crs: Mapped[str] = mapped_column(String(16), default="EPSG:4326")
    mission: Mapped[Mission] = relationship(back_populates="aois")
