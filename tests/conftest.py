import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup environment variables for test execution BEFORE importing app components
import os
os.environ["API_KEY"] = "test-secret-key-12345"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["REDIS_HOST"] = "localhost"
os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"

from app.main import app
from app.database.session import Base, get_db
from app.services.cache_service import cache_service
from app.services.model_service import model_service
from app.api.dependencies import get_database_session

# Create SQLite database engine for unit tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mock classes for testing
class MockMLModel:
    def predict(self, df):
        # Custom prediction logic for testing
        bmi = df["bmi"].iloc[0]
        glucose = df["glucose_level"].iloc[0]
        if bmi > 30 or glucose > 140:
            return [0.85]  # High Risk
        elif bmi < 20:
            return [0.15]  # Low Risk
        return [0.50]      # Medium Risk

class MockRedisClient:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, val):
        self.store[key] = val
        return True

    def ping(self):
        return True

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create the database schema inside SQLite
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Dispose of engine to release file lock on Windows
    engine.dispose()
    # Cleanup file
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def mock_dependencies(db_session):
    # Override FastAPI database session dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_database_session] = override_get_db
    
    # Mock Redis client inside cache_service
    mock_redis = MockRedisClient()
    cache_service.client = mock_redis
    
    # Mock MLflow model inside model_service
    model_service.model = MockMLModel()
    model_service.model_version = "1"
    model_service.metadata = {
        "name": "disease-risk-model",
        "version": "1",
        "stage": "Production"
    }

    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-secret-key-12345"}
