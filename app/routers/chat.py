from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas import RecentChatSummary
from app.crud import chats

router = APIRouter(prefix='/api/chats')

@router.get("/recent", response_model=List[RecentChatSummary])
async def get_recent_chats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await chats.get_recent_chats(db, current_user)

