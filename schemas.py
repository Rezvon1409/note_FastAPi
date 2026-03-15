from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    username : str
    email : EmailStr
    password : str
    confirm_password : str

class UserOut(BaseModel):
    id : int 
    username : str
    email : str
    is_admin: bool
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class NoteCreate(BaseModel):
    title : str
    content : str

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class NoteOut(BaseModel):
    id: int
    owner_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True