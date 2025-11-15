"""CreatedAsset API endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.created_asset import (
    CreatedAssetCreate,
    CreatedAssetListResponse,
    CreatedAssetResponse,
    CreatedAssetUpdate,
)
from app.schemas.response import APIResponse
from app.services.created_asset_service import CreatedAssetService
from app.services.event_service import EventService
from app.services.execution_project_service import ExecutionProjectService

router = APIRouter(prefix="/assets", tags=["created_assets"])


@router.post("", response_model=APIResponse[CreatedAssetResponse], status_code=201)
async def create_asset(
    project_id: UUID,
    asset_data: CreatedAssetCreate,
    task_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Create a new asset"""
    project_service = ExecutionProjectService(db)
    asset_service = CreatedAssetService(db)
    event_service = EventService(db)

    # Verify project exists
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create asset
    asset = await asset_service.create_asset(project_id, project.session_id, asset_data, task_id)

    # Log event
    await event_service.log_event(
        event_type="execution.asset_created",
        event_data={
            "asset_name": asset.asset_name,
            "asset_type": asset.asset_type,
            "url": asset.url,
        },
        session_id=project.session_id,
        entity_type="created_asset",
        entity_id=asset.id,
    )

    await db.commit()

    return APIResponse(data=CreatedAssetResponse.model_validate(asset))


@router.get("", response_model=APIResponse[CreatedAssetListResponse])
async def list_assets(
    project_id: Optional[UUID] = Query(None),
    task_id: Optional[UUID] = Query(None),
    session_id: Optional[UUID] = Query(None),
    asset_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List created assets"""
    asset_service = CreatedAssetService(db)

    assets = await asset_service.list_assets(
        project_id=project_id,
        task_id=task_id,
        session_id=session_id,
        asset_type=asset_type,
        limit=limit,
    )

    return APIResponse(
        data=CreatedAssetListResponse(
            assets=[CreatedAssetResponse.model_validate(a) for a in assets], total=len(assets)
        )
    )


@router.get("/{asset_id}", response_model=APIResponse[CreatedAssetResponse])
async def get_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get asset details"""
    asset_service = CreatedAssetService(db)

    asset = await asset_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return APIResponse(data=CreatedAssetResponse.model_validate(asset))


@router.patch("/{asset_id}", response_model=APIResponse[CreatedAssetResponse])
async def update_asset(
    asset_id: UUID, asset_data: CreatedAssetUpdate, db: AsyncSession = Depends(get_db)
):
    """Update asset"""
    asset_service = CreatedAssetService(db)
    event_service = EventService(db)

    asset = await asset_service.update_asset(asset_id, asset_data)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Log event
    await event_service.log_event(
        event_type="execution.asset_updated",
        event_data=asset_data.model_dump(exclude_unset=True),
        session_id=asset.session_id,
        entity_type="created_asset",
        entity_id=asset.id,
    )

    await db.commit()

    return APIResponse(data=CreatedAssetResponse.model_validate(asset))


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(asset_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete asset"""
    asset_service = CreatedAssetService(db)
    event_service = EventService(db)

    asset = await asset_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Log event before deletion
    await event_service.log_event(
        event_type="execution.asset_deleted",
        event_data={"asset_id": str(asset_id), "asset_name": asset.asset_name},
        session_id=asset.session_id,
    )

    deleted = await asset_service.delete_asset(asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")

    await db.commit()
