"""Embedding generation utilities."""
import logging
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

from config import EMBEDDING_MODEL, EMBEDDING_DIMENSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Handles text embedding generation."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Initialize the embedding generator."""
        self.model_name = model_name
        self.model = None
        self.dimension = EMBEDDING_DIMENSION

    def load_model(self) -> None:
        """Load the embedding model."""
        logger.info(f"Loading embedding model: {self.model_name}")
        try:
            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

            self.model = SentenceTransformer(self.model_name, device=device)
            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts using optimized numpy operations."""
        if self.model is None:
            self.load_model()

        logger.info(f"Generating embeddings for {len(texts)} texts")

        try:
            # Pre-allocate numpy array for better performance
            total_texts = len(texts)
            embeddings_list = []

            for i in tqdm(range(0, total_texts, batch_size), desc="Generating embeddings"):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_tensor=False,
                    convert_to_numpy=True,  # Directly get numpy arrays
                    show_progress_bar=False
                )
                embeddings_list.append(batch_embeddings)

            # Use numpy.vstack for efficient concatenation
            embeddings_array = np.vstack(embeddings_list).astype(np.float32)
            logger.info(f"Generated embeddings shape: {embeddings_array.shape}")

            return embeddings_array

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text using optimized numpy operations."""
        if self.model is None:
            self.load_model()

        try:
            # Use convert_to_numpy=True for direct numpy array output
            embedding = self.model.encode(
                [text],
                convert_to_tensor=False,
                convert_to_numpy=True
            )[0]
            return embedding.astype(np.float32)

        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            raise

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }


class EmbeddingUtils:
    """Utility functions for working with embeddings."""

    @staticmethod
    def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
        """Normalize embeddings to unit length."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-8)  # Add small epsilon to avoid division by zero
        return normalized.astype(np.float32)

    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    @staticmethod
    def batch_cosine_similarity(query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between a query and a batch of embeddings."""
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Calculate similarities
        similarities = np.dot(embeddings_norm, query_norm)
        return similarities

    @staticmethod
    def save_embeddings(embeddings: np.ndarray, file_path: str) -> None:
        """Save embeddings to a numpy file."""
        logger.info(f"Saving embeddings to {file_path}")
        np.save(file_path, embeddings)
        logger.info("Embeddings saved successfully")

    @staticmethod
    def load_embeddings(file_path: str) -> np.ndarray:
        """Load embeddings from a numpy file."""
        logger.info(f"Loading embeddings from {file_path}")
        embeddings = np.load(file_path)
        logger.info(f"Loaded embeddings shape: {embeddings.shape}")
        return embeddings

    @staticmethod
    def compute_similarity_matrix(embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
        """Compute cosine similarity matrix between two sets of embeddings using vectorized operations."""
        # Normalize both sets of embeddings
        norm1 = np.linalg.norm(embeddings1, axis=1, keepdims=True)
        norm2 = np.linalg.norm(embeddings2, axis=1, keepdims=True)

        embeddings1_norm = embeddings1 / (norm1 + 1e-8)
        embeddings2_norm = embeddings2 / (norm2 + 1e-8)

        # Compute similarity matrix using matrix multiplication
        similarity_matrix = np.dot(embeddings1_norm, embeddings2_norm.T)

        return similarity_matrix

    @staticmethod
    def find_top_k_similar(query_embedding: np.ndarray, embeddings: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Find top-k most similar embeddings using efficient numpy operations."""
        similarities = EmbeddingUtils.batch_cosine_similarity(query_embedding, embeddings)

        # Use numpy.argpartition for efficient top-k selection
        if k >= len(similarities):
            top_k_indices = np.argsort(similarities)[::-1]
        else:
            # More efficient for large arrays when k is small
            top_k_indices = np.argpartition(similarities, -k)[-k:]
            top_k_indices = top_k_indices[np.argsort(similarities[top_k_indices])[::-1]]

        top_k_similarities = similarities[top_k_indices]

        return top_k_similarities, top_k_indices