"""Main RAG system interface."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.retriever import DocumentRetriever, ContextBuilder, RetrievalResult
from utils.data_loader import DataLoader, ChunkData
from config import DATA_DIR, MODELS_DIR, CHUNKS_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """Main RAG (Retrieval-Augmented Generation) system."""

    def __init__(self, embedding_model_name: str = None, index_type: str = "flat"):
        """Initialize the RAG system."""
        self.retriever = DocumentRetriever(MODELS_DIR, embedding_model_name)
        self.context_builder = ContextBuilder()
        self.index_type = index_type
        self.is_initialized = False

    def initialize_from_chunks_file(self, chunks_file: Path = CHUNKS_FILE,
                                   index_name: str = "default",
                                   force_rebuild: bool = False) -> None:
        """Initialize the RAG system from a chunks JSON file."""
        logger.info(f"Initializing RAG system from {chunks_file}")

        # Load chunks
        chunks = DataLoader.load_chunks_from_json(chunks_file)

        # Setup retriever
        self.retriever.setup_from_chunks(
            chunks=chunks,
            index_name=index_name,
            index_type=self.index_type,
            force_rebuild=force_rebuild
        )

        self.is_initialized = True
        logger.info("RAG system initialized successfully")

    def initialize_from_chunks(self, chunks: List[ChunkData],
                              index_name: str = "default",
                              force_rebuild: bool = False) -> None:
        """Initialize the RAG system from a list of chunks."""
        logger.info(f"Initializing RAG system with {len(chunks)} chunks")

        self.retriever.setup_from_chunks(
            chunks=chunks,
            index_name=index_name,
            index_type=self.index_type,
            force_rebuild=force_rebuild
        )

        self.is_initialized = True
        logger.info("RAG system initialized successfully")

    def search(self, query: str, top_k: int = 5,
               min_similarity: float = 0.7) -> List[RetrievalResult]:
        """Search for relevant documents."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        return self.retriever.retrieve(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )

    def search_in_document(self, query: str, document_title: str,
                          top_k: int = 5) -> List[RetrievalResult]:
        """Search for relevant chunks within a specific document."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        return self.retriever.retrieve_by_document(
            query=query,
            document_title=document_title,
            top_k=top_k
        )

    def build_context(self, query: str, top_k: int = 5,
                     max_context_length: int = 4000,
                     include_metadata: bool = True) -> str:
        """Build a context string for LLM prompts."""
        results = self.search(query, top_k)
        return self.context_builder.build_context(
            results=results,
            max_context_length=max_context_length,
            include_metadata=include_metadata
        )

    def build_structured_context(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Build a structured context dictionary."""
        results = self.search(query, top_k)
        return self.context_builder.build_structured_context(results)

    def get_document_info(self, document_title: str) -> Dict[str, Any]:
        """Get information about a specific document."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        return self.retriever.get_document_summary(document_title)

    def list_documents(self) -> List[str]:
        """Get a list of all available documents."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        return self.retriever.list_documents()

    def get_system_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "retriever_stats": self.retriever.get_retriever_stats(),
            "available_documents": self.list_documents(),
            "index_type": self.index_type
        }

    def add_documents(self, new_chunks: List[ChunkData],
                     index_name: str = "default",
                     rebuild_index: bool = True) -> None:
        """Add new documents to the system."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        # Get current chunks
        current_chunks = self.retriever.chunks

        # Add new chunks
        all_chunks = current_chunks + new_chunks

        # Rebuild the system with all chunks
        if rebuild_index:
            self.initialize_from_chunks(all_chunks, index_name, force_rebuild=True)
        else:
            logger.warning("rebuild_index=False: New chunks added but index not rebuilt")


def create_simple_rag_interface():
    """Create a simple command-line interface for the RAG system."""

    def print_results(results: List[RetrievalResult]):
        """Print search results in a nice format."""
        if not results:
            print("No results found.")
            return

        print(f"\n📄 Found {len(results)} relevant chunks:\n")

        for result in results:
            print(f"🏆 Rank {result.rank} | Score: {result.similarity_score:.3f}")
            print(f"📖 Document: {result.chunk.document_title}")
            print(f"🔍 Chunk ID: {result.chunk.chunk_id}")
            print(f"📝 Content: {result.chunk.text[:200]}...")
            print("-" * 80)

    def print_help():
        """Print available commands."""
        print("\n📚 RAG System Commands:")
        print("  search <query>           - Search for relevant documents")
        print("  search_doc <doc> <query> - Search within a specific document")
        print("  context <query>          - Build context for LLM")
        print("  list_docs               - List all available documents")
        print("  doc_info <doc_title>    - Get info about a document")
        print("  stats                   - Show system statistics")
        print("  help                    - Show this help")
        print("  quit                    - Exit the system")

    # Initialize RAG system
    print("🚀 Initializing RAG System...")

    try:
        rag = RAGSystem()
        rag.initialize_from_chunks_file()
        print("✅ RAG system initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        return

    print_help()

    # Main interaction loop
    while True:
        try:
            command = input("\n🤖 RAG> ").strip()

            if not command:
                continue

            parts = command.split(" ", 2)
            cmd = parts[0].lower()

            if cmd == "quit":
                print("👋 Goodbye!")
                break

            elif cmd == "help":
                print_help()

            elif cmd == "search":
                if len(parts) < 2:
                    print("❌ Usage: search <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"🔍 Searching for: {query}")
                results = rag.search(query)
                print_results(results)

            elif cmd == "search_doc":
                if len(parts) < 3:
                    print("❌ Usage: search_doc <document_title> <query>")
                    continue

                doc_title = parts[1]
                query = " ".join(parts[2:])
                print(f"🔍 Searching in '{doc_title}' for: {query}")
                results = rag.search_in_document(query, doc_title)
                print_results(results)

            elif cmd == "context":
                if len(parts) < 2:
                    print("❌ Usage: context <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"🔍 Building context for: {query}")
                context = rag.build_context(query)
                print(f"\n📄 Context:\n{context}")

            elif cmd == "list_docs":
                docs = rag.list_documents()
                print(f"\n📚 Available documents ({len(docs)}):")
                for doc in docs:
                    print(f"  - {doc}")

            elif cmd == "doc_info":
                if len(parts) < 2:
                    print("❌ Usage: doc_info <document_title>")
                    continue

                doc_title = " ".join(parts[1:])
                info = rag.get_document_info(doc_title)
                print(f"\n📖 Document Info:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

            elif cmd == "stats":
                stats = rag.get_system_stats()
                print(f"\n📊 System Statistics:")
                print(f"  Status: {stats['status']}")
                if 'retriever_stats' in stats:
                    rs = stats['retriever_stats']
                    print(f"  Total chunks: {rs['total_chunks']}")
                    print(f"  Unique documents: {rs['unique_documents']}")
                    if 'index_stats' in rs:
                        print(f"  Index type: {rs['index_stats'].get('type', 'N/A')}")
                        print(f"  Vectors in index: {rs['index_stats'].get('total_vectors', 'N/A')}")

            else:
                print(f"❌ Unknown command: {cmd}. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    create_simple_rag_interface()