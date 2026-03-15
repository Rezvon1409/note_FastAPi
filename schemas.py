from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List



class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    role: str = "user"   

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    token: str
    user_id: int
    token_expiry: datetime

    class Config:
        from_attributes = True



class NoteRequest(BaseModel):
    title: str
    description: str

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class NoteOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NotesList(BaseModel):
    notes: List[NoteOut]
