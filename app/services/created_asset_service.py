"""CreatedAsset service for managing created business assets"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CreatedAsset
from app.schemas.created_asset import CreatedAssetCreate, CreatedAssetUpdate


class CreatedAssetService:
    """Service for managing created assets"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_asset(
        self,
        project_id: UUID,
        session_id: UUID,
        asset_data: CreatedAssetCreate,
        task_id: Optional[UUID] = None,
    ) -> CreatedAsset:
        """Create a new asset"""
        asset = CreatedAsset(
            id=uuid4(),
            project_id=project_id,
            task_id=task_id,
            session_id=session_id,
            asset_name=asset_data.asset_name,
            asset_type=asset_data.asset_type,
            description=asset_data.description,
            url=asset_data.url,
            file_path=asset_data.file_path,
            credentials=asset_data.credentials,
            asset_metadata=asset_data.asset_metadata,
            deployment_status="created",
            external_id=asset_data.external_id,
            external_service=asset_data.external_service,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(asset)
        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def get_asset(self, asset_id: UUID) -> Optional[CreatedAsset]:
        """Get asset by ID"""
        result = await self.db.execute(select(CreatedAsset).where(CreatedAsset.id == asset_id))
        return result.scalars().first()

    async def list_assets(
        self,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        asset_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[CreatedAsset]:
        """List assets with optional filters"""
        query = select(CreatedAsset).order_by(CreatedAsset.created_at.desc())

        if project_id:
            query = query.where(CreatedAsset.project_id == project_id)
        if task_id:
            query = query.where(CreatedAsset.task_id == task_id)
        if session_id:
            query = query.where(CreatedAsset.session_id == session_id)
        if asset_type:
            query = query.where(CreatedAsset.asset_type == asset_type)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_asset(
        self, asset_id: UUID, asset_data: CreatedAssetUpdate
    ) -> Optional[CreatedAsset]:
        """Update asset"""
        asset = await self.get_asset(asset_id)
        if not asset:
            return None

        # Update fields if provided
        update_dict = asset_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(asset, field, value)

        asset.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def update_deployment_status(
        self, asset_id: UUID, status: str
    ) -> Optional[CreatedAsset]:
        """Update asset deployment status"""
        asset = await self.get_asset(asset_id)
        if not asset:
            return None

        asset.deployment_status = status
        asset.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(asset)
        return asset

    async def delete_asset(self, asset_id: UUID) -> bool:
        """Delete asset"""
        asset = await self.get_asset(asset_id)
        if not asset:
            return False

        await self.db.delete(asset)
        await self.db.flush()
        return True
