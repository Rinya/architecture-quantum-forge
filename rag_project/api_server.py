#!/usr/bin/env python3
"""
RAG System API Server

Launch the FastAPI server for the RAG system.
"""
import os
import sys
from pathlib import Path

# Add the current directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

if __name__ == "__main__":
    try:
        from api.server import main
        print("Starting RAG System API Server...")
        print("Swagger docs will be available at: http://localhost:8000/docs")
        print("ReDoc docs will be available at: http://localhost:8000/redoc")
        print("Health check at: http://localhost:8000/health")
        print()
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure to install FastAPI dependencies:")
        print("   pip install fastapi uvicorn pydantic")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)