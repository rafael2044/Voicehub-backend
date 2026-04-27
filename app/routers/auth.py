from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.schemas import RefreshRequest
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_refresh_token

router = APIRouter()

@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == form_data.username)
    user = await db.scalar(stmt)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Sua conta foi desativada. Procure o administrador.")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user_id": user.id, "name": user.name, "role": user.role}

@router.post("/refresh")
async def refresh_token_route(request: RefreshRequest):
    payload = verify_refresh_token(request.refresh_token)
    new_access_token = create_access_token(data={"sub": payload.get('sub')})
    return {"access_token": new_access_token}
    