"""FAISS index utilities for vector similarity search."""
import logging
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import faiss

from config import EMBEDDING_DIMENSION, FAISS_NPROBE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FAISSIndex:
    """FAISS-based vector similarity search index."""

    def __init__(self, dimension: int = EMBEDDING_DIMENSION):
        """Initialize the FAISS index."""
        self.dimension = dimension
        self.index = None
        self.metadata = []  # Store metadata for each vector
        self.is_trained = False

    def create_index(self, index_type: str = "flat") -> None:
        """Create a new FAISS index.

        Args:
            index_type: Type of index ('flat', 'ivf', 'hnsw')
        """
        logger.info(f"Creating {index_type} index with dimension {self.dimension}")

        if index_type == "flat":
            # Simple brute-force L2 search
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine similarity)

        elif index_type == "ivf":
            # Inverted File index for faster search
            quantizer = faiss.IndexFlatIP(self.dimension)
            nlist = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            self.index.nprobe = FAISS_NPROBE

        elif index_type == "hnsw":
            # Hierarchical Navigable Small World
            M = 32  # Number of bi-directional links for each node
            self.index = faiss.IndexHNSWFlat(self.dimension, M)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 128

        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        logger.info(f"Index created successfully: {type(self.index).__name__}")

    def train_index(self, embeddings: np.ndarray) -> None:
        """Train the index if necessary (for IVF indices)."""
        if self.index is None:
            raise ValueError("Index not created. Call create_index() first.")

        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            logger.info("Training index...")
            # Normalize embeddings for cosine similarity
            normalized_embeddings = self._normalize_embeddings(embeddings)
            self.index.train(normalized_embeddings)
            self.is_trained = True
            logger.info("Index training completed")
        else:
            self.is_trained = True
            logger.info("Index doesn't require training or is already trained")

    def add_embeddings(self, embeddings: np.ndarray, metadata: List[dict] = None) -> None:
        """Add embeddings to the index.

        Args:
            embeddings: Array of embeddings to add
            metadata: List of metadata dictionaries for each embedding
        """
        if self.index is None:
            raise ValueError("Index not created. Call create_index() first.")

        # Ensure index is trained if necessary
        if not self.is_trained:
            self.train_index(embeddings)

        logger.info(f"Adding {len(embeddings)} embeddings to index")

        # Normalize embeddings for cosine similarity
        normalized_embeddings = self._normalize_embeddings(embeddings)

        # Add to FAISS index
        self.index.add(normalized_embeddings)

        # Store metadata
        if metadata is None:
            metadata = [{"id": i} for i in range(len(embeddings))]

        self.metadata.extend(metadata)

        logger.info(f"Total vectors in index: {self.index.ntotal}")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray, List[dict]]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector
            k: Number of results to return

        Returns:
            Tuple of (similarities, indices, metadata)
        """
        if self.index is None or self.index.ntotal == 0:
            return np.array([]), np.array([]), []

        # Normalize query embedding
        normalized_query = self._normalize_embeddings(query_embedding.reshape(1, -1))

        # Search
        similarities, indices = self.index.search(normalized_query, k)

        # Filter out invalid indices (-1)
        valid_mask = indices[0] != -1
        valid_similarities = similarities[0][valid_mask]
        valid_indices = indices[0][valid_mask]

        # Get metadata for valid results
        valid_metadata = [self.metadata[idx] for idx in valid_indices]

        return valid_similarities, valid_indices, valid_metadata

    def save(self, index_path: Path, metadata_path: Path) -> None:
        """Save the index and metadata to files."""
        if self.index is None:
            raise ValueError("No index to save")

        logger.info(f"Saving index to {index_path}")

        # Save FAISS index
        faiss.write_index(self.index, str(index_path))

        # Save metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'dimension': self.dimension,
                'is_trained': self.is_trained
            }, f)

        logger.info("Index and metadata saved successfully")

    def load(self, index_path: Path, metadata_path: Path) -> None:
        """Load the index and metadata from files."""
        logger.info(f"Loading index from {index_path}")

        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load FAISS index
        self.index = faiss.read_index(str(index_path))

        # Load metadata
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.metadata = data['metadata']
            self.dimension = data['dimension']
            self.is_trained = data['is_trained']

        logger.info(f"Index loaded successfully with {self.index.ntotal} vectors")

    def get_stats(self) -> dict:
        """Get statistics about the index."""
        if self.index is None:
            return {"status": "not_created"}

        return {
            "type": type(self.index).__name__,
            "dimension": self.dimension,
            "total_vectors": self.index.ntotal,
            "is_trained": self.is_trained,
            "metadata_count": len(self.metadata)
        }

    @staticmethod
    def _normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length for cosine similarity."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-8)  # Add small epsilon to avoid division by zero
        return normalized.astype(np.float32)


class IndexManager:
    """High-level interface for managing FAISS indices."""

    def __init__(self, models_dir: Path):
        """Initialize the index manager."""
        self.models_dir = models_dir
        self.models_dir.mkdir(exist_ok=True)

    def create_and_save_index(self, embeddings: np.ndarray, metadata: List[dict],
                             index_name: str = "default", index_type: str = "flat") -> FAISSIndex:
        """Create, populate, and save a new index."""
        index = FAISSIndex()
        index.create_index(index_type)
        index.add_embeddings(embeddings, metadata)

        # Save index
        index_path = self.models_dir / f"{index_name}_index.bin"
        metadata_path = self.models_dir / f"{index_name}_metadata.pkl"

        index.save(index_path, metadata_path)

        return index

    def load_index(self, index_name: str = "default") -> FAISSIndex:
        """Load an existing index."""
        index_path = self.models_dir / f"{index_name}_index.bin"
        metadata_path = self.models_dir / f"{index_name}_metadata.pkl"

        index = FAISSIndex()
        index.load(index_path, metadata_path)

        return index

    def list_available_indices(self) -> List[str]:
        """List all available indices."""
        index_files = list(self.models_dir.glob("*_index.bin"))
        return [f.stem.replace("_index", "") for f in index_files]