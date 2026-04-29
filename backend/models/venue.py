# models/venue.py (Simplified version)
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, relationship
from database import Base

class Venue(Base):
    __tablename__ = "venues"
    
    VenueID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    VenueName = Column(String(255), unique=True, nullable=False)
    Campus = Column(String(100), nullable=False)
    Location = Column(String(255), nullable=False)
    Capacity = Column(Integer, default=100)
    IsActive = Column(Boolean, default=True)
    
    # Performance metrics for dashboard
    Stars = Column(Float, default=5.0)
    QueueSpeed = Column(Integer, default=15)  # Seconds per student
    
    # Timestamps
    CreatedAt = Column(DateTime, server_default=func.now())
    UpdatedAt = Column(DateTime, onupdate=func.now())
    
    # Relationships
    # exam_sessions : Mapped["ExamSession"] = relationship("ExamSession", back_populates="venue")
    
    def __repr__(self):
        return f"<Venue {self.VenueName}>"