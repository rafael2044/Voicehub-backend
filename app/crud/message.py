from sqlalchemy import select, or_, and_
from app.core.database import AsyncSessionLocal
from app.models import Message

async def save_message(sender_id, recipient_id, content, msg_type="text"):
    async with AsyncSessionLocal() as session:
        new_msg = Message(sender_id=sender_id, recipient_id=recipient_id, content=content, msg_type=msg_type)
        session.add(new_msg)
        await session.commit()

async def get_conversation_history(user1_id, user2_id):
    async with AsyncSessionLocal() as session:
        stmt = select(Message).where(
            or_(
                and_(Message.sender_id == user1_id, Message.recipient_id == user2_id),
                and_(Message.sender_id == user2_id, Message.recipient_id == user1_id)
            )
        ).order_by(Message.id.asc())
        
        result = await session.execute(stmt)
        messages = result.scalars().all()
        # Converte para dicionário para manter compatibilidade com seu frontend
        return [{
            "id": msg.id,
            "sender_id": msg.sender_id, 
            "recipient_id": msg.recipient_id, 
            "content": msg.content, 
            "msg_type": msg.msg_type, 
            "timestamp": str(msg.timestamp)
        } for msg in messages]