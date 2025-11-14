"""Event logging service"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_log import EventLog


class EventService:
    """Service for logging events to audit trail"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        session_id: Optional[UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None
    ) -> EventLog:
        """Log an event to the audit trail"""
        event = EventLog(
            session_id=session_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            event_data=event_data,
            actor_id=actor_id
        )

        self.db.add(event)
        await self.db.flush()

        return event

    async def log_session_event(
        self,
        session_id: UUID,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> EventLog:
        """Log a session-related event"""
        return await self.log_event(
            event_type=event_type,
            event_data=event_data,
            session_id=session_id,
            entity_type="session",
            entity_id=session_id
        )

    async def log_approval_event(
        self,
        session_id: UUID,
        approval_id: UUID,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> EventLog:
        """Log an approval-related event"""
        return await self.log_event(
            event_type=event_type,
            event_data=event_data,
            session_id=session_id,
            entity_type="approval",
            entity_id=approval_id
        )

    async def log_goal_event(
        self,
        session_id: UUID,
        goal_id: UUID,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> EventLog:
        """Log a goal-related event"""
        return await self.log_event(
            event_type=event_type,
            event_data=event_data,
            session_id=session_id,
            entity_type="goal",
            entity_id=goal_id
        )
