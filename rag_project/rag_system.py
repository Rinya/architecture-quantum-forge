"""Main RAG system interface."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.retriever import DocumentRetriever, ContextBuilder, RetrievalResult
from utils.data_loader import DataLoader, ChunkData
from utils.prompt_generator import FewShotPromptGenerator, ContextualPromptGenerator
from config import DATA_DIR, MODELS_DIR, CHUNKS_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """Main RAG (Retrieval-Augmented Generation) system."""

    def __init__(self, embedding_model_name: str = None, index_type: str = "flat",
                 use_adaptive_prompting: bool = True):
        """Initialize the RAG system."""
        self.retriever = DocumentRetriever(MODELS_DIR, embedding_model_name)
        self.context_builder = ContextBuilder()
        self.index_type = index_type
        self.is_initialized = False

        # Initialize prompt generators
        if use_adaptive_prompting:
            self.prompt_generator = ContextualPromptGenerator()
        else:
            self.prompt_generator = FewShotPromptGenerator()

        self.use_adaptive_prompting = use_adaptive_prompting

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
               min_similarity: float = 0.5) -> List[RetrievalResult]:
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
            "index_type": self.index_type,
            "prompt_generator": type(self.prompt_generator).__name__,
            "adaptive_prompting": self.use_adaptive_prompting
        }

    def generate_answer(self, query: str, top_k: int = 5,
                       max_context_length: int = 2000,
                       use_fewshot: bool = True) -> str:
        """Generate an answer using Few-shot prompting with retrieved context."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        # Get relevant documents
        results = self.search(query, top_k)

        if not results:
            return "Извините, я не нашел релевантной информации для ответа на ваш вопрос."

        # Build context from results
        context = self.context_builder.build_context(
            results, max_context_length=max_context_length, include_metadata=True
        )

        if use_fewshot and hasattr(self.prompt_generator, 'generate_adaptive_prompt'):
            # Use adaptive prompting if available
            prompt = self.prompt_generator.generate_adaptive_prompt(
                query, context, max_context_length
            )
        elif use_fewshot:
            # Use standard few-shot prompting
            prompt = self.prompt_generator.generate_prompt(
                query, context, include_examples=True, max_context_length=max_context_length
            )
        else:
            # Simple context-based response
            prompt = f"Контекст: {context}\n\nВопрос: {query}\nОтвет:"

        return prompt

    def generate_structured_answer(self, query: str, top_k: int = 5,
                                 max_context_length: int = 2000) -> Dict[str, Any]:
        """Generate a structured answer with metadata and Few-shot prompting."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        # Get relevant documents
        results = self.search(query, top_k)

        if not results:
            return {
                "answer": "Извините, я не нашел релевантной информации для ответа на ваш вопрос.",
                "sources": [],
                "confidence": 0.0,
                "query_type": "unknown"
            }

        # Generate structured prompt
        structured_prompt = self.prompt_generator.generate_structured_prompt(
            query, results, max_context_length
        )

        # Extract source information
        sources = [
            {
                "document": result.chunk.document_title,
                "chunk_id": result.chunk.chunk_id,
                "similarity": float(result.similarity_score),
                "text_preview": result.chunk.text[:150] + "..."
            }
            for result in results
        ]

        # Calculate confidence based on similarity scores
        avg_similarity = sum(r.similarity_score for r in results) / len(results)
        confidence = float(min(avg_similarity * 1.2, 1.0))  # Scale and cap at 1.0

        # Detect query type
        query_type = self.prompt_generator.detect_query_type(query)

        return {
            "answer_prompt": structured_prompt["prompt"],
            "structured_data": structured_prompt,
            "sources": sources,
            "confidence": confidence,
            "query_type": query_type,
            "total_results": len(results)
        }

    def generate_cot_answer(self, query: str, top_k: int = 5,
                           max_context_length: int = 2000) -> str:
        """Generate an answer using Chain-of-Thought prompting with explicit reasoning steps."""
        if not self.is_initialized:
            raise ValueError("RAG system not initialized. Call initialize_from_chunks_file() first.")

        # Get relevant documents
        results = self.search(query, top_k)

        if not results:
            return "Извините, я не нашел релевантной информации для ответа на ваш вопрос."

        # Build context from results
        context = self.context_builder.build_context(
            results, max_context_length=max_context_length, include_metadata=True
        )

        # Use CoT method if available (ContextualPromptGenerator has it)
        if hasattr(self.prompt_generator, 'generate_cot_prompt'):
            prompt = self.prompt_generator.generate_cot_prompt(
                query, context, max_context_length
            )
        else:
            # Fallback to adaptive prompting
            prompt = self.prompt_generator.generate_adaptive_prompt(
                query, context, max_context_length
            )

        return prompt

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

        print(f"\nFound {len(results)} relevant chunks:\n")

        for result in results:
            print(f"[RANK] Rank {result.rank} | Score: {result.similarity_score:.3f}")
            print(f"[DOC] Document: {result.chunk.document_title}")
            print(f"Chunk ID: {result.chunk.chunk_id}")
            print(f"Content: {result.chunk.text[:200]}...")
            print("-" * 80)

    def print_help():
        """Print available commands."""
        print("\nRAG System Commands:")
        print("  search <query>           - Search for relevant documents")
        print("  search_doc <doc> <query> - Search within a specific document")
        print("  context <query>          - Build context for LLM")
        print("  answer <query>           - Generate answer with Few-shot prompting")
        print("  answer_detailed <query>  - Generate detailed answer with metadata")
        print("  answer_cot <query>       - Generate answer with Chain-of-Thought reasoning")
        print("  list_docs               - List all available documents")
        print("  doc_info <doc_title>    - Get info about a document")
        print("  stats                   - Show system statistics")
        print("  help                    - Show this help")
        print("  quit                    - Exit the system")

    # Initialize RAG system
    print("Initializing RAG System...")

    try:
        rag = RAGSystem()
        rag.initialize_from_chunks_file()
        print("RAG system initialized successfully!")
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        return

    print_help()

    # Main interaction loop
    while True:
        try:
            command = input("\nRAG> ").strip()

            if not command:
                continue

            parts = command.split(" ", 2)
            cmd = parts[0].lower()

            if cmd == "quit":
                print("Goodbye!")
                break

            elif cmd == "help":
                print_help()

            elif cmd == "search":
                if len(parts) < 2:
                    print("ERROR: Usage: search <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"[SEARCH] Searching for: {query}")
                results = rag.search(query)
                print_results(results)

            elif cmd == "search_doc":
                if len(parts) < 3:
                    print("ERROR: Usage: search_doc <document_title> <query>")
                    continue

                doc_title = parts[1]
                query = " ".join(parts[2:])
                print(f"[SEARCH] Searching in '{doc_title}' for: {query}")
                results = rag.search_in_document(query, doc_title)
                print_results(results)

            elif cmd == "context":
                if len(parts) < 2:
                    print("ERROR: Usage: context <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"[SEARCH] Building context for: {query}")
                context = rag.build_context(query)
                print(f"\nContext:\n{context}")

            elif cmd == "list_docs":
                docs = rag.list_documents()
                print(f"\n[DOCS] Available documents ({len(docs)}):")
                for doc in docs:
                    print(f"  - {doc}")

            elif cmd == "doc_info":
                if len(parts) < 2:
                    print("ERROR: Usage: doc_info <document_title>")
                    continue

                doc_title = " ".join(parts[1:])
                info = rag.get_document_info(doc_title)
                print(f"\n[DOC] Document Info:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

            elif cmd == "answer":
                if len(parts) < 2:
                    print("ERROR: Usage: answer <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"[BOT] Generating answer with Few-shot prompting for: {query}")
                try:
                    answer_prompt = rag.generate_answer(query)
                    print(f"\n[NOTE] Generated Few-shot Prompt:\n")
                    print("-" * 80)
                    print(answer_prompt)
                    print("-" * 80)
                except Exception as e:
                    print(f"ERROR: Error generating answer: {e}")

            elif cmd == "answer_detailed":
                if len(parts) < 2:
                    print("ERROR: Usage: answer_detailed <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"[BOT] Generating detailed answer for: {query}")
                try:
                    result = rag.generate_structured_answer(query)

                    print(f"\n[STATS] Answer Analysis:")
                    print(f"  Query Type: {result['query_type']}")
                    print(f"  Confidence: {result['confidence']:.3f}")
                    print(f"  Sources Used: {result['total_results']}")

                    print(f"\n[NOTE] Few-shot Prompt:")
                    print("-" * 80)
                    print(result['answer_prompt'])
                    print("-" * 80)

                    print(f"\n[DOCS] Source Documents:")
                    for i, source in enumerate(result['sources'], 1):
                        print(f"  {i}. {source['document']} (similarity: {source['similarity']:.3f})")
                        print(f"     Preview: {source['text_preview']}")

                except Exception as e:
                    print(f"ERROR: Error generating detailed answer: {e}")

            elif cmd == "answer_cot":
                if len(parts) < 2:
                    print("ERROR: Usage: answer_cot <query>")
                    continue

                query = " ".join(parts[1:])
                print(f"[BRAIN] Generating Chain-of-Thought answer for: {query}")
                try:
                    cot_prompt = rag.generate_cot_answer(query)
                    print(f"\n[THINK] Chain-of-Thought Prompt:\n")
                    print("-" * 80)
                    print(cot_prompt)
                    print("-" * 80)
                except Exception as e:
                    print(f"ERROR: Error generating CoT answer: {e}")

            elif cmd == "stats":
                stats = rag.get_system_stats()
                print(f"\n[STATS] System Statistics:")
                print(f"  Status: {stats['status']}")
                print(f"  Prompt Generator: {stats.get('prompt_generator', 'N/A')}")
                print(f"  Adaptive Prompting: {stats.get('adaptive_prompting', 'N/A')}")
                if 'retriever_stats' in stats:
                    rs = stats['retriever_stats']
                    print(f"  Total chunks: {rs['total_chunks']}")
                    print(f"  Unique documents: {rs['unique_documents']}")
                    if 'index_stats' in rs:
                        print(f"  Index type: {rs['index_stats'].get('type', 'N/A')}")
                        print(f"  Vectors in index: {rs['index_stats'].get('total_vectors', 'N/A')}")

            else:
                print(f"ERROR: Unknown command: {cmd}. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: Error: {e}")


if __name__ == "__main__":
    create_simple_rag_interface()