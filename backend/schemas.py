from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- User схемы ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_online: bool = False
    last_seen: Optional[datetime] = None
    avatar_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# --- Group схемы ---
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    member_ids: List[int] = []


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    creator_id: int
    created_at: datetime
    members: List[UserResponse] = []

    class Config:
        from_attributes = True


class GroupAddMembers(BaseModel):
    user_ids: List[int]


# --- Message схемы ---
class MessageCreate(BaseModel):
    content: Optional[str] = None
    sender_id: int
    receiver_id: Optional[int] = None
    group_id: Optional[int] = None
    reply_to_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    content: Optional[str] = None
    sender_id: int
    receiver_id: Optional[int] = None
    group_id: Optional[int] = None
    is_read: bool
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    reply_to_id: Optional[int] = None
    reply_to: Optional['MessageResponse'] = None

    class Config:
        from_attributes = True
    

class MessageUpdate(BaseModel):
    content: str