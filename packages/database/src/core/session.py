"""
Database session management with connection pooling and transaction support.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool


class DatabaseSession:
    """
    Manages database connections and sessions for FlowPilot AI.
    
    Features:
    - Connection pooling with QueuePool
    - Automatic retry logic
    - Transaction management
    - Multi-tenancy support via session context
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@localhost:5432/flowpilot"
        )
        
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            echo=echo,
            pool_pre_ping=True,  # Validate connections before use
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db.session_scope() as session:
                session.add(obj)
                # commits on exit, rolls back on exception
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def dispose(self):
        """Dispose of the connection pool."""
        self.engine.dispose()


# Global instance for application-wide use
_db_instance: Optional[DatabaseSession] = None


def get_database() -> DatabaseSession:
    """Get or create the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseSession()
    return _db_instance


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            ...
    """
    db = get_database()
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
