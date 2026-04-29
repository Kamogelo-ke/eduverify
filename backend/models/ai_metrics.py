# models/ai_metrics.py
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, relationship
from database import Base

class AIMetrics(Base):
    __tablename__ = "ai_metrics"
    
    MetricID = Column(Integer, primary_key=True, index=True)
    SessionID = Column(Integer, ForeignKey("exam_sessions.SessionID"), nullable=False)
    FAR = Column(Float, nullable=False)  # False Acceptance Rate
    FRR = Column(Float, nullable=False)  # False Rejection Rate
    AvgProcessTime = Column(Float, nullable=False)  # seconds
    TotalProcessed = Column(Integer, default=0)
    Timestamp = Column(DateTime, default=datetime.utcnow)

    # exam_session : Mapped["ExamSessio"] = relationship("ExamSession", back_populates="ai_metrics")