from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

class base(DeclarativeBase):
    pass

class Report(base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(String(36), primary_key=True)
    file_hash: Mapped[str] = mapped_column(String(64), index=True, unique=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    signals_json: Mapped[str] = mapped_column(String(255), nullable=False)
    ocr_text: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[str] = mapped_column(String(255), nullable=True)
    technical_metrics_json: Mapped[str] = mapped_column(String(255), nullable=True)
    
