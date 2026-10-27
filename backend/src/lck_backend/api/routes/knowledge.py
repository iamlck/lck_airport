from fastapi import APIRouter, Depends
from lck_backend.schemas.knowledge import SnapshotStatusResponse, RefreshResponse
from lck_backend.knowledge.snapshot import snapshot_manager
from lck_backend.api.dependencies import verify_admin_token

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/status", response_model=SnapshotStatusResponse)
async def get_knowledge_status():
    snapshot = snapshot_manager.active_snapshot
    if not snapshot:
        snapshot = snapshot_manager.refresh()
    return snapshot.to_status_response(is_active=True)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_knowledge(authenticated: bool = Depends(verify_admin_token)):
    snapshot = snapshot_manager.refresh()
    return RefreshResponse(
        success=True,
        message=f"Knowledge snapshot {snapshot.version} successfully activated.",
        snapshot=snapshot.to_status_response(is_active=True)
    )

