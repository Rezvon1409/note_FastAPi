import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import *
from database import get_db
from schemas import RegisterRequest, LoginRequest, NoteRequest
from auth import hash_password , verify_password
from quires import (
    create_user, get_user_by_data, create_token, get_user_by_token,
    create_note, update_note, delete_note, get_my_notes, get_note_by_id, check_permission
)

app = FastAPI()

TOKEN_EXPIRY_MINUTES = 30

def user_to_dict(user):
    return {"id": user.id, "email": user.email, "role": user.role}

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("token_for_login")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_user_by_token(token=token, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    return user

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(body: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(body.password)
    user = create_user(email=body.email, password=hashed, role=body.role, db=db)
    return user_to_dict(user)


from auth import hash_password, verify_password

from datetime import datetime, timedelta, timezone

@app.post("/login")
def login_user(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user_found = get_user_by_data(email=body.email, db=db)
    if not user_found or not verify_password(body.password, user_found.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    expiry = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    token = f"{user_found.id}_{int(expiry.timestamp())}"
    create_token(user_id=user_found.id, token=token, expiry=expiry, db=db)

    response.set_cookie(key="token_for_login", value=token, httponly=True)
    return {"message": "Success", "token": token, "user": user_to_dict(user_found)}




@app.post("/add-note")
def add_notes(body: NoteRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    note = create_note(title=body.title, description=body.description, user_id=current_user.id, db=db)
    return {"message": "success", "note": note}

@app.get("/get-my-notes")
def get_notes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    notes = get_my_notes(user_id=current_user.id, db=db)
    return {"message": "success", "notes": notes}

@app.put("/update-note/{note_id}")
def patch_note(note_id: int, body: NoteRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    note = get_note_by_id(note_id, db=db)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    if note.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
    updated = update_note(new_title=body.title, new_description=body.description, note_id=note_id, db=db)
    return {"message": "success", "note": updated}

@app.delete("/delete/{note_id}")
def delete_notes(note_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not check_permission(user_id=current_user.id, note_id=note_id, db=db) and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
    found = delete_note(note_id, db=db)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return {"message": "success"}


@app.get("/get-all-notes")
def get_all_notes(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin has access")

    notes = db.query(Notes).all()
    return {"message": "success", "notes": notes}


@app.get("/get-all-users")
def get_all_users(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin has access")

    users = db.query(User).all()
    return {"message": "success", "users": [user_to_dict(u) for u in users]}

@app.delete("/delete-user/{user_id}")
def delete_user(user_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins are allowed to delete users")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


@app.put("/update-user-role/{user_id}")
def update_user_role(user_id: int, new_role: str, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update user roles")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role
    db.commit()
    db.refresh(user)

    return {"message": "User role updated successfully", "user": user_to_dict(user)}




if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
