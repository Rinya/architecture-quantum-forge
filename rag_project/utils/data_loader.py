"""Data loading and processing utilities."""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkData:
    """Represents a document chunk with metadata."""

    def __init__(self, text: str, document_title: str, chunk_id: str,
                 file_path: Optional[str] = None, start_position: Optional[int] = None,
                 embedding: Optional[np.ndarray] = None):
        self.text = text
        self.document_title = document_title
        self.chunk_id = chunk_id
        self.file_path = file_path
        self.start_position = start_position
        self.embedding = embedding

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary representation."""
        data = {
            "text": self.text,
            "document_title": self.document_title,
            "chunk_id": self.chunk_id,
        }
        if self.file_path:
            data["file_path"] = self.file_path
        if self.start_position is not None:
            data["start_position"] = self.start_position
        if self.embedding is not None:
            data["embedding"] = self.embedding.tolist()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkData':
        """Create ChunkData from dictionary."""
        embedding = None
        if "embedding" in data:
            embedding = np.array(data["embedding"], dtype=np.float32)

        # Handle both "text" and "content" fields for backward compatibility
        text = data.get("text") or data.get("content", "")

        return cls(
            text=text,
            document_title=data["document_title"],
            chunk_id=data["chunk_id"],
            file_path=data.get("file_path"),
            start_position=data.get("start_position"),
            embedding=embedding
        )


class DataLoader:
    """Handles loading and processing of chunk data."""

    @staticmethod
    def load_chunks_from_json(file_path: Path) -> List[ChunkData]:
        """Load chunks from JSON file."""
        logger.info(f"Loading chunks from {file_path}")

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            chunks = []
            for item in raw_data:
                chunk = ChunkData.from_dict(item)
                chunks.append(chunk)

            logger.info(f"Loaded {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            raise

    @staticmethod
    def save_chunks_to_json(chunks: List[ChunkData], file_path: Path) -> None:
        """Save chunks to JSON file."""
        logger.info(f"Saving {len(chunks)} chunks to {file_path}")

        try:
            data = [chunk.to_dict() for chunk in chunks]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info("Chunks saved successfully")

        except Exception as e:
            logger.error(f"Error saving chunks: {e}")
            raise

    @staticmethod
    def prepare_embeddings_data(chunks: List[ChunkData]) -> tuple[List[str], List[str], np.ndarray]:
        """Prepare data for embedding processing."""
        texts = []
        chunk_ids = []
        embeddings = []

        for chunk in chunks:
            texts.append(chunk.text)
            chunk_ids.append(chunk.chunk_id)
            if chunk.embedding is not None:
                embeddings.append(chunk.embedding)

        embeddings_array = np.array(embeddings, dtype=np.float32) if embeddings else None
        return texts, chunk_ids, embeddings_array

    @staticmethod
    def filter_chunks_by_document(chunks: List[ChunkData], document_title: str) -> List[ChunkData]:
        """Filter chunks by document title."""
        return [chunk for chunk in chunks if chunk.document_title == document_title]

    @staticmethod
    def get_unique_documents(chunks: List[ChunkData]) -> List[str]:
        """Get list of unique document titles."""
        return list(set(chunk.document_title for chunk in chunks))