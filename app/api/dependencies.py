from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_api_key

# We re-export get_db and verify_api_key for convenience
def get_database_session() -> Generator[Session, None, None]:
    """Dependency generator to acquire database sessions."""
    yield from get_db()

# Common dependency grouping for secured prediction endpoints
class ProtectedEndpointDependencies:
    def __init__(
        self,
        db: Session = Depends(get_database_session),
        api_key: str = Depends(verify_api_key)
    ):
        self.db = db
        self.api_key = api_key
