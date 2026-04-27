from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models import Mural
from app.core.database import AsyncSessionLocal

async def save_mural(content, updated_by_id):
    async with AsyncSessionLocal() as session:
        new_mural = Mural(content=content, updated_by_id=updated_by_id)
        session.add(new_mural)
        await session.commit()

async def get_latest_mural():
    async with AsyncSessionLocal() as session:
        stmt = select(Mural).options(selectinload(Mural.updater)).order_by(desc(Mural.id)).limit(1)
        result = await session.execute(stmt)
        mural = result.scalar_one_or_none()
        
        if mural:
            return {
                "id": mural.id,
                "content": mural.content,
                "updated_by_id": mural.updated_by_id,
                "updater": {
                    'id': mural.updater.id,
                    'name': mural.updater.name,
                    'email': mural.updater.email,
                    'is_active': mural.updater.is_active
                }, 
                "timestamp": str(mural.timestamp)
            }
        return None