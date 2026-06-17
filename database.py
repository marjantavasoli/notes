from sqlalchemy.orm.session import sessionmaker
from sqlmodel import create_engine, SQLModel,Session
from contextlib import contextmanager


SQLITE_DATABASE = "sqlite:///./app.db"
engine = create_engine(SQLITE_DATABASE,connect_args={'check_same_thread': False})


def create_tables():
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session



@contextmanager
def life_span():
    create_tables()
    yield