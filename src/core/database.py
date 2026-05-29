from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import config as cfg


class DatabaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 30,
        max_overflow: int = 10,
    ):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session_factory() as session:
            yield session

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_session_factory() as session:
            yield session

db_conn = DatabaseHelper(
    url=cfg.db.url(),
    echo=cfg.db.echo,
    echo_pool=cfg.db.echo_pool,
    pool_size=cfg.db.pool_size,
    max_overflow=cfg.db.max_overflow,
)
