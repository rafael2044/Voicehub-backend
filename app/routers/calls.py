from fastapi import APIRouter, Depends
from typing import List

from app.core.security import get_current_user
from app.models import User
from app.schemas import CallHistoryResponse
from app.crud.calls import get_calls_history


router = APIRouter(prefix='/api/calls')

@router.get("/{user_id}", response_model=List[CallHistoryResponse])
async def get_calls_api(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """Busca o histórico de chamadas de um usuário."""
    calls = await get_calls_history(user_id)
    return calls