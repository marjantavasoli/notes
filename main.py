from datetime import datetime, timezone

from fastapi import FastAPI,Depends,HTTPException,Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import func

from database import lifespan
from models import UserCreate, User, UserUpdate, UserRead, NoteCreate, Note, NoteRead, NoteUpdate, Tag, TagCreate, \
    TagRead, NoteTag,PaginatedNotes
from sqlmodel import select
from database import get_session
from auth import verify_password,hash_password,create_access_token,get_current_user


app = FastAPI(lifespan=lifespan)

@app.post("/register",response_model=UserRead)
async def register(user: UserCreate,session:AsyncSession=Depends(get_session)):
    existing_user = await session.exec(select(User).where(User.username == user.username))
    existing_user = existing_user.first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, email=user.email)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@app.post("/token")
async def login_for_get_token(session:AsyncSession=Depends(get_session),form_data: OAuth2PasswordRequestForm = Depends()):
    user = await session.exec(select(User).where(User.username == form_data.username))
    existing_user = user.first()
    if not existing_user or not verify_password(form_data.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": existing_user.username})
    print(access_token)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me",response_model=UserRead)
async def read_users_me(current_user:User=Depends(get_current_user)):
    return current_user


@app.post("/notes",response_model=NoteRead)
async def create_note(note_data:NoteCreate,current_user:User=Depends(get_current_user),session:AsyncSession=Depends(get_session)):
    note = Note(**note_data.model_dump(),owner_id=current_user.id)
    session.add(note)
    await session.commit()
    await session.refresh(note,attribute_names=["tags"])
    return note

@app.get("/notes",response_model=PaginatedNotes)
async def get_notes(pinned:bool|None=None,tag:str|None=None,
    search:str|None=None,offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),session:AsyncSession=Depends(get_session),
    current_user:User=Depends(get_current_user)):
    conditions = [Note.owner_id == current_user.id]
    if pinned is not None:
        conditions.append(Note.is_pinned == pinned)
    if search is not None:
        conditions.append(Note.title.contains(search)|Note.content.contains(search))
    if tag is not None:
        conditions.append(Note.tags.any(Tag.name==tag))
    statement = select(Note).where(*conditions).options(selectinload(Note.tags)).order_by(Note.created_at.desc()).limit(limit).offset(offset)
    count_statement = select(func.count()).select_from(Note).where(*conditions)
    items_result = await session.exec(statement)
    items = items_result.all()
    count_result = await session.exec(count_statement)
    total = count_result.one()
    return PaginatedNotes(items=items,total=total,limit=limit,offset=offset)



@app.get("/notes/{note_id}",response_model=NoteRead)
async def get_note(note_id:int,session:AsyncSession=Depends(get_session),current_user:User=Depends(get_current_user)):
    result = await session.exec(select (Note).where(Note.id==note_id).options(selectinload(Note.tags)))
    note = result.first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot get this")
    return note


@app.patch("/notes/{note_id}",response_model=NoteRead)
async def update_note(note_id:int,note:NoteUpdate,session:AsyncSession=Depends(get_session),current_user:User=Depends(get_current_user)):
    note_db =  await session.get(Note, note_id,options=[selectinload(Note.tags)])
    if note_db is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot update this")
    note_data = note.model_dump(exclude_unset=True, exclude_none=True)
    note_db.sqlmodel_update(obj=note_data)
    note_db.updated_at = datetime.now(tz=timezone.utc)
    session.add(note_db)
    await session.commit()
    await session.refresh(note_db,attribute_names=["tags"])
    return note_db

@app.delete("/notes/{note_id}")
async def delete_note(note_id:int,session:AsyncSession=Depends(get_session),current_user:User=Depends(get_current_user)):
    note_db = await session.get(Note, note_id)
    if note_db is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot delete this")
    await session.delete(note_db)
    await session.commit()
    return {"message": f"{note_db.title} has been deleted"}


@app.post("/notes/{note_id}/tags")
async def add_tag_to_note(note_id:int,tag_data:TagCreate,session:AsyncSession=Depends(get_session),current_user:User=Depends(get_current_user)):
    result = await session.exec(
        select(Note)
        .where(Note.id == note_id)
        .options(selectinload(Note.tags))
    )
    note = result.first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot add tag to this note")
    result = await session.exec(select(Tag).where(Tag.name == tag_data.name))
    tag = result.first()
    if tag is None:
        tag = Tag(name=tag_data.name)
        session.add(tag)

    elif tag in note.tags:
        return note

    note.tags.append(tag)
    session.add(note)
    await session.commit()
    await session.refresh(note,attribute_names= ['tags'])
    return note


@app.delete("/notes/{note_id}/tags/{tag_name}",response_model=NoteRead)
async def delete_tag_from_note(note_id:int,tag_name:str,session:AsyncSession=Depends(get_session),current_user:User=Depends(get_current_user)):
    result = await session.exec(select(Note).where(Note.id == note_id).options(selectinload(Note.tags)))
    note = result.first()
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You cannot delete tag from this note")
    tag_to_remove = next((t for t in note.tags if t.name==tag_name), None)
    if tag_to_remove is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    note.tags.remove(tag_to_remove)
    session.add(note)
    await session.commit()
    await session.refresh(note,attribute_names=['tags'])
    return note





