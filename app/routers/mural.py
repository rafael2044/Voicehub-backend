from fastapi import APIRouter, Depends
from typing import Optional

from app.models import User
from app.core.security import get_current_user
from app.crud.mural import save_mural, get_latest_mural
from app.schemas import MuralResponse, MuralCreate
from app.core.ws_manager import manager

router = APIRouter(prefix='/api/mural')

@router.get("", response_model=Optional[MuralResponse])
async def get_mural_api(
    current_user: User = Depends(get_current_user)
):
    """Retorna o aviso mais recente do mural."""
    mural = await get_latest_mural()
    return mural

@router.post("")
async def update_mural_api(
    mural_data: MuralCreate,
    current_user: User = Depends(get_current_user)
):
    """Atualiza o mural."""
  
    await save_mural(mural_data.content, current_user.id)
    updated_mural = await get_latest_mural()
    
    await manager.broadcast_mural(updated_mural)
    return {"status": "success"}