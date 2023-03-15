from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""
    pass


class OccupationVisa(Base):
    """Database model for scraped occupation-visa mappings."""
    __tablename__ = "occupation_visas"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation: Mapped[str] = mapped_column(String, nullable=False, index=True)
    visa_subclass: Mapped[str] = mapped_column(String, nullable=False, index=True)
    stream: Mapped[str] = mapped_column(String, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict[str, str]:
        """Convert model attributes to dictionary."""
        return {
            "occupation": self.occupation,
            "visa_subclass": self.visa_subclass,
            "stream": self.stream,
            "scraped_at": self.scraped_at.isoformat()
        }
