from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from database import engine, get_db, Base
from models import User, Message, Group
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    MessageCreate, MessageResponse, MessageUpdate,
    GroupCreate, GroupResponse, GroupAddMembers
)
from auth import hash_password, verify_password, create_access_token, decode_token
from websocket_manager import manager

# Создаём таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Папка для загрузки файлов
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Создаём приложение
app = FastAPI(
    title="UzGidroChat API",
    description="Корпоративный мессенджер для Узбекгидроэнерго",
    version="2.0.0"
)

# Подключаем статические файлы (для доступа к загруженным файлам)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_file_type(filename: str) -> str:
    """Определяет тип файла по расширению"""
    ext = filename.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
        return 'image'
    elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
        return 'video'
    elif ext in ['mp3', 'wav', 'ogg', 'flac']:
        return 'audio'
    else:
        return 'document'


@app.get("/")
async def root():
    return {"message": "UzGidroChat API работает!"}


# ==================== USERS ====================

@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email уже используется")
    
    hashed_pwd = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pwd,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@app.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    
    if not db_user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    access_token = create_access_token(data={"sub": db_user.username, "user_id": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }


@app.get("/users", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@app.get("/users/online")
async def get_online_users():
    return {"online_users": manager.get_online_users()}

@app.post("/users/{user_id}/avatar")
async def upload_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Генерируем уникальное имя файла
    file_ext = file.filename.split('.')[-1]
    unique_filename = f"avatar_{user_id}_{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Обновляем путь к аватарке в базе
    user.avatar_path = f"/uploads/{unique_filename}"
    db.commit()
    db.refresh(user)
    
    return {"avatar_path": user.avatar_path}


@app.delete("/users/{user_id}/avatar")
async def delete_avatar(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Удаляем файл если существует
    if user.avatar_path:
        file_path = user.avatar_path.replace("/uploads/", "")
        full_path = os.path.join(UPLOAD_DIR, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    
    user.avatar_path = None
    db.commit()
    
    return {"message": "Аватарка удалена"}


# ==================== GROUPS ====================

@app.post("/groups", response_model=GroupResponse)
async def create_group(group: GroupCreate, creator_id: int, db: Session = Depends(get_db)):
    db_group = Group(
        name=group.name,
        description=group.description,
        creator_id=creator_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    creator = db.query(User).filter(User.id == creator_id).first()
    if creator:
        db_group.members.append(creator)
    
    for member_id in group.member_ids:
        member = db.query(User).filter(User.id == member_id).first()
        if member and member not in db_group.members:
            db_group.members.append(member)
    
    db.commit()
    db.refresh(db_group)
    
    return db_group


@app.get("/groups", response_model=List[GroupResponse])
async def get_groups(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user.groups


@app.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return group


@app.post("/groups/{group_id}/members")
async def add_members(group_id: int, data: GroupAddMembers, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    for user_id in data.user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user and user not in group.members:
            group.members.append(user)
    
    db.commit()
    return {"message": "Участники добавлены"}


@app.delete("/groups/{group_id}/members/{user_id}")
async def remove_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user and user in group.members:
        group.members.remove(user)
        db.commit()
    
    return {"message": "Участник удалён"}


# ==================== MESSAGES ====================

@app.post("/messages", response_model=MessageResponse)
async def create_message(message: MessageCreate, db: Session = Depends(get_db)):
    db_message = Message(
        content=message.content,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        group_id=message.group_id,
        reply_to_id=message.reply_to_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    message_data = {
        "type": "new_message",
        "message": {
            "id": db_message.id,
            "content": db_message.content,
            "sender_id": db_message.sender_id,
            "receiver_id": db_message.receiver_id,
            "group_id": db_message.group_id,
            "file_name": db_message.file_name,
            "file_path": db_message.file_path,
            "file_type": db_message.file_type,
            "created_at": str(db_message.created_at)
        }
    }
    
    if message.receiver_id:
        await manager.send_personal_message(message_data, message.receiver_id)
    elif message.group_id:
        group = db.query(Group).filter(Group.id == message.group_id).first()
        if group:
            for member in group.members:
                if member.id != user_id:
                    await manager.send_personal_message(message_data, member.id)
    
    return db_message


@app.post("/messages/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = 0,
    receiver_id: Optional[int] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # Генерируем уникальное имя файла
    file_ext = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Определяем тип файла
    file_type = get_file_type(file.filename)
    
    # Создаём сообщение с файлом
    db_message = Message(
        content=None,
        sender_id=user_id,
        receiver_id=receiver_id,
        group_id=group_id,
        file_name=file.filename,
        file_path=f"/uploads/{unique_filename}",
        file_type=file_type
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Отправляем через WebSocket
    message_data = {
        "type": "new_message",
        "message": {
            "id": db_message.id,
            "content": db_message.content,
            "sender_id": db_message.sender_id,
            "receiver_id": db_message.receiver_id,
            "group_id": db_message.group_id,
            "file_name": db_message.file_name,
            "file_path": db_message.file_path,
            "file_type": db_message.file_type,
            "created_at": str(db_message.created_at)
        }
    }
    
    if receiver_id:
        await manager.send_personal_message(message_data, receiver_id)
    elif group_id:
        group = db.query(Group).filter(Group.id == group_id).first()
        if group:
            for member in group.members:
                if member.id != user_id:
                    await manager.send_personal_message(message_data, member.id)
    
    return {
        "id": db_message.id,
        "file_name": db_message.file_name,
        "file_path": db_message.file_path,
        "file_type": db_message.file_type,
        "created_at": str(db_message.created_at)
    }


@app.get("/messages/{user_id}/{other_user_id}", response_model=List[MessageResponse])
async def get_messages(user_id: int, other_user_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == user_id))
    ).order_by(Message.created_at).all()
    return messages


@app.get("/messages/group/{group_id}", response_model=List[MessageResponse])
async def get_group_messages(group_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        Message.group_id == group_id
    ).order_by(Message.created_at).all()
    return messages

@app.put("/messages/{message_id}")
async def edit_message(message_id: int, data: MessageUpdate, user_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    if message.sender_id != user_id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать чужое сообщение")
    
    message.content = data.content
    message.is_edited = True
    message.edited_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    
    # Уведомляем через WebSocket
    message_data = {
        "type": "message_edited",
        "message": {
            "id": message.id,
            "content": message.content,
            "is_edited": message.is_edited,
            "edited_at": str(message.edited_at)
        }
    }
    await manager.broadcast(message_data)
    
    return message


@app.delete("/messages/{message_id}")
async def delete_message(message_id: int, user_id: int, db: Session = Depends(get_db)):
    message = db.query(Message).filter(Message.id == message_id).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    if message.sender_id != user_id:
        raise HTTPException(status_code=403, detail="Нельзя удалить чужое сообщение")
    
    message.is_deleted = True
    message.content = None
    db.commit()
    
    # Уведомляем через WebSocket
    message_data = {
        "type": "message_deleted",
        "message_id": message.id
    }
    await manager.broadcast(message_data)
    
    return {"message": "Сообщение удалено"}


# ==================== WEBSOCKET ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, user_id)
    
    # Устанавливаем статус онлайн
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_online = True
        db.commit()
        # Уведомляем всех о статусе
        await manager.broadcast({"type": "user_online", "user_id": user_id})
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif data.get("type") == "typing":
                receiver_id = data.get("receiver_id")
                is_typing = data.get("is_typing", False)
                if receiver_id:
                    await manager.send_typing_status(user_id, receiver_id, is_typing)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        # Устанавливаем статус офлайн
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_online = False
            user.last_seen = datetime.utcnow()
            db.commit()
            # Уведомляем всех о статусе
            await manager.broadcast({"type": "user_offline", "user_id": user_id})


@app.get("/health")
async def health_check():
    return {"status": "healthy"}