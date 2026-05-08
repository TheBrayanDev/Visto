import time
from collections.abc import Generator
from sqlmodel import Session, SQLModel, create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/visto_db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def init_db():
    for attempt in range(30):
        try:
            SQLModel.metadata.create_all(engine)
            return
        except Exception:
            if attempt < 29:
                time.sleep(2)
            else:
                raise


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
