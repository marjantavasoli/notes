from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import  SQLModel
from contextlib import asynccontextmanager
from models import User,Note,Tag,NoteTag  #noqe

SQLITE_DATABASE = "sqlite+aiosqlite:///./app.db"
engine = create_async_engine(SQLITE_DATABASE,connect_args={'check_same_thread': False})
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_tables():
    print("=== create_tables CALLED ===")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print(f"=== Tables in metadata: {list(SQLModel.metadata.tables.keys())} ===")



async def get_session():
    async with async_session() as session:
        yield session



@asynccontextmanager
async def lifespan(app):
    await create_tables()
    yield