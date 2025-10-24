# database/repositories.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, InterviewSession, Recommendation, BotLog
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    
    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> User:
        user = User(**kwargs)
        session.add(user)
        await session.flush()
        return user
    
    @staticmethod
    async def update(session: AsyncSession, telegram_id: int, **kwargs) -> Optional[User]:
        await session.execute(
            update(User).where(User.telegram_id == telegram_id).values(**kwargs)
        )
        return await UserRepository.get_by_telegram_id(session, telegram_id)
    
    @staticmethod
    async def update_activity(session: AsyncSession, telegram_id: int):
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(last_activity=func.now())
        )
    
    @staticmethod
    async def get_all_users(session: AsyncSession, limit: int = 1000, offset: int = 0) -> List[User]:
        result = await session.execute(
            select(User).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def count_users(session: AsyncSession) -> int:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()



class InterviewSessionRepository:
    
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> InterviewSession:
        """Create new interview session"""
        interview = InterviewSession(**kwargs)
        session.add(interview)
        await session.flush()
        return interview
    
    @staticmethod
    async def get_active_session(session: AsyncSession, telegram_id: int) -> Optional[InterviewSession]:
        """Get active interview session for user"""
        result = await session.execute(
            select(InterviewSession)
            .where(InterviewSession.telegram_id == telegram_id)
            .where(InterviewSession.status == "active")
            .order_by(desc(InterviewSession.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_session(session: AsyncSession, session_id: int, **kwargs):
        """Update interview session"""
        await session.execute(
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(**kwargs)
        )
    
    @staticmethod
    async def add_message(session: AsyncSession, session_id: int, role: str, content: str):
        """Add message to conversation history"""
        result = await session.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        interview = result.scalar_one_or_none()
        if interview:
            history = interview.conversation_history or []
            history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            await session.execute(
                update(InterviewSession)
                .where(InterviewSession.id == session_id)
                .values(conversation_history=history)
            )
    
    @staticmethod
    async def update_collected_data(session: AsyncSession, session_id: int, data_updates: dict):
        """Update collected data"""
        result = await session.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        interview = result.scalar_one_or_none()
        if interview:
            collected = interview.collected_data or {}
            collected.update(data_updates)
            await session.execute(
                update(InterviewSession)
                .where(InterviewSession.id == session_id)
                .values(collected_data=collected)
            )
    
    @staticmethod
    async def get_by_id(session: AsyncSession, session_id: int) -> Optional[InterviewSession]:
        """Get session by ID"""
        result = await session.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_sessions(session: AsyncSession, telegram_id: int, limit: int = 10) -> List[InterviewSession]:
        """Get user's interview sessions"""
        result = await session.execute(
            select(InterviewSession)
            .where(InterviewSession.telegram_id == telegram_id)
            .order_by(desc(InterviewSession.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod  # Yangi metod qo'shildi
    async def count_completed_sessions(session: AsyncSession) -> int:
        """Count completed interview sessions"""
        result = await session.execute(
            select(func.count(InterviewSession.id)).where(InterviewSession.status == "completed")
        )
        return result.scalar_one()

# database/repositories.py (добавить)

class RecommendationRepository:
    """Repository for Recommendation operations"""
    
    @staticmethod
    async def create(session: AsyncSession, **kwargs) -> Recommendation:
        """Create new recommendation"""
        recommendation = Recommendation(**kwargs)
        session.add(recommendation)
        await session.flush()
        return recommendation
    
    @staticmethod
    async def get_by_session_id(session: AsyncSession, session_id: int) -> Optional[Recommendation]:
        """Get recommendation by session ID"""
        result = await session.execute(
            select(Recommendation).where(Recommendation.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_recommendations(
        session: AsyncSession, 
        telegram_id: int, 
        limit: int = 10
    ) -> List[Recommendation]:
        """Get user's recommendations"""
        result = await session.execute(
            select(Recommendation)
            .where(Recommendation.telegram_id == telegram_id)
            .order_by(desc(Recommendation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())