from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import require_admin
from app.crud import users
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix='/api/users')

@router.get("", response_model=List[UserResponse])
async def list_users(admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await users.lists_users(db)

@router.post("", response_model=UserResponse)
async def create_user(
  user_data: UserCreate, 
  admin: User = Depends(require_admin), 
  db: AsyncSession = Depends(get_db)
):
    return await users.create_user(db, user_data)
    
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await users.update_user(db, user_id, user_data)

@router.delete("/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    return await users.delete_user(db, user_id, admin)