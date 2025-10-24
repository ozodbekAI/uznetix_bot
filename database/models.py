# database/models.py
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Column, String, DateTime, Boolean, Text, Integer, JSON, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    is_getcourse_client: Mapped[bool] = mapped_column(Boolean, default=False)
    getcourse_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    getcourse_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    preferred_script: Mapped[str] = mapped_column(String(10), default="latin")  # latin or cyrillic
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    total_interviews: Mapped[int] = mapped_column(Integer, default=0)
    completed_interviews: Mapped[int] = mapped_column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


    def __repr__(self) -> str:
        return f"<InterviewSession(id={self.id}, telegram_id={self.telegram_id}, status={self.status})>"


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    
    recommendation_type: Mapped[str] = mapped_column(String(50)) 
    content: Mapped[str] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    
    stocks: Mapped[list] = mapped_column(JSON, default=list)
    etfs: Mapped[list] = mapped_column(JSON, default=list)
    bonds: Mapped[list] = mapped_column(JSON, default=list)
    other: Mapped[list] = mapped_column(JSON, default=list)
    
    ai_model_used: Mapped[str] = mapped_column(String(100))
    generation_time: Mapped[float] = mapped_column(Float)
    
    user_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<Recommendation(id={self.id}, type={self.recommendation_type})>"


class BotLog(Base):
    __tablename__ = "bot_logs"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    

    log_type: Mapped[str] = mapped_column(String(50), index=True)  # error, info, warning, debug
    event: Mapped[str] = mapped_column(String(255))
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<BotLog(id={self.id}, type={self.log_type}, event={self.event})>"
    



class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    
    status: Mapped[str] = mapped_column(String(50), default="active")  
    
    conversation_history: Mapped[list] = mapped_column(JSON, default=list)
    
    collected_data: Mapped[dict] = mapped_column(JSON, default=dict)
    # Structure: {
    #   "goal": "...",
    #   "horizon": "...",
    #   "budget": "...",
    #   "risk_tolerance": "...",
    #   "liquidity": "...",
    #   "currency": "...",
    #   "experience": "...",
    #   "restrictions": "...",
    #   "halal_filter": false
    # }
    
    preferred_script: Mapped[str] = mapped_column(String(10), default="latin")
    questions_asked: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<InterviewSession(id={self.id}, telegram_id={self.telegram_id}, status={self.status})>"