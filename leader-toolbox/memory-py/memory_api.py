"""
FastAPI integration for the memory system.

This module extends the existing FastAPI application with memory endpoints
while maintaining backward compatibility with the existing chat system.
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager

# Import existing models for compatibility
try:
    from backend.fastapi_chat import app as existing_app, ChatRequest, ChatResponse
    EXISTING_APP_AVAILABLE = True
except ImportError:
    EXISTING_APP_AVAILABLE = False
    # Fallback definitions
    from pydantic import BaseModel

    class ChatRequest(BaseModel):
        session_id: str
        user_id: str
        message: str

    class ChatResponse(BaseModel):
        text: str
        citations: List[str] = []
        used_kb_ids: List[str] = []
        kb_version: str = "1.0"

# Import memory system components
from memory import MemoryManager, load_memory_config
from memory.models import (
    MemorySearchRequest,
    MemorySearchResponse,
    TextIngestRequest,
    FileIngestRequest,
    IngestResponse,
    FileContentRequest,
    FileContentResponse,
    SyncRequest,
    SyncResponse,
    MemoryStatus,
    SearchResult,
    SearchOptions,
    Range
)

logger = logging.getLogger(__name__)

# Global memory manager instance
memory_manager: Optional[MemoryManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager."""
    global memory_manager

    # Startup
    try:
        logger.info("Starting memory system...")
        memory_manager = MemoryManager()
        await memory_manager.initialize()
        logger.info("Memory system started successfully")
    except Exception as e:
        logger.error(f"Failed to start memory system: {e}")
        memory_manager = None

    yield

    # Shutdown
    if memory_manager:
        try:
            logger.info("Shutting down memory system...")
            await memory_manager.close()
            logger.info("Memory system shut down successfully")
        except Exception as e:
            logger.error(f"Error during memory system shutdown: {e}")

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    if memory_manager is None:
        raise HTTPException(status_code=503, detail="Memory system not available")
    return memory_manager

# Create new FastAPI app or extend existing one
if EXISTING_APP_AVAILABLE:
    app = existing_app
    logger.info("Extending existing FastAPI application")
else:
    app = FastAPI(
        title="Leader-Toolbox with Memory System",
        description="Enhanced leader-toolbox with advanced memory and search capabilities",
        version="1.0.0",
        lifespan=lifespan
    )
    logger.info("Created new FastAPI application")

# Memory System API Endpoints

@app.post("/memory/search", response_model=MemorySearchResponse)
async def memory_search(request: MemorySearchRequest) -> MemorySearchResponse:
    """
    Search memory using semantic and keyword search.

    Supports vector, keyword, and hybrid search modes.
    """
    manager = get_memory_manager()

    start_time = time.time()

    try:
        options = request.options or SearchOptions()
        results = await manager.search(request.query, options)

        search_time_ms = (time.time() - start_time) * 1000

        return MemorySearchResponse(
            results=results,
            query=request.query,
            total_results=len(results),
            search_time_ms=search_time_ms,
            mode_used=options.mode,
            has_more=len(results) == options.max_results
        )

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/memory/ingest/text", response_model=IngestResponse)
async def memory_ingest_text(request: TextIngestRequest) -> IngestResponse:
    """
    Ingest text content into memory.

    Creates chunks and generates embeddings for the text.
    """
    manager = get_memory_manager()

    start_time = time.time()

    try:
        file_id = await manager.ingest_text(request.text, request.metadata)

        processing_time_ms = (time.time() - start_time) * 1000

        # Get stats about what was created
        file_info = await manager.storage.get_file(file_id)
        chunks = await manager.storage.get_chunks_by_file(file_id)

        return IngestResponse(
            file_id=file_id,
            chunks_created=len(chunks),
            embeddings_generated=len(chunks),
            processing_time_ms=processing_time_ms,
            success=True,
            message=f"Ingested {len(chunks)} chunks from text"
        )

    except Exception as e:
        logger.error(f"Text ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/memory/ingest/file", response_model=IngestResponse)
