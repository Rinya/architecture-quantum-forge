"""Configuration settings for the RAG system."""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Files
CHUNKS_FILE = DATA_DIR / "chunks.json"
EMBEDDINGS_FILE = DATA_DIR / "embeddings.json"
FAISS_INDEX_FILE = MODELS_DIR / "faiss_index.bin"
METADATA_FILE = DATA_DIR / "metadata.json"

# Model settings - using local model
LOCAL_MODEL_PATH = MODELS_DIR / "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_MODEL = str(LOCAL_MODEL_PATH)  # Path to local model
EMBEDDING_DIMENSION = 384  # Will be determined from model

# FAISS settings
FAISS_NPROBE = 32  # Number of clusters to probe during search
SIMILARITY_THRESHOLD = 0.7  # Minimum similarity score for retrieval

# Retrieval settings
DEFAULT_TOP_K = 5  # Default number of documents to retrieve
MAX_CHUNK_SIZE = 1000  # Maximum characters per chunk

# API settings (if using OpenAI or other LLM APIs)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-3.5-turbo"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)