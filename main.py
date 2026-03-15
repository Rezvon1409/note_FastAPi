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


@app.post("/login")
def login(response: Response, user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Error")

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    session_id = str(uuid.uuid4())
    sessions[session_id] = user.id
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "Welcome"}

@app.post("/logout")
def logout(response: Response, request: Request):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    response.delete_cookie("session_id")
    return {"message": "Logged out"}



@app.get("/notes", response_model=list[NoteOut])
def get_my_notes(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    notes = db.query(Note).filter(Note.owner_id == user_id).all()
    return notes

@app.post("/notes", response_model=NoteOut)
def create_note(request: Request, note_in: NoteCreate, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    new_note = Note(title=note_in.title, content=note_in.content, owner_id=user_id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, note_in: NoteUpdate, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    if note_in.title is not None:
        note.title = note_in.title
    if note_in.content is not None:
        note.content = note_in.content
        
    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == user_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    db.delete(note)
    db.commit()
    return {"message": "Note deleted"}

@app.get("/admin/notes", response_model=list[NoteOut])
def get_all_notes_admin(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id(request)
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin")
        
    notes = db.query(Note).all()
    return notes

if __name__ == '__main__':
    uvicorn.run('main:app' , host='127.0.0.1' , port=8000 , reload=True)