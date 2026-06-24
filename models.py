from sqlmodel import Field, SQLModel,Relationship
from datetime import datetime, timezone


class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True, default=None)
    username: str = Field(unique=True, index=True)
    email: str | None = Field(unique=True, default=None, index=True)
    hashed_password: str
    notes: list["Note"] = Relationship(back_populates="owner")

class UserRead(SQLModel):
    id: int
    username: str
    email: str | None = None


class UserCreate(SQLModel):
    username: str
    password: str
    email: str | None = None


class UserUpdate(SQLModel):
    username: str | None = None
    email: str | None = None

class NoteTag(SQLModel, table=True):
    note_id: int = Field(foreign_key="note.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)



class Note(SQLModel, table=True):
    id: int|None= Field(primary_key=True, default=None)
    title: str
    content: str | None = None
    is_pinned: bool  = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    owner_id: int = Field(foreign_key="user.id", index=True)
    owner: "User" = Relationship(back_populates="notes")
    tags: list["Tag"] = Relationship(back_populates="notes", link_model= NoteTag)


class NoteCreate(SQLModel):
    title: str
    content: str|None = None
    is_pinned: bool = Field(default=False)


class NoteRead(SQLModel):
    id: int|None = None
    title: str
    content: str | None = None
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    owner_id: int

class NoteUpdate(NoteCreate):
    title: str | None = None
    is_pinned: bool = False


class Tag(SQLModel, table=True):
    id: int|None = Field(primary_key=True, default=None)
    name: str = Field(unique=True, index=True)
    notes: list["Note"] = Relationship(back_populates="tags", link_model= NoteTag)



