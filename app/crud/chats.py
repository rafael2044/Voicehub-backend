from typing import List, Dict, Any
from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, User


async def get_recent_chats(db: AsyncSession, current_user: User) -> List[Dict[str, Any]]:
    """Retorna uma lista de usuários com quem o current_user já conversou."""
    
    stmt = select(Message).where(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    ).order_by(desc(Message.timestamp))
    
    result = await db.execute(stmt)
    messages = result.scalars().all()

    recent_partners = {}
    
    for msg in messages:
        # Descobre quem é a "outra pessoa" na conversa
        partner_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        
        if partner_id not in recent_partners:
            # Busca o nome desse usuário no banco
            partner_user = await db.scalar(select(User).where(User.id == partner_id))
            if partner_user:
                recent_partners[partner_id] = {
                    "id": partner_id,
                    "name": partner_user.name,
                    "last_message": msg.content if msg.msg_type == "text" else f"📎 {msg.msg_type.capitalize()}",
                    "timestamp": str(msg.timestamp)
                }
                
    return list(recent_partners.values())