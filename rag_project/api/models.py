"""API data models for RAG system."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    top_k: int = Field(default=5, description="Number of results to return", ge=1, le=20)
    min_similarity: float = Field(default=0.5, description="Minimum similarity threshold", ge=0.0, le=1.0)


class DocumentSearchRequest(BaseModel):
    """Request model for document-specific search."""
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    document_title: str = Field(..., description="Document title to search within")
    top_k: int = Field(default=5, description="Number of results to return", ge=1, le=20)


class AnswerRequest(BaseModel):
    """Request model for answer generation."""
    query: str = Field(..., description="Question to answer", min_length=1, max_length=1000)
    top_k: int = Field(default=5, description="Number of context documents", ge=1, le=20)
    max_context_length: int = Field(default=2000, description="Maximum context length", ge=500, le=10000)
    use_fewshot: bool = Field(default=True, description="Use few-shot prompting")


class CoTAnswerRequest(BaseModel):
    """Request model for Chain-of-Thought answer generation."""
    query: str = Field(..., description="Question to answer", min_length=1, max_length=1000)
    top_k: int = Field(default=5, description="Number of context documents", ge=1, le=20)
    max_context_length: int = Field(default=2000, description="Maximum context length", ge=500, le=10000)


class SearchResult(BaseModel):
    """Single search result."""
    rank: int = Field(..., description="Result ranking")
    similarity_score: float = Field(..., description="Similarity score")
    document_title: str = Field(..., description="Source document title")
    chunk_id: str = Field(..., description="Chunk identifier")
    text: str = Field(..., description="Text content")
    file_path: Optional[str] = Field(None, description="Source file path")


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class AnswerResponse(BaseModel):
    """Response model for answer generation."""
    query: str = Field(..., description="Original question")
    answer_prompt: str = Field(..., description="Generated prompt for LLM")
    query_type: str = Field(..., description="Detected query type")
    confidence: float = Field(..., description="Confidence score")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class DetailedAnswerResponse(AnswerResponse):
    """Extended response with source information."""
    sources: List[Dict[str, Any]] = Field(..., description="Source documents used")
    total_results: int = Field(..., description="Number of source documents")
    structured_data: Dict[str, Any] = Field(..., description="Additional structured data")


class ContextResponse(BaseModel):
    """Response model for context building."""
    query: str = Field(..., description="Original query")
    context: str = Field(..., description="Built context string")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class DocumentInfo(BaseModel):
    """Document information model."""
    title: str = Field(..., description="Document title")
    chunk_count: int = Field(..., description="Number of chunks")
    total_length: int = Field(..., description="Total character length")


class SystemStats(BaseModel):
    """System statistics model."""
    status: str = Field(..., description="System status")
    prompt_generator: str = Field(..., description="Prompt generator type")
    adaptive_prompting: bool = Field(..., description="Whether adaptive prompting is enabled")
    total_chunks: int = Field(..., description="Total number of chunks")
    unique_documents: int = Field(..., description="Number of unique documents")
    index_type: Optional[str] = Field(None, description="Index type")
    total_vectors: Optional[int] = Field(None, description="Total vectors in index")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    system_initialized: bool = Field(..., description="Whether RAG system is initialized")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")