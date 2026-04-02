from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import QueuePool
from .settings import settings
from contextlib import contextmanager

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,  
    echo=settings.BACKEND_DEBUG  
)
meta = MetaData()

def get_db_connection():
    
    connection = engine.connect()
    transaction = connection.begin()

    try:
        yield connection
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()

@contextmanager
def get_db_transaction():
    
    connection = engine.connect()
    transaction = connection.begin()

    try:
        yield connection
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()

class ConnectionManager:

    def __init__(self):
        self._connection = None
        self._transaction = None

    def _ensure_connection(self):
        
        if self._connection is None or self._connection.closed:
            self._connection = engine.connect()
            self._transaction = self._connection.begin()
        return self._connection

    def execute(self, statement, *args, **kwargs):
        
        connection = self._ensure_connection()
        return connection.execute(statement, *args, **kwargs)

    def execution_options(self, **options):
        
        return self

    def begin(self):
        
        connection = self._ensure_connection()
        return self._transaction

    def commit(self):
        
        if self._transaction:
            try:
                self._transaction.commit()
            except Exception:
                pass
            finally:
                self._transaction = None
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None

    def rollback(self):
        
        if self._transaction:
            try:
                self._transaction.rollback()
            except Exception:
                pass
            finally:
                self._transaction = None
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            finally:
                self._connection = None

    def close(self):
        
        self.rollback()

conn = ConnectionManager()
