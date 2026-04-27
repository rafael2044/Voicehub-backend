from datetime import datetime
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models import CallHistory

async def save_call_record(caller_id: int, callee_id: int, start_time: datetime, end_time: datetime, duration: str, status: str):
    async with AsyncSessionLocal() as session:
        new_call = CallHistory(
            caller_id=caller_id, callee_id=callee_id, 
            start_time=start_time, end_time=end_time,
            duration=duration, status=status
        )
        session.add(new_call)
        await session.commit()

async def get_calls_history(user_id: int):
    async with AsyncSessionLocal() as session:
        # MUDANÇA: Buscando pelas colunas _id
        stmt = select(CallHistory).where(
            or_(CallHistory.caller_id == user_id, CallHistory.callee_id == user_id)
        ).options(selectinload(CallHistory.caller), selectinload(CallHistory.callee)).order_by(desc(CallHistory.id)).limit(50)
        
        result = await session.execute(stmt)
        calls = result.scalars().all()
        return [{
            "id": call.id,
            "caller_id": call.caller_id,
            "callee_id": call.callee_id,
            "start_time": call.start_time,
            "end_time": call.end_time,
            "duration": call.duration,
            "status": call.status,
            "caller_name": call.caller.name,
            "callee_name": call.callee.name
        } for call in calls]

