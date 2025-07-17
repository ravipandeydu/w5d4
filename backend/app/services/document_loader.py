from typing import List, Dict, Any
from pathlib import Path
import base64
from PIL import Image
import io
import pandas as pd
import nbformat
import markdown
from unstructured.partition.auto import partition
from unstructured.partition.image import partition_image
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.pptx import partition_pptx

from ..core.logger import logger
from ..models.document import DocumentChunk, ChunkType

class DocumentLoader:
    def __init__(self):
        self.handlers = {
            ".pdf": self._handle_pdf,
            ".docx": self._handle_docx,
            ".pptx": self._handle_pptx,
            ".xlsx": self._handle_excel,
            ".csv": self._handle_csv,
            ".md": self._handle_markdown,
            ".ipynb": self._handle_notebook,
            ".png": self._handle_image,
            ".jpg": self._handle_image,
            ".jpeg": self._handle_image,
            ".html": self._handle_html,
        }

    async def load_document(self, file_path: Path) -> List[DocumentChunk]:
        """Load a document and return its chunks."""
        try:
            suffix = file_path.suffix.lower()
            if suffix not in self.handlers:
                raise ValueError(f"Unsupported file type: {suffix}")
            
            return await self.handlers[suffix](file_path)
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise

    async def _handle_pdf(self, file_path: Path) -> List[DocumentChunk]:
        """Handle PDF documents."""
        chunks = []
        elements = partition_pdf(file_path)
        
        for idx, element in enumerate(elements):
            chunk_type = ChunkType.TEXT
            if element.type == "Image":
                chunk_type = ChunkType.IMAGE
                # Convert image to base64
                img_data = base64.b64encode(element.image).decode()
            elif element.type == "Table":
                chunk_type = ChunkType.TABLE
            
            chunks.append(DocumentChunk(
                text=str(element),
                chunk_type=chunk_type,
                page_num=element.page_number or idx // 3,  # Approximate if no page number
                metadata={"type": element.type}
            ))
        
        return chunks

    async def _handle_docx(self, file_path: Path) -> List[DocumentChunk]:
        """Handle Word documents."""
        chunks = []
        elements = partition_docx(file_path)
        
        for idx, element in enumerate(elements):
            chunk_type = ChunkType.TEXT
            if hasattr(element, "image"):
                chunk_type = ChunkType.IMAGE
            elif hasattr(element, "cells"):
                chunk_type = ChunkType.TABLE
            
            chunks.append(DocumentChunk(
                text=str(element),
                chunk_type=chunk_type,
                page_num=idx // 3,  # Approximate page numbers
                metadata={"type": element.type}
            ))
        
        return chunks

    async def _handle_pptx(self, file_path: Path) -> List[DocumentChunk]:
        """Handle PowerPoint presentations."""
        chunks = []
        elements = partition_pptx(file_path)
        
        for element in elements:
            chunk_type = ChunkType.TEXT
            if hasattr(element, "image"):
                chunk_type = ChunkType.IMAGE
            
            chunks.append(DocumentChunk(
                text=str(element),
                chunk_type=chunk_type,
                page_num=element.page_number,
                metadata={"type": element.type}
            ))
        
        return chunks

    async def _handle_excel(self, file_path: Path) -> List[DocumentChunk]:
        """Handle Excel files."""
        chunks = []
        df = pd.read_excel(file_path)
        
        # Process each sheet
        for sheet_name, sheet_df in df.items():
            # Convert DataFrame to string representation
            table_str = sheet_df.to_string()
            chunks.append(DocumentChunk(
                text=table_str,
                chunk_type=ChunkType.TABLE,
                page_num=0,
                metadata={"sheet_name": sheet_name}
            ))
        
        return chunks

    async def _handle_csv(self, file_path: Path) -> List[DocumentChunk]:
        """Handle CSV files."""
        df = pd.read_csv(file_path)
        table_str = df.to_string()
        
        return [DocumentChunk(
            text=table_str,
            chunk_type=ChunkType.TABLE,
            page_num=0,
            metadata={}
        )]

    async def _handle_markdown(self, file_path: Path) -> List[DocumentChunk]:
        """Handle Markdown files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        
        # Convert to HTML first
        html = markdown.markdown(md_text)
        
        # Use unstructured to parse HTML
        elements = partition(text=html)
        
        chunks = []
        for idx, element in enumerate(elements):
            chunks.append(DocumentChunk(
                text=str(element),
                chunk_type=ChunkType.TEXT,
                page_num=0,
                metadata={"type": "markdown"}
            ))
        
        return chunks

    async def _handle_notebook(self, file_path: Path) -> List[DocumentChunk]:
        """Handle Jupyter notebooks."""
        with open(file_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        
        chunks = []
        for idx, cell in enumerate(nb.cells):
            chunk_type = ChunkType.CODE if cell.cell_type == "code" else ChunkType.TEXT
            
            chunks.append(DocumentChunk(
                text=cell.source,
                chunk_type=chunk_type,
                page_num=0,
                metadata={"cell_type": cell.cell_type, "cell_number": idx}
            ))
        
        return chunks

    async def _handle_image(self, file_path: Path) -> List[DocumentChunk]:
        """Handle image files."""
        # Open and convert image to base64
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Use unstructured to extract text from image
        elements = partition_image(file_path)
        
        chunks = []
        # Add the image itself
        chunks.append(DocumentChunk(
            text=img_base64,
            chunk_type=ChunkType.IMAGE,
            page_num=0,
            metadata={"type": "image"}
        ))
        
        # Add any extracted text
        for element in elements:
            if str(element).strip():
                chunks.append(DocumentChunk(
                    text=str(element),
                    chunk_type=ChunkType.TEXT,
                    page_num=0,
                    metadata={"type": "image_text"}
                ))
        
        return chunks

    async def _handle_html(self, file_path: Path) -> List[DocumentChunk]:
        """Handle HTML files."""
        elements = partition(filename=str(file_path))
        
        chunks = []
        for idx, element in enumerate(elements):
            chunk_type = ChunkType.TEXT
            if hasattr(element, "image"):
                chunk_type = ChunkType.IMAGE
            elif hasattr(element, "cells"):
                chunk_type = ChunkType.TABLE
            
            chunks.append(DocumentChunk(
                text=str(element),
                chunk_type=chunk_type,
                page_num=0,
                metadata={"type": element.type}
            ))
        
        return chunks
