from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from geoalchemy2 import Geography
from db.base import Base


class Zone(Base):
    """Administrative zone boundary (polygon)."""
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=True, unique=True, index=True)
    boundary = Column(Geography(geometry_type="POLYGON", srid=4326), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Zone {self.id} - {self.name}>"
