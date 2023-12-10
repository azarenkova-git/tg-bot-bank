from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models import Base


def setup_session(persist=False) -> Session:
    """Создает сессию для работы с БД"""

    engine = create_engine('sqlite:///:memory:' if not persist else 'sqlite:///bank_bot.db')
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    return session_maker()
