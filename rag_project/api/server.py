"""FastAPI server for RAG system."""
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api.models import (
    SearchRequest, DocumentSearchRequest, AnswerRequest, CoTAnswerRequest,
    SearchResponse, AnswerResponse, DetailedAnswerResponse, ContextResponse,
    SystemStats, ErrorResponse, HealthResponse, SearchResult
)
from rag_system import RAGSystem
from config import DATA_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
rag_system = None
startup_time = None
API_VERSION = "1.0.0"


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="RAG System API",
        description="REST API for Retrieval-Augmented Generation system with Chain-of-Thought prompting",
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on your security needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup."""
    global rag_system, startup_time
    startup_time = time.time()

    logger.info("Initializing RAG system...")
    try:
        rag_system = RAGSystem(use_adaptive_prompting=True)
        rag_system.initialize_from_chunks_file()
        logger.info("RAG system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        # Continue without initialized system for health checks


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__, "message": str(exc)}
        ).dict()
    )


def check_system_initialized():
    """Check if RAG system is initialized."""
    if rag_system is None or not rag_system.is_initialized:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG system is not initialized"
        )


def measure_time(func):
    """Decorator to measure execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        return result, processing_time
    return wrapper


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        system_initialized=rag_system is not None and rag_system.is_initialized,
        uptime_seconds=time.time() - startup_time if startup_time else 0
    )


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search for relevant documents."""
    check_system_initialized()

    @measure_time
    def perform_search():
        results = rag_system.search(
            query=request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )

        search_results = [
            SearchResult(
                rank=result.rank,
                similarity_score=result.similarity_score,
                document_title=result.chunk.document_title,
                chunk_id=result.chunk.chunk_id,
                text=result.chunk.text,
                file_path=result.chunk.file_path
            )
            for result in results
        ]

        return search_results

    try:
        results, processing_time = perform_search()

        return SearchResponse(
            query=request.query,
            results=results,
            total_found=len(results),
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@app.post("/search/document", response_model=SearchResponse)
async def search_in_document(request: DocumentSearchRequest):
    """Search within a specific document."""
    check_system_initialized()

    @measure_time
    def perform_search():
        results = rag_system.search_in_document(
            query=request.query,
            document_title=request.document_title,
            top_k=request.top_k
        )

        search_results = [
            SearchResult(
                rank=result.rank,
                similarity_score=result.similarity_score,
                document_title=result.chunk.document_title,
                chunk_id=result.chunk.chunk_id,
                text=result.chunk.text,
                file_path=result.chunk.file_path
            )
            for result in results
        ]

        return search_results

    try:
        results, processing_time = perform_search()

        return SearchResponse(
            query=request.query,
            results=results,
            total_found=len(results),
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document search failed: {str(e)}"
        )


@app.post("/answer", response_model=AnswerResponse)
async def generate_answer(request: AnswerRequest):
    """Generate answer using Few-shot prompting."""
    check_system_initialized()

    @measure_time
    def perform_answer():
        answer_prompt = rag_system.generate_answer(
            query=request.query,
            top_k=request.top_k,
            max_context_length=request.max_context_length,
            use_fewshot=request.use_fewshot
        )

        query_type = rag_system.prompt_generator.detect_query_type(request.query)

        # Calculate confidence based on search results
        search_results = rag_system.search(request.query, request.top_k)
        confidence = 0.0
        if search_results:
            avg_similarity = sum(r.similarity_score for r in search_results) / len(search_results)
            confidence = min(avg_similarity * 1.2, 1.0)

        return answer_prompt, query_type, confidence

    try:
        (answer_prompt, query_type, confidence), processing_time = perform_answer()

        return AnswerResponse(
            query=request.query,
            answer_prompt=answer_prompt,
            query_type=query_type,
            confidence=confidence,
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Answer generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Answer generation failed: {str(e)}"
        )


@app.post("/answer/detailed", response_model=DetailedAnswerResponse)
async def generate_detailed_answer(request: AnswerRequest):
    """Generate detailed answer with metadata."""
    check_system_initialized()

    @measure_time
    def perform_detailed_answer():
        return rag_system.generate_structured_answer(
            query=request.query,
            top_k=request.top_k,
            max_context_length=request.max_context_length
        )

    try:
        result, processing_time = perform_detailed_answer()

        return DetailedAnswerResponse(
            query=request.query,
            answer_prompt=result["answer_prompt"],
            query_type=result["query_type"],
            confidence=result["confidence"],
            sources=result["sources"],
            total_results=result["total_results"],
            structured_data=result["structured_data"],
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Detailed answer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detailed answer generation failed: {str(e)}"
        )


@app.post("/answer/cot", response_model=AnswerResponse)
async def generate_cot_answer(request: CoTAnswerRequest):
    """Generate answer using Chain-of-Thought prompting."""
    check_system_initialized()

    @measure_time
    def perform_cot_answer():
        answer_prompt = rag_system.generate_cot_answer(
            query=request.query,
            top_k=request.top_k,
            max_context_length=request.max_context_length
        )

        query_type = rag_system.prompt_generator.detect_query_type(request.query)

        # Calculate confidence based on search results
        search_results = rag_system.search(request.query, request.top_k)
        confidence = 0.0
        if search_results:
            avg_similarity = sum(r.similarity_score for r in search_results) / len(search_results)
            confidence = min(avg_similarity * 1.2, 1.0)

        return answer_prompt, query_type, confidence

    try:
        (answer_prompt, query_type, confidence), processing_time = perform_cot_answer()

        return AnswerResponse(
            query=request.query,
            answer_prompt=answer_prompt,
            query_type=query_type,
            confidence=confidence,
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"CoT answer error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CoT answer generation failed: {str(e)}"
        )


@app.post("/context", response_model=ContextResponse)
async def build_context(request: SearchRequest):
    """Build context for LLM prompts."""
    check_system_initialized()

    @measure_time
    def perform_context():
        return rag_system.build_context(
            query=request.query,
            top_k=request.top_k,
            max_context_length=4000,
            include_metadata=True
        )

    try:
        context, processing_time = perform_context()

        return ContextResponse(
            query=request.query,
            context=context,
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error(f"Context building error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context building failed: {str(e)}"
        )


@app.get("/documents", response_model=List[str])
async def list_documents():
    """List all available documents."""
    check_system_initialized()

    try:
        return rag_system.list_documents()
    except Exception as e:
        logger.error(f"Document listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics."""
    check_system_initialized()

    try:
        stats = rag_system.get_system_stats()

        return SystemStats(
            status=stats["status"],
            prompt_generator=stats.get("prompt_generator", "Unknown"),
            adaptive_prompting=stats.get("adaptive_prompting", False),
            total_chunks=stats["retriever_stats"]["total_chunks"],
            unique_documents=stats["retriever_stats"]["unique_documents"],
            index_type=stats.get("index_type"),
            total_vectors=stats["retriever_stats"].get("index_stats", {}).get("total_vectors")
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()