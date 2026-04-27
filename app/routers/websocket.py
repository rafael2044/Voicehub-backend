import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.core.ws_manager import manager
from app.core.database import get_db
from app.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from app.core.settings import settings
from app.crud.message import save_message
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            await websocket.close(code=1008)
            return
            
        user = await db.scalar(select(User).filter(User.email == email))
        
        if user is None:
            await websocket.close(code=1008)
            return
            
        user_id_str = str(user.id) 
        await manager.connect(websocket, user_id_str, user.name)
        
        try:
            while True:
                data = await websocket.receive_text()
                
                # 1. Proteção contra JSON malformado
                try:
                    msg = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"JSON inválido recebido de {user_id_str}")
                    continue # Ignora a mensagem ruim e mantém o websocket aberto
                
                msg_type = msg.get("type")
            
                # 2. Heartbeat para manter intermediários (Proxies/Tunnels) abertos
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue

                # 3. Proteção genérica para não quebrar o loop em caso de erro na lógica de negócio
                try:
                    if msg_type == "private_chat":
                        target_str = str(msg["target"])
                        content = msg["content"]
                        chat_msg_type = msg.get("msg_type", "text")
                        
                        await save_message(user.id, int(target_str), content, chat_msg_type) 
                        await manager.send_private({"type": "private_chat", "sender": user_id_str, "content": content, "msg_type": chat_msg_type}, target_str)
                        await manager.send_private({"type": "private_chat_sent", "recipient": target_str, "content": content, "msg_type": chat_msg_type}, user_id_str)
                    
                    elif msg_type == "verify_status":
                        target_str = str(msg["target"])
                        status = manager.user_status.get(target_str)
                        if status == "busy":
                            await manager.send_private({"type": "call_rejected", "reason": "busy", "target": target_str}, user_id_str)
                            await manager.inject_system_message(user_id_str, target_str, "⚠️ Ocupado: Chamada Recusada")
                        elif status is None:
                            await manager.send_private({"type": "call_rejected", "reason": "offline", "target": target_str}, user_id_str)
                            await save_message(user.id, int(target_str), "📞 Tentei te ligar (Offline)", "system") 
                        else:
                            await manager.send_private({"type": "status_ok_proceed", "target": target_str}, user_id_str)

                    elif msg_type == "call_request":
                        target_str = str(msg["target"])
                        manager.set_status(user_id_str, "busy")
                        manager.set_status(target_str, "busy")
                        manager.start_call_tracking(user_id_str, target_str)
                        await manager.broadcast_user_list()
                        await manager.send_private({"type": "incoming_call", "caller": user_id_str}, target_str)

                    elif msg_type == "answer":
                        manager.mark_call_accepted(user_id_str)
                        target_str = str(msg["target"])
                        msg["sender"] = user_id_str
                        await manager.send_private(msg, target_str)

                    elif msg_type in ["offer", "candidate"]:
                        target_str = str(msg["target"])
                        msg["sender"] = user_id_str
                        await manager.send_private(msg, target_str)

                    elif msg_type == "end_call":
                        target_raw = msg.get("target")
                        target_str = str(target_raw) if target_raw else None
                        reason = msg.get("reason", "manual") 
                        
                        was_accepted = await manager.stop_call_tracking(user_id_str)
                        
                        if not was_accepted and target_str:
                            message_text = "📞 Chamada Perdida / Recusada"
                            if reason == "timeout":
                                message_text = "📞 Sem resposta (Ligação caiu)"
                            await manager.inject_system_message(user_id_str, target_str, message_text)

                        manager.set_status(user_id_str, "online")
                        
                        await manager.send_private({"type": "call_ended"}, user_id_str)

                        if target_str and target_str in manager.user_status:
                            manager.set_status(target_str, "online")
                            await manager.send_private({"type": "call_ended"}, target_str)
                        
                        await manager.broadcast_user_list()

                except Exception as inner_e:
                    # Loga o erro específico da regra de negócio, mas não derruba a conexão do usuário
                    logger.error(f"Erro ao processar mensagem {msg_type} do usuário {user_id_str}: {inner_e}")

        except WebSocketDisconnect:
            manager.disconnect(user_id_str)
            await manager.broadcast_user_list()
            
    except JWTError:
        await websocket.close(code=1008)