"""Main entry point for RAG system with local model."""
import sys
import logging
import json
import numpy as np
from pathlib import Path

from utils.data_loader import ChunkData, DataLoader
from utils.faiss_index import IndexManager
from rag_system import RAGSystem
from config import MODELS_DIR, DATA_DIR, EMBEDDINGS_FILE, CHUNKS_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_existing_embeddings():
    """Load embeddings from the existing embeddings.json file."""
    # Try multiple paths for the embeddings file
    possible_paths = [
        EMBEDDINGS_FILE,  # data/embeddings.json
        Path("embeddings.json"),  # root embeddings.json
        DATA_DIR.parent / "scripts" / "embeddings.json",  # scripts/embeddings.json
    ]

    embeddings_file = None
    for path in possible_paths:
        if path.exists():
            embeddings_file = path
            break

    if embeddings_file is None:
        print("Error: embeddings.json file not found in any of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        return None

    print(f"Loading data from {embeddings_file}")

    try:
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = []

        for item in data:
            # Create chunk from the data (handle both 'content' and 'text' fields)
            text_content = item.get("content") or item.get("text", "")

            chunk = ChunkData(
                text=text_content,
                document_title=item.get("document_title", ""),
                chunk_id=item.get("chunk_id", ""),
                file_path=item.get("file_path"),
                start_position=item.get("start_position"),
                embedding=np.array(item["embedding"], dtype=np.float32)
            )
            chunks.append(chunk)

        print(f"SUCCESS: Loaded {len(chunks)} chunks with embeddings")
        print(f"Embedding dimension: {chunks[0].embedding.shape[0] if chunks else 'Unknown'}")

        return chunks

    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return None


def create_faiss_index_from_chunks(chunks):
    """Create FAISS index from chunks with embeddings."""
    print("Creating FAISS index from existing embeddings...")

    embeddings = []
    metadata = []

    for i, chunk in enumerate(chunks):
        if chunk.embedding is not None:
            embeddings.append(chunk.embedding)
            metadata.append({
                "chunk_id": chunk.chunk_id,
                "document_title": chunk.document_title,
                "chunk_index": i
            })

    if not embeddings:
        raise ValueError("No embeddings found in chunks")

    embeddings_array = np.array(embeddings, dtype=np.float32)

    # Create and save index
    index_manager = IndexManager(MODELS_DIR)
    faiss_index = index_manager.create_and_save_index(
        embeddings_array,
        metadata,
        index_name="main_index",
        index_type="flat"
    )

    print(f"Index created with {len(embeddings)} vectors")
    return faiss_index


def show_document_stats(chunks):
    """Show statistics about the loaded documents."""
    print("\n=== Document Statistics ===")

    # Get unique documents
    documents = {}
    for chunk in chunks:
        doc_title = chunk.document_title
        if doc_title not in documents:
            documents[doc_title] = 0
        documents[doc_title] += 1

    print(f"Total documents: {len(documents)}")
    print(f"Total chunks: {len(chunks)}")
    print()

    print("Top 10 documents by chunk count:")
    sorted_docs = sorted(documents.items(), key=lambda x: x[1], reverse=True)
    for i, (doc_title, count) in enumerate(sorted_docs[:10], 1):
        # Clean document name for display
        clean_title = doc_title.replace('.txt', '') if doc_title.endswith('.txt') else doc_title
        print(f"  {i:2d}. {clean_title}: {count} chunks")


def search_demo(chunks):
    """Demonstrate search functionality using simple text matching."""
    print("\n=== Search Demo (Text-based) ===")

    test_queries = [
        "узбекский эпос",
        "главный герой",
        "богатырь",
        "Алпамыш",
        "народный эпос"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = simple_text_search(chunks, query, top_k=3)

        if results:
            for i, (chunk, score) in enumerate(results, 1):
                print(f"  {i}. Score: {score:.3f}")
                print(f"     Document: {chunk.document_title}")
                print(f"     Content: {chunk.text[:120]}...")
        else:
            print("  No results found")


def simple_text_search(chunks, query, top_k=3):
    """Simple text-based search for demo purposes."""
    results = []
    query_lower = query.lower()

    for chunk in chunks:
        text_lower = chunk.text.lower()

        # Simple scoring based on keyword matching
        score = 0.0
        query_words = query_lower.split()

        for word in query_words:
            if word in text_lower:
                # Give higher score for exact matches
                if f" {word} " in text_lower:
                    score += 1.0 / len(query_words)
                else:
                    score += 0.5 / len(query_words)

        if score > 0:
            results.append((chunk, score))

    # Sort by score and return top_k
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def interactive_search(chunks):
    """Interactive search interface."""
    print("\n=== Interactive Search ===")
    print("Enter search queries (type 'quit' to exit)")
    print("Commands:")
    print("  search <query>  - Search for documents")
    print("  help           - Show this help")
    print("  stats          - Show document statistics")
    print("  quit           - Exit")

    while True:
        try:
            command = input("\nRAG> ").strip()

            if not command:
                continue

            if command.lower() == 'quit':
                print("Goodbye!")
                break

            if command.lower() == 'help':
                print("Commands:")
                print("  search <query>  - Search for documents")
                print("  help           - Show this help")
                print("  stats          - Show document statistics")
                print("  quit           - Exit")
                continue

            if command.lower() == 'stats':
                show_document_stats(chunks)
                continue

            # Handle search command
            if command.lower().startswith('search '):
                query = command[7:].strip()
            else:
                # Treat everything else as a search query
                query = command

            if query:
                results = simple_text_search(chunks, query, top_k=5)

                if results:
                    print(f"\nFound {len(results)} results for '{query}':")
                    for i, (chunk, score) in enumerate(results, 1):
                        print(f"\n{i}. Score: {score:.3f}")
                        print(f"   Document: {chunk.document_title}")
                        print(f"   Chunk ID: {chunk.chunk_id}")
                        print(f"   Content: {chunk.text[:250]}...")
                else:
                    print(f"No results found for '{query}'")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function."""
    print("RAG System with Local Model")
    print("=" * 50)

    # Load existing embeddings
    chunks = load_existing_embeddings()
    if not chunks:
        print("Failed to load embeddings. Exiting.")
        return

    # Show document statistics
    show_document_stats(chunks)

    # Try to create FAISS index
    try:
        faiss_index = create_faiss_index_from_chunks(chunks)
        print("SUCCESS: FAISS index created!")

        # Show index stats
        stats = faiss_index.get_stats()
        print(f"Index Statistics:")
        print(f"  Type: {stats['type']}")
        print(f"  Dimension: {stats['dimension']}")
        print(f"  Total vectors: {stats['total_vectors']}")

    except Exception as e:
        print(f"Warning: Could not create FAISS index: {e}")
        print("Continuing with text-based search...")

    # Run search demo
    search_demo(chunks)

    # Interactive mode
    print("\n" + "=" * 50)
    response = input("Would you like to try interactive search? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        interactive_search(chunks)

    print("\nDemo completed!")
    print("\nNext steps:")
    print("1. Run 'python utils/prepare_data.py' to generate embeddings with local model")
    print("2. Use 'python rag_system.py' for full RAG functionality")


if __name__ == "__main__":
    main()