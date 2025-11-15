"""ServiceIntegration service for managing third-party service integrations"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ServiceIntegration
from app.schemas.service_integration import (
    ServiceIntegrationCreate,
    ServiceIntegrationUpdate,
)


class ServiceIntegrationService:
    """Service for managing service integrations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_integration(
        self, project_id: UUID, session_id: UUID, integration_data: ServiceIntegrationCreate
    ) -> ServiceIntegration:
        """Create a new service integration"""
        integration = ServiceIntegration(
            id=uuid4(),
            project_id=project_id,
            session_id=session_id,
            service_name=integration_data.service_name,
            service_category=integration_data.service_category,
            status="pending",
            api_key=integration_data.api_key,
            api_credentials=integration_data.api_credentials,
            config=integration_data.config,
            webhooks=integration_data.webhooks,
            retry_count="0",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(integration)
        await self.db.flush()
        await self.db.refresh(integration)
        return integration

    async def get_integration(self, integration_id: UUID) -> Optional[ServiceIntegration]:
        """Get integration by ID"""
        result = await self.db.execute(
            select(ServiceIntegration).where(ServiceIntegration.id == integration_id)
        )
        return result.scalars().first()

    async def get_by_service(
        self, project_id: UUID, service_name: str
    ) -> Optional[ServiceIntegration]:
        """Get integration by project and service name"""
        result = await self.db.execute(
            select(ServiceIntegration)
            .where(ServiceIntegration.project_id == project_id)
            .where(ServiceIntegration.service_name == service_name)
        )
        return result.scalars().first()

    async def list_integrations(
        self,
        project_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        service_category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ServiceIntegration]:
        """List integrations with optional filters"""
        query = select(ServiceIntegration).order_by(ServiceIntegration.created_at.desc())

        if project_id:
            query = query.where(ServiceIntegration.project_id == project_id)
        if session_id:
            query = query.where(ServiceIntegration.session_id == session_id)
        if service_category:
            query = query.where(ServiceIntegration.service_category == service_category)
        if status:
            query = query.where(ServiceIntegration.status == status)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_integration(
        self, integration_id: UUID, integration_data: ServiceIntegrationUpdate
    ) -> Optional[ServiceIntegration]:
        """Update service integration"""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        # Update fields if provided
        update_dict = integration_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(integration, field, value)

        integration.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(integration)
        return integration

    async def update_status(
        self, integration_id: UUID, status: str, error_message: Optional[str] = None
    ) -> Optional[ServiceIntegration]:
        """Update integration status"""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        integration.status = status
        if error_message:
            integration.error_message = error_message

        if status == "active":
            integration.last_used_at = datetime.utcnow()

        integration.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(integration)
        return integration

    async def record_usage(self, integration_id: UUID, usage_data: dict) -> Optional[ServiceIntegration]:
        """Record usage statistics for integration"""
        integration = await self.get_integration(integration_id)
        if not integration:
            return None

        integration.last_used_at = datetime.utcnow()

        # Merge usage stats
        if integration.usage_stats is None:
            integration.usage_stats = {}

        integration.usage_stats.update(usage_data)
        integration.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(integration)
        return integration

    async def delete_integration(self, integration_id: UUID) -> bool:
        """Delete service integration"""
        integration = await self.get_integration(integration_id)
        if not integration:
            return False

        await self.db.delete(integration)
        await self.db.flush()
        return True