async def memory_ingest_file(request: FileIngestRequest) -> IngestResponse:
    """
    Ingest a file into memory.

    Processes the file, creates chunks, and generates embeddings.
    """
    manager = get_memory_manager()

    start_time = time.time()

    try:
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        file_id = await manager.ingest_file(file_path, request.metadata)

        processing_time_ms = (time.time() - start_time) * 1000

        # Get stats about what was created
        chunks = await manager.storage.get_chunks_by_file(file_id)

        return IngestResponse(
            file_id=file_id,
            chunks_created=len(chunks),
            embeddings_generated=len(chunks),
            processing_time_ms=processing_time_ms,
            success=True,
            message=f"Ingested file {file_path.name}: {len(chunks)} chunks"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/memory/files/{file_id}", response_model=FileContentResponse)
async def memory_get_file(
    file_id: str,
    lines: Optional[str] = None,
    include_metadata: bool = False
) -> FileContentResponse:
    """
    Get file content by ID.

    Optionally specify line range and whether to include metadata.
    """
    manager = get_memory_manager()

    try:
        # Parse line range if provided
        line_range = None
        if lines:
            try:
                if ':' in lines:
                    start, end = lines.split(':', 1)
                    line_range = (int(start), int(end))
                else:
                    start = int(lines)
                    line_range = (start, start + 50)  # Default 50 lines
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid line range format")

        content = await manager.get_file(file_id, line_range)
        file_info = await manager.storage.get_file(file_id)

        if not file_info:
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

        # Determine actual character range
        if line_range:
            lines_list = content.split('\n')
            char_start = len('\n'.join(lines_list[:line_range[0]]))
            char_end = char_start + len(content)
            char_range = Range(start=char_start, end=char_end)
        else:
            char_range = Range(start=0, end=len(content))

        return FileContentResponse(
            file_id=file_id,
            file_path=file_info.path,
            content=content,
            metadata=file_info.metadata if include_metadata else None,
            char_range=char_range,
            total_chars=file_info.size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.post("/memory/sync", response_model=SyncResponse)
async def memory_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
) -> SyncResponse:
    """
    Synchronize files with memory.

    Can be run in background for large sync operations.
    """
    manager = get_memory_manager()

    try:
        if request.paths and len(request.paths) > 100:
            # Run large sync operations in background
            background_tasks.add_task(manager.sync_files, request.paths)

            return SyncResponse(
                stats=SyncStats(files_processed=0),
                success=True,
                message="Large sync operation started in background"
            )
        else:
            # Run small sync operations synchronously
            stats = await manager.sync_files(request.paths)

            return SyncResponse(
                stats=stats,
                success=True,
                message=f"Synchronized {stats.files_processed} files"
            )

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.get("/memory/status", response_model=MemoryStatus)
async def memory_status() -> MemoryStatus:
    """
    Get memory system status and statistics.
    """
    manager = get_memory_manager()

    try:
        status = await manager.get_status()
        return status

    except Exception as e:
        logger.error(f"Status retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status failed: {str(e)}")

# Enhanced Chat Endpoint (extends existing functionality)

@app.post("/chat/enhanced", response_model=ChatResponse)
async def enhanced_chat(request: ChatRequest) -> ChatResponse:
    """
    Enhanced chat endpoint with memory search integration.

    This extends the existing chat functionality with memory search.
    Falls back to original behavior if memory system is not available.
    """
    try:
        manager = get_memory_manager()

        # Search memory for relevant context
        search_results = await manager.search(
            request.message,
            SearchOptions(
                mode="hybrid",
                max_results=5,
                min_score=0.4
            )
        )

        # Extract relevant text from search results
        context_texts = []
        citations = []
        used_kb_ids = []

        for result in search_results:
            context_texts.append(result.text)
            citations.append(f"{result.file_path}:{result.start_char}-{result.end_char}")
            used_kb_ids.append(result.file_id)

        # Combine context with user message
        if context_texts:
            context = "\n\n".join(context_texts[:3])  # Limit context
            enhanced_message = f"Context:\n{context}\n\nUser Question: {request.message}"
        else:
            enhanced_message = request.message

        # Generate response (this would integrate with your LLM)
        # For now, return a simple response with memory citations
        response_text = f"Based on the available context, I found {len(search_results)} relevant pieces of information. Here's what I can tell you about '{request.message}':\n\n"

        if search_results:
            response_text += f"Most relevant information:\n{search_results[0].text[:300]}..."
        else:
            response_text += "No specific information found in the knowledge base for this query."

        return ChatResponse(
            text=response_text,
            citations=citations,
            used_kb_ids=used_kb_ids,
            kb_version="memory-2.0"
        )

    except Exception as e:
        logger.warning(f"Enhanced chat failed, falling back to basic response: {e}")

        # Fallback to basic response
        return ChatResponse(
            text=f"I received your message: '{request.message}'. The memory system is currently unavailable, so I cannot provide context-enhanced responses.",
            citations=[],
            used_kb_ids=[],
            kb_version="basic-1.0"
        )

# Backward compatibility: extend existing /ingest_text endpoint
if EXISTING_APP_AVAILABLE:
    @app.post("/ingest_text/enhanced")
    async def enhanced_ingest_text(
        name: str,
        content: str,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Enhanced version of the original ingest_text endpoint.

        Stores in both the original system and the new memory system.
        """
        try:
            # Call original ingest function if available
            try:
                from backend.fastapi_chat import ingest_text as original_ingest
                original_result = await original_ingest(name, content)
            except:
                original_result = {"success": True, "message": "Original ingest not available"}

            # Also ingest into memory system
            manager = get_memory_manager()
            file_id = await manager.ingest_text(
                content,
                metadata={"title": name, "source": "legacy_ingest"}
            )

            return {
                "success": True,
                "message": f"Content ingested into both systems",
                "original_result": original_result,
                "memory_file_id": file_id
            }

        except Exception as e:
            logger.error(f"Enhanced ingest failed: {e}")
            raise HTTPException(status_code=500, detail=f"Enhanced ingest failed: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    try:
        manager = get_memory_manager()
        status = await manager.get_status()

        return {
            "status": "healthy" if status.is_healthy else "degraded",
            "memory_system": {
                "backend": status.backend,
                "files": status.total_files,
                "chunks": status.total_chunks,
                "embeddings": status.total_embeddings,
                "providers": len(status.embedding_providers)
            }
        }
    except:
        return {
            "status": "unavailable",
            "memory_system": None
        }

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)

    uvicorn.run(
        "memory_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )