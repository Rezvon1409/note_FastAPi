from sqlalchemy.orm import Session
from sqlalchemy import select
from models import User, Notes, Token
from datetime import datetime

def create_user(email: str, role: str, password: str, db: Session):
    new_user = User(email=email, password_hash=password, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_data(email: str, db: Session):
    stmt = select(User).where(User.email == email)
    user = db.scalars(stmt).one_or_none()
    return user


def create_token(user_id: int, token: str, expiry: datetime, db: Session):
    stmt = select(Token).where(Token.user_id == user_id)
    existing = db.scalars(stmt).one_or_none()
    if existing:
        existing.token = token
        existing.token_expiry = expiry
        db.commit()
        db.refresh(existing)
        return existing.token

    new_token = Token(user_id=user_id, token=token, token_expiry=expiry)
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token.token

def get_token_by_email(email: str, db: Session):
    stmt = select(Token).join(User).where(User.email == email)
    found_token = db.scalars(stmt).one_or_none()
    return found_token

def get_user_by_token(token: str, db: Session):
    stmt = select(User).join(Token).where(Token.token == token)
    found_user = db.scalars(stmt).one_or_none()
    if found_user and found_user.tokens.token_expiry < datetime.utcnow():
        return None  # expired
    return found_user

def login(email: str, password: str, db: Session):
    stmt = select(User).where(User.email == email, User.password_hash == password)
    user = db.scalars(stmt).one_or_none()
    return user

def create_note(title: str, description: str, user_id: int, db: Session):
    new_note = Notes(title=title, content=description, owner_id=user_id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

def update_note(new_title: str, new_description: str, note_id: int, db: Session):
    stmt = select(Notes).where(Notes.id == note_id)
    note = db.scalars(stmt).first()
    if not note:
        return None
    note.title = new_title
    note.content = new_description
    db.commit()
    db.refresh(note)
    return note

def delete_note(note_id: int, db: Session):
    stmt = select(Notes).where(Notes.id == note_id)
    note = db.scalars(stmt).first()
    if note:
        db.delete(note)
        db.commit()
        return True
    return False

def get_my_notes(user_id: int, db: Session):
    stmt = select(Notes).where(Notes.owner_id == user_id)
    notes = db.scalars(stmt).all()
    return notes or []

def get_note_by_id(note_id: int, db: Session):
    stmt = select(Notes).where(Notes.id == note_id)
    note = db.scalars(stmt).one_or_none()
    return note

def check_permission(user_id: int, note_id: int, db: Session):
    stmt = select(Notes).where(Notes.owner_id == user_id, Notes.id == note_id)
    note = db.scalars(stmt).one_or_none()
    return note is not None
