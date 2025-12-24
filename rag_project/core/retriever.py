"""Document retrieval system."""
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from utils.data_loader import ChunkData, DataLoader
from utils.embedding_generator import EmbeddingGenerator
from utils.faiss_index import FAISSIndex, IndexManager
from config import DEFAULT_TOP_K, SIMILARITY_THRESHOLD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Represents a single retrieval result."""
    chunk: ChunkData
    similarity_score: float
    rank: int


class DocumentRetriever:
    """Main document retrieval system."""

    def __init__(self, models_dir, embedding_model_name: str = None):
        """Initialize the retriever."""
        self.models_dir = models_dir
        self.embedding_generator = EmbeddingGenerator(embedding_model_name) if embedding_model_name else EmbeddingGenerator()
        self.index_manager = IndexManager(models_dir)
        self.faiss_index: Optional[FAISSIndex] = None
        self.chunks: List[ChunkData] = []

    def setup_from_chunks(self, chunks: List[ChunkData],
                         index_name: str = "default",
                         index_type: str = "flat",
                         force_rebuild: bool = False) -> None:
        """Setup the retriever from a list of chunks."""
        logger.info(f"Setting up retriever with {len(chunks)} chunks")

        self.chunks = chunks

        # Check if index already exists
        existing_indices = self.index_manager.list_available_indices()

        if index_name in existing_indices and not force_rebuild:
            logger.info(f"Loading existing index: {index_name}")
            self.faiss_index = self.index_manager.load_index(index_name)
        else:
            logger.info(f"Creating new index: {index_name}")
            self._build_index(chunks, index_name, index_type)

    def _build_index(self, chunks: List[ChunkData], index_name: str, index_type: str) -> None:
        """Build a new FAISS index from chunks."""
        # Extract texts and generate embeddings if needed
        texts = []
        embeddings = []

        for chunk in chunks:
            texts.append(chunk.text)

            if chunk.embedding is not None:
                embeddings.append(chunk.embedding)
            else:
                # Generate embedding for this chunk
                embedding = self.embedding_generator.generate_single_embedding(chunk.text)
                chunk.embedding = embedding
                embeddings.append(embedding)

        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)

        # Create metadata for FAISS index
        metadata = []
        for i, chunk in enumerate(chunks):
            metadata.append({
                "chunk_id": chunk.chunk_id,
                "document_title": chunk.document_title,
                "chunk_index": i
            })

        # Create and save index
        self.faiss_index = self.index_manager.create_and_save_index(
            embeddings_array, metadata, index_name, index_type
        )

        logger.info(f"Index built successfully with {len(embeddings)} embeddings")

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K,
                min_similarity: float = SIMILARITY_THRESHOLD) -> List[RetrievalResult]:
        """Retrieve relevant documents for a query."""
        if not self.faiss_index:
            raise ValueError("Retriever not set up. Call setup_from_chunks() first.")

        logger.info(f"Retrieving documents for query: '{query[:100]}...'")

        # Generate query embedding
        query_embedding = self.embedding_generator.generate_single_embedding(query)

        # Search in FAISS index
        similarities, indices, metadata = self.faiss_index.search(query_embedding, top_k)

        # Build results
        results = []
        for rank, (similarity, metadata_dict) in enumerate(zip(similarities, metadata)):
            if similarity >= min_similarity:
                chunk_index = metadata_dict["chunk_index"]
                chunk = self.chunks[chunk_index]

                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=float(similarity),
                    rank=rank + 1
                )
                results.append(result)

        logger.info(f"Retrieved {len(results)} relevant documents")
        return results

    def retrieve_by_document(self, query: str, document_title: str,
                           top_k: int = DEFAULT_TOP_K) -> List[RetrievalResult]:
        """Retrieve documents filtered by document title."""
        # First get all results
        all_results = self.retrieve(query, top_k * 3)  # Get more to allow filtering

        # Filter by document
        filtered_results = [
            result for result in all_results
            if result.chunk.document_title == document_title
        ]

        # Return top_k results
        return filtered_results[:top_k]

    def get_document_summary(self, document_title: str) -> Dict[str, any]:
        """Get summary information about a document."""
        doc_chunks = [chunk for chunk in self.chunks if chunk.document_title == document_title]

        if not doc_chunks:
            return {"error": f"Document '{document_title}' not found"}

        total_text_length = sum(len(chunk.text) for chunk in doc_chunks)

        return {
            "document_title": document_title,
            "chunk_count": len(doc_chunks),
            "total_text_length": total_text_length,
            "chunk_ids": [chunk.chunk_id for chunk in doc_chunks]
        }

    def list_documents(self) -> List[str]:
        """Get a list of all document titles."""
        return list(set(chunk.document_title for chunk in self.chunks))

    def get_retriever_stats(self) -> Dict[str, any]:
        """Get statistics about the retriever."""
        index_stats = self.faiss_index.get_stats() if self.faiss_index else {}

        return {
            "total_chunks": len(self.chunks),
            "unique_documents": len(self.list_documents()),
            "index_stats": index_stats,
            "embedding_model": self.embedding_generator.get_model_info()
        }


class ContextBuilder:
    """Builds context from retrieval results for LLM prompts."""

    @staticmethod
    def build_context(results: List[RetrievalResult],
                     max_context_length: int = 4000,
                     include_metadata: bool = True) -> str:
        """Build a context string from retrieval results."""
        context_parts = []

        for result in results:
            chunk_text = result.chunk.text.strip()

            if include_metadata:
                metadata_str = f"[Document: {result.chunk.document_title}, Score: {result.similarity_score:.3f}]"
                chunk_content = f"{metadata_str}\n{chunk_text}"
            else:
                chunk_content = chunk_text

            context_parts.append(chunk_content)

            # Check if we've exceeded max length
            current_context = "\n\n".join(context_parts)
            if len(current_context) > max_context_length:
                # Remove the last added part and break
                context_parts.pop()
                break

        return "\n\n".join(context_parts)

    @staticmethod
    def build_structured_context(results: List[RetrievalResult]) -> Dict[str, any]:
        """Build a structured context dictionary."""
        context = {
            "total_results": len(results),
            "documents": {},
            "text_chunks": []
        }

        for result in results:
            doc_title = result.chunk.document_title

            if doc_title not in context["documents"]:
                context["documents"][doc_title] = {
                    "chunks": [],
                    "average_score": 0.0
                }

            chunk_info = {
                "chunk_id": result.chunk.chunk_id,
                "text": result.chunk.text,
                "similarity_score": result.similarity_score,
                "rank": result.rank
            }

            context["documents"][doc_title]["chunks"].append(chunk_info)
            context["text_chunks"].append(chunk_info)

        # Calculate average scores
        for doc_title, doc_info in context["documents"].items():
            scores = [chunk["similarity_score"] for chunk in doc_info["chunks"]]
            doc_info["average_score"] = sum(scores) / len(scores)

        return context