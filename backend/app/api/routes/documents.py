from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from pathlib import Path

from ...core.config import settings
from ...core.logger import logger
from ...models.document import Document, DocumentCreate, DocumentUpdate
from ...services.document_loader import DocumentLoader
from ...services.rag_pipeline import RAGPipeline
from ...core.security import verify_token
from ...db.session import get_db

router = APIRouter()
document_loader = DocumentLoader()
rag_pipeline = RAGPipeline()

@router.post("/upload/")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    try:
        # Validate file type
        file_ext = file.filename.lower().split(".")[-1]
        if f".{file_ext}" not in settings.SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Create document record
        doc_id = str(uuid.uuid4())
        document = Document(
            id=doc_id,
            title=file.filename,
            file_path=f"{settings.UPLOAD_DIR}/{doc_id}.{file_ext}",
            file_type=file_ext,
            upload_time=datetime.utcnow(),
            user_id=user_id,
            size_bytes=0  # Will be updated after saving
        )
        
        # Save file
        file_path = settings.UPLOAD_DIR / f"{doc_id}.{file_ext}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            document.size_bytes = len(content)
        
        # Process document
        chunks = await document_loader.load_document(file_path)
        
        # Store chunks in vector store
        chunk_ids = await rag_pipeline.process_document(
            file_path,
            metadata={
                "doc_id": doc_id,
                "title": document.title,
                "file_type": document.file_type
            }
        )
        
        # Update document with chunk IDs
        document.chunk_ids = chunk_ids
        document.processed = True
        
        # Save to database
        db.add(document)
        db.commit()
        
        return {"message": "Document uploaded and processed successfully", "document_id": doc_id}
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/")
async def query_documents(
    query: str,
    image_data: str = None,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Query documents using RAG."""
    try:
        response = await rag_pipeline.query(query, image_data)
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/", response_model=List[Document])
async def get_documents(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all documents for a user."""
    documents = db.query(Document).filter(Document.user_id == user_id).all()
    return documents

@router.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a specific document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
