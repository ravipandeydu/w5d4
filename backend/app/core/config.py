from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Base
    PROJECT_NAME: str = "Notebook LLM"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Claude API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = "claude-3-sonnet-20240229"
    
    # Database
    SQLITE_URL: str = "sqlite:///./notebook_llm.db"
    
    # Vector Store
    VECTOR_STORE_PATH: str = "./data/chroma"
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    
    # File Storage
    UPLOAD_DIR: Path = Path("./data/uploads")
    PROCESSED_DIR: Path = Path("./data/processed")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # Supported File Types
    SUPPORTED_EXTENSIONS: set = {
        # Documents
        ".pdf", ".docx", ".txt", ".md",
        # Spreadsheets
        ".csv", ".xlsx",
        # Presentations
        ".pptx",
        # Code & Notebooks
        ".ipynb", ".py",
        # Images
        ".png", ".jpg", ".jpeg",
        # Web
        ".html"
    }
    
    # Real-time
    ENABLE_WEBSOCKET: bool = True
    FIREBASE_CREDENTIALS: Optional[Dict[str, Any]] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create upload and processed directories
settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Ensure vector store directory exists
Path(settings.VECTOR_STORE_PATH).mkdir(parents=True, exist_ok=True)
