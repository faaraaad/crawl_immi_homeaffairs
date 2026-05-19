from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from immi_crawler.config import settings

# Create async engine with asyncpg
# We disable echo by default, but it can be enabled for debugging
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
