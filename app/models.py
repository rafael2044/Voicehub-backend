from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class RoleEnum(str, enum.Enum):
    user_default = "user_default"
    user_admin = "user_admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.user_default)
    is_active = Column(Boolean, default=True)

    # Relacionamentos bidirecionais (facilita consultas no SQLAlchemy)
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    calls_made = relationship("CallHistory", foreign_keys="CallHistory.caller_id", back_populates="caller")
    calls_received = relationship("CallHistory", foreign_keys="CallHistory.callee_id", back_populates="callee")
    mural_updates = relationship("Mural", back_populates="updater")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    msg_type = Column(String, default="text")
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="messages_received")

class CallHistory(Base):
    __tablename__ = "call_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    callee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(String, nullable=True)
    status = Column(String)

    caller = relationship("User", foreign_keys=[caller_id], back_populates="calls_made")
    callee = relationship("User", foreign_keys=[callee_id], back_populates="calls_received")

class Mural(Base):
    __tablename__ = "mural"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(String, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    updater = relationship("User", foreign_keys=[updated_by_id], back_populates="mural_updates")