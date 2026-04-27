from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.security import get_password_hash
from app.schemas import UserCreate, UserUpdate

async def lists_users(db: AsyncSession):
    result = await db.execute(select(User).order_by(User.name))
    return result.scalars().all()

async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    existing = await db.scalar(select(User).where(User.email == user_data.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(name=user_data.name, email=user_data.email, hashed_password=hashed_pw, role=user_data.role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> User:
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    email_already = await db.scalar(select(User).where(User.email == user_data.email))
    if email_already and user.email != user_data.email:
        raise HTTPException(status_code=409, detail="Email já cadastrado")

    
    user.name = user_data.name
    user.email = user_data.email
    user.role = user_data.role
    user.is_active = user_data.is_active
    
    if user_data.password: # Só atualiza a senha se o admin digitou uma nova
        user.hashed_password = get_password_hash(user_data.password)
        
    await db.commit()
    await db.refresh(user)
    return user
    
async def delete_user(db: AsyncSession, user_id: int, admin: User):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Você não pode excluir a si mesmo.")
        
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    user.is_active = False
    
    await db.commit()
    return {"status": "success"}