"""
RAG (Retrieval-Augmented Generation) Routes
Handles query history management and similarity search
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import tempfile
import os

from ..services.rag_service import get_rag_service, reload_rag_service
from ..middleware.license import require_valid_license

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryHistoryItem(BaseModel):
    """Model for adding a single query to history"""
    user_query: str
    sql_query: str
    database_type: Optional[str] = "postgresql"
    schema_name: Optional[str] = None
    success: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None


class BulkQueryImport(BaseModel):
    """Model for bulk importing queries"""
    queries: List[Dict[str, Any]]


class SimilarQueryRequest(BaseModel):
    """Model for searching similar queries"""
    user_query: str
    database_type: Optional[str] = None
    schema_name: Optional[str] = None
    only_successful: Optional[bool] = True


@router.get("/status")
async def get_rag_status():
    """Get RAG service status and statistics"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service:
            return {
                "enabled": False,
                "message": "RAG service not initialized"
            }
        
        connection_status = rag_service.test_connection()
        statistics = rag_service.get_statistics()
        
        return {
            **connection_status,
            **statistics
        }
        
    except Exception as e:
        logger.error(f"Failed to get RAG status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-query")
async def add_query_to_rag(query_item: QueryHistoryItem):
    """Add a single query to RAG database"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service or not rag_service.enabled:
            raise HTTPException(status_code=400, detail="RAG service is not enabled")
        
        success = rag_service.add_query(
            user_query=query_item.user_query,
            sql_query=query_item.sql_query,
            database_type=query_item.database_type,
            schema_name=query_item.schema_name,
            success=query_item.success,
            metadata=query_item.metadata
        )
        
        if success:
            return {
                "success": True,
                "message": "Query added to RAG database"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add query to RAG")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-similar")
async def search_similar_queries(request: SimilarQueryRequest):
    """Search for similar queries in RAG database"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service or not rag_service.enabled:
            return {
                "success": False,
                "message": "RAG service is not enabled",
                "similar_queries": []
            }
        
        similar_queries = rag_service.search_similar_queries(
            user_query=request.user_query,
            database_type=request.database_type,
            schema_name=request.schema_name,
            only_successful=request.only_successful
        )
        
        return {
            "success": True,
            "similar_queries": similar_queries,
            "count": len(similar_queries)
        }
        
    except Exception as e:
        logger.error(f"Failed to search similar queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-import")
async def bulk_import_queries(import_data: BulkQueryImport):
    """Bulk import queries from JSON data"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service or not rag_service.enabled:
            raise HTTPException(status_code=400, detail="RAG service is not enabled")
        
        success_count, error_count, error_messages = rag_service.bulk_import_data(
            queries=import_data.queries
        )
        
        return {
            "success": True,
            "success_count": success_count,
            "error_count": error_count,
            "error_messages": error_messages[:10]  # Limit to first 10 errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-csv")
async def upload_csv_queries(file: UploadFile = File(...)):
    """Upload CSV file with query history"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service or not rag_service.enabled:
            raise HTTPException(status_code=400, detail="RAG service is not enabled")
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Import from CSV
            success_count, error_count, error_messages = rag_service.bulk_import_csv(
                csv_file_path=tmp_file_path
            )
            
            return {
                "success": True,
                "filename": file.filename,
                "success_count": success_count,
                "error_count": error_count,
                "error_messages": error_messages[:10]  # Limit to first 10 errors
            }
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear-all")
async def clear_all_queries():
    """Clear all queries from RAG database"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service or not rag_service.enabled:
            raise HTTPException(status_code=400, detail="RAG service is not enabled")
        
        success = rag_service.clear_all_queries()
        
        if success:
            return {
                "success": True,
                "message": "All queries cleared from RAG database"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear queries")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_rag_statistics():
    """Get RAG database statistics"""
    try:
        from ..main import app
        config = app.state.config if hasattr(app.state, 'config') else {}
        rag_service = get_rag_service(config)
        
        if not rag_service:
            return {
                "enabled": False,
                "message": "RAG service not initialized"
            }
        
        stats = rag_service.get_statistics()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
