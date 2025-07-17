from typing import List, Dict, Any, Optional
from pathlib import Path
import base64
import anthropic
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import chromadb

from ..core.config import settings
from ..core.logger import logger
from ..models.document import DocumentChunk

class RAGPipeline:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Initialize embedding model
        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=settings.VECTOR_STORE_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.collection = chroma_client.get_or_create_collection(
            name="document_store",
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"}
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    async def process_document(self, document_path: Path, metadata: Dict[str, Any]) -> List[str]:
        """Process a document and store its chunks in the vector store."""
        try:
            # Extract text and create chunks
            chunks = self._create_chunks(document_path, metadata)
            
            # Store chunks in vector store
            chunk_ids = []
            for chunk in chunks:
                chunk_id = f"{metadata['doc_id']}_{len(chunk_ids)}"
                
                # Get embeddings
                embeddings = self.embedding_model.embed_documents([chunk.text])
                
                # Store in ChromaDB
                self.collection.add(
                    ids=[chunk_id],
                    embeddings=embeddings,
                    documents=[chunk.text],
                    metadatas=[{
                        "doc_id": metadata["doc_id"],
                        "chunk_type": chunk.chunk_type,
                        "page_num": chunk.page_num,
                        **metadata
                    }]
                )
                chunk_ids.append(chunk_id)
            
            return chunk_ids
            
        except Exception as e:
            logger.error(f"Error processing document {document_path}: {str(e)}")
            raise

    async def query(self, query: str, image_data: Optional[str] = None) -> Dict[str, Any]:
        """Query the RAG system with text and optional image."""
        try:
            # Get relevant chunks from vector store
            query_embedding = self.embedding_model.embed_query(query)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                include=["documents", "metadatas"]
            )
            
            # Prepare context from retrieved chunks
            context = "\n\n".join(results["documents"][0])
            
            # Prepare messages for Claude
            messages = [
                {
                    "role": "system",
                    "content": """You are an AI assistant helping users understand technical documents. 
                    Answer questions based on the provided context. If you cannot answer from the context, 
                    say so. Always cite sources using [doc_id:page] format."""
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                }
            ]
            
            # Add image if provided
            if image_data:
                messages[1]["content"] = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": messages[1]["content"]
                    }
                ]
            
            # Get response from Claude
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1000,
                messages=messages
            )
            
            return {
                "answer": response.content[0].text,
                "sources": [m["doc_id"] for m in results["metadatas"][0]]
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {str(e)}")
            raise

    def _create_chunks(self, document_path: Path, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """Create chunks from a document."""
        # This is a placeholder - actual implementation would use unstructured and
        # custom parsers for different file types
        chunks = []
        # Implementation details will be added in document_loader.py
        return chunks
