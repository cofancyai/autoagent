"""Session management service"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate


class SessionService:
    """Service for managing sessions"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        session_data: SessionCreate
    ) -> Session:
        """Create a new session"""
        session = Session(
            user_id=session_data.user_id,
            title=session_data.title or "New Session",
            context=session_data.context or {},
            status="active"
        )

        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def get_session(self, session_id: UUID) -> Optional[Session]:
        """Get a session by ID"""
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[Session], int]:
        """
        List sessions with pagination

        Returns:
            Tuple of (sessions list, total count)
        """
        query = select(Session)

        # Apply filters
        if user_id:
            query = query.where(Session.user_id == user_id)
        if status:
            query = query.where(Session.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        query = query.order_by(Session.created_at.desc())

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return list(sessions), total

    async def update_session(
        self,
        session_id: UUID,
        session_data: SessionUpdate
    ) -> Optional[Session]:
        """Update a session"""
        session = await self.get_session(session_id)
        if not session:
            return None

        # Update fields
        update_data = session_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session"""
        session = await self.get_session(session_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.flush()

        return True

    async def update_context(
        self,
        session_id: UUID,
        context_updates: Dict[str, Any]
    ) -> Optional[Session]:
        """Update session context"""
        session = await self.get_session(session_id)
        if not session:
            return None

        # Merge context
        current_context = session.context or {}
        current_context.update(context_updates)
        session.context = current_context

        await self.db.flush()
        await self.db.refresh(session)

        return session
