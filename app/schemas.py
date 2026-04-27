from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.models import RoleEnum

class RefreshRequest(BaseModel):
    refresh_token: str;

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.user_default
    is_active: bool

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: str
    email: str
    role: str
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    content: str
    msg_type: Optional[str] = "text"

class MessageCreate(MessageBase):
    recipient_id: int

class MessageResponse(MessageBase):
    id: int
    sender_id: int
    recipient_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class CallHistoryCreate(BaseModel):
    callee_id: int
    duration: Optional[str] = None
    

class CallHistoryResponse(BaseModel):
    id: int
    caller_id: int
    callee_id: int
    start_time: datetime
    duration: Optional[str]
    caller_name: str
    callee_name: str

    class Config:
        from_attributes = True

class RecentChatSummary(BaseModel):
    id: int
    name: str
    last_message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class MuralBase(BaseModel):
    content: str

class MuralCreate(MuralBase):
    pass

class MuralResponse(MuralBase):
    id: int
    updated_by_id: int
    updater: UserResponse
    timestamp: datetime

    class Config:
        from_attributes = True