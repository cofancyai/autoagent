"""Message management service"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.schemas.message import MessageCreate


class MessageService:
    """Service for managing messages"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(self, session_id: UUID, message_data: MessageCreate) -> Message:
        """Create a new message"""
        message = Message(
            session_id=session_id,
            role=message_data.role,
            content=message_data.content,
            metadata=message_data.metadata,
        )

        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        return message

    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get a message by ID"""
        result = await self.db.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def list_messages(
        self, session_id: UUID, limit: int = 50, before_id: Optional[UUID] = None
    ) -> tuple[List[Message], bool]:
        """
        List messages for a session

        Returns:
            Tuple of (messages list, has_more flag)
        """
        query = select(Message).where(Message.session_id == session_id)

        # Apply cursor pagination if before_id provided
        if before_id:
            before_message = await self.get_message(before_id)
            if before_message:
                query = query.where(Message.created_at < before_message.created_at)

        # Fetch one extra to check if there are more
        query = query.order_by(Message.created_at.desc()).limit(limit + 1)

        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        return messages, has_more

    async def get_conversation_history(self, session_id: UUID, limit: int = 20) -> List[Message]:
        """Get recent conversation history"""
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # Return in chronological order
        return list(reversed(messages))
