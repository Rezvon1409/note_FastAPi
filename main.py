from fastapi import FastAPI, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
import uuid
import uvicorn
from models import *
from database import get_db
from schemas import *
from auth import verify_password , hash_password

app = FastAPI()

sessions = {}

def get_current_user_id(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in")
    return sessions[session_id]

@app.post("/register", response_model=UserOut)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if user_in.password != user_in.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password wrong")
    
    existing_user = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    hashed_pwd = hash_password(user_in.password)

    new_user = User(username=user_in.username, email=user_in.email, password_hash=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
