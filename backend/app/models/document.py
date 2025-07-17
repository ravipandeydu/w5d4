from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ChunkType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    CODE = "code"

class DocumentChunk(BaseModel):
    text: str
    chunk_type: ChunkType
    page_num: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    id: str
    title: str
    file_path: str
    file_type: str
    upload_time: datetime
    user_id: str
    size_bytes: int
    num_pages: Optional[int] = None
    processed: bool = False
    chunk_ids: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentCreate(BaseModel):
    title: str
    file_type: str
    user_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processed: Optional[bool] = None
    chunk_ids: Optional[list[str]] = None
