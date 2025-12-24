"""Data preparation script for RAG system."""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.data_loader import DataLoader
from utils.embedding_generator import EmbeddingGenerator, EmbeddingUtils
from utils.faiss_index import IndexManager
from config import CHUNKS_FILE, MODELS_DIR, EMBEDDING_MODEL, EMBEDDINGS_FILE
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_embeddings_and_index(chunks_file: Path = CHUNKS_FILE,
                                index_name: str = "default",
                                index_type: str = "flat",
                                batch_size: int = 32,
                                force_regenerate: bool = False):
    """Prepare embeddings and FAISS index from chunks file."""

    logger.info("🚀 Starting data preparation...")

    try:
        # 1. Load chunks
        logger.info(f"📄 Loading chunks from {chunks_file}")
        chunks = DataLoader.load_chunks_from_json(chunks_file)
        logger.info(f"✅ Loaded {len(chunks)} chunks")

        # 2. Check if we need to generate embeddings
        need_embeddings = any(chunk.embedding is None for chunk in chunks)

        if need_embeddings or force_regenerate:
            logger.info("🧠 Generating embeddings...")

            # Initialize embedding generator
            embedder = EmbeddingGenerator(EMBEDDING_MODEL)

            # Extract texts that need embeddings
            if force_regenerate:
                texts_to_embed = [chunk.text for chunk in chunks]
                chunk_indices = list(range(len(chunks)))
            else:
                texts_to_embed = []
                chunk_indices = []
                for i, chunk in enumerate(chunks):
                    if chunk.embedding is None:
                        texts_to_embed.append(chunk.text)
                        chunk_indices.append(i)

            if texts_to_embed:
                # Generate embeddings in batches
                embeddings = embedder.generate_embeddings(texts_to_embed, batch_size)

                # Assign embeddings back to chunks
                for i, embedding in zip(chunk_indices, embeddings):
                    chunks[i].embedding = embedding

                logger.info(f"✅ Generated {len(embeddings)} embeddings")

                # Save updated chunks with embeddings to data directory
                DataLoader.save_chunks_to_json(chunks, EMBEDDINGS_FILE)
                logger.info(f"💾 Saved chunks with embeddings to {EMBEDDINGS_FILE}")

        else:
            logger.info("✅ All chunks already have embeddings")

        # 3. Prepare data for FAISS index
        logger.info("🔧 Preparing FAISS index...")

        # Extract embeddings and metadata
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
        logger.info(f"📊 Prepared {len(embeddings)} embeddings for indexing")

        # 4. Create and save FAISS index
        index_manager = IndexManager(MODELS_DIR)

        logger.info(f"🏗️ Creating {index_type} index...")
        faiss_index = index_manager.create_and_save_index(
            embeddings_array,
            metadata,
            index_name,
            index_type
        )

        # 5. Print statistics
        stats = faiss_index.get_stats()
        logger.info("📈 Index Statistics:")
        logger.info(f"  Type: {stats['type']}")
        logger.info(f"  Dimension: {stats['dimension']}")
        logger.info(f"  Total vectors: {stats['total_vectors']}")
        logger.info(f"  Is trained: {stats['is_trained']}")

        # 6. Test the index with a sample query
        logger.info("🧪 Testing index with sample query...")
        test_query = "узбекский народный эпос"

        # Generate embedding for test query
        embedder = EmbeddingGenerator(EMBEDDING_MODEL)
        query_embedding = embedder.generate_single_embedding(test_query)

        # Search
        similarities, indices, result_metadata = faiss_index.search(query_embedding, k=3)

        logger.info(f"🔍 Test query: '{test_query}'")
        logger.info("🎯 Top results:")
        for i, (sim, meta) in enumerate(zip(similarities, result_metadata)):
            chunk_idx = meta["chunk_index"]
            chunk_text = chunks[chunk_idx].text[:100] + "..."
            logger.info(f"  {i+1}. Score: {sim:.3f} | {chunk_text}")

        logger.info("🎉 Data preparation completed successfully!")

        return {
            "chunks_count": len(chunks),
            "embeddings_count": len(embeddings),
            "index_stats": stats,
            "chunks_file": str(chunks_file),
            "index_name": index_name
        }

    except Exception as e:
        logger.error(f"❌ Error during data preparation: {e}")
        raise


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Prepare data for RAG system")
    parser.add_argument("--chunks-file", type=Path, default=CHUNKS_FILE,
                       help="Path to chunks JSON file")
    parser.add_argument("--index-name", default="default",
                       help="Name for the FAISS index")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat",
                       help="Type of FAISS index to create")
    parser.add_argument("--batch-size", type=int, default=32,
                       help="Batch size for embedding generation")
    parser.add_argument("--force-regenerate", action="store_true",
                       help="Force regeneration of embeddings")

    args = parser.parse_args()

    try:
        result = prepare_embeddings_and_index(
            chunks_file=args.chunks_file,
            index_name=args.index_name,
            index_type=args.index_type,
            batch_size=args.batch_size,
            force_regenerate=args.force_regenerate
        )

        print("\n✅ Preparation Summary:")
        print(f"  Chunks processed: {result['chunks_count']}")
        print(f"  Embeddings created: {result['embeddings_count']}")
        print(f"  Index type: {result['index_stats']['type']}")
        print(f"  Index name: {result['index_name']}")

    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()