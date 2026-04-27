import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File
from app.models import User
from app.core.security import get_current_user
from app.crud.message import get_conversation_history
from app.schemas import MessageResponse
from typing import List

router = APIRouter(prefix='/api/messages')

@router.get("/{user_id}/{target_id}", response_model=List[MessageResponse])
async def get_messages_api(
    user_id: int,
    target_id: int,
    current_user: User = Depends(get_current_user)
    ):
    """Busca o histórico de mensagens entre dois usuários."""
    history = await get_conversation_history(user_id, target_id)
    return history

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    """Salva o arquivo localmente e retorna a URL. Fácil de trocar para S3 no futuro."""
    # Gera um nome único para não sobrescrever arquivos com o mesmo nome
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join("uploads", unique_filename)

    # Salva o arquivo no disco
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "url": f"/uploads/{unique_filename}",
        "filename": file.filename
    }
