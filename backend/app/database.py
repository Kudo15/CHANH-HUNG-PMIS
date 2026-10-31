from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session as DBSession

from app.config import Settings


class Base(DeclarativeBase):
    """Empty metadata; business schemas require a separate approved task."""


def build_engine(settings: Settings) -> Engine | None:
    if settings.database_url is None:
        return None
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_timeout=3,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
    )


def get_engine(request: Request) -> Engine | None:
    return request.app.state.engine


def database_available(engine: Engine | None) -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT 1")).scalar_one() == 1
    except SQLAlchemyError:
        # Health responses must not expose driver exceptions or connection credentials.
        return False


def get_db(request: Request) -> Generator[DBSession, None, None]:
    engine = request.app.state.engine
    if engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    with DBSession(bind=engine) as session:
        yield session
