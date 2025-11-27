"""
API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from ..models.schemas import (
    DatabaseConnection, ConnectionTestResponse, QueryRequest, 
    QueryResponse, ErrorResponse, LLMConfigUpdate, HealthResponse,
    DatabaseSnapshot
)
from ..services.database import db_service
from ..services.llm import LLMService
from ..services.sql_agent import SQLAgent
from ..middleware.license import require_valid_license

logger = logging.getLogger(__name__)

router = APIRouter()

# Global LLM service and SQL agent instances
llm_service = None
sql_agent = None

def get_llm_service():
    """Get LLM service instance"""
    global llm_service
    if llm_service is None:
        raise HTTPException(status_code=500, detail="LLM service not initialized")
    return llm_service


def get_sql_agent():
    """Get SQL agent instance"""
    global sql_agent
    if sql_agent is None:
        raise HTTPException(status_code=500, detail="SQL agent not initialized")
    return sql_agent


@router.post("/database/connect", response_model=ConnectionTestResponse)
async def connect_database(connection: DatabaseConnection):
    """
    Connect to database and test connection
    Returns connection info AND full database schema
    Supports PostgreSQL, Oracle, MySQL, SQLite
    """
    try:
        db_service.set_connection(
            database_type=connection.database_type.value,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=connection.password,
            sid=connection.sid,
            service_name=connection.service_name,
            file_path=connection.file_path,
            use_docker=connection.use_docker,
            docker_container=connection.docker_container
        )
        
        success, message, info = db_service.test_connection()
        
        # Also fetch the full schema to send to frontend
        if success:
            try:
                schema_snapshot = db_service.get_database_snapshot()
                # Add schema to the database_info
                if info:
                    info['schema'] = {
                        'database_name': schema_snapshot['database_name'],
                        'tables': schema_snapshot['tables'],
                        'views': schema_snapshot.get('views', []),
                        'total_tables': schema_snapshot['total_tables'],
                        'total_views': schema_snapshot.get('total_views', 0)
                    }
                    info['database_type'] = connection.database_type.value
            except Exception as e:
                logger.warning(f"Could not fetch schema: {e}")
                # Don't fail the connection if schema fetch fails
        
        return ConnectionTestResponse(
            success=success,
            message=message,
            database_info=info
        )
        
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/database/snapshot", response_model=DatabaseSnapshot)
async def get_database_snapshot():
    """
    Get database schema snapshot
    """
    try:
        snapshot = db_service.get_database_snapshot()
        return snapshot
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Database not connected")
    except Exception as e:
        logger.error(f"Failed to get snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/schemas")
async def get_all_schemas():
    """
    Get list of all schemas in the database
    """
    try:
        schemas = db_service.get_all_schemas()
        return {
            "success": True,
            "schemas": schemas,
            "total": len(schemas)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Database not connected")
    except Exception as e:
        logger.error(f"Failed to get schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/schemas/{schema_name}/snapshot")
async def get_schema_snapshot(schema_name: str):
    """
    Get snapshot for a specific schema
    """
    try:
        snapshot = db_service.get_schema_snapshot(schema_name)
        return {
            "success": True,
            "snapshot": snapshot
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Database not connected")
    except Exception as e:
        logger.error(f"Failed to get schema snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_database(
    request: QueryRequest, 
    agent: SQLAgent = Depends(get_sql_agent),
    license_info: dict = Depends(require_valid_license)
):
    """
    Process natural language query and return results using SQL Agent with retry logic
    Requires valid license - runs asynchronously with timeout
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def _process_query():
        """Synchronous query processing in thread pool"""
        try:
            logger.info(f"Processing query with agent: {request.question}")
            logger.info(f"Max retries: {request.max_retries}, Schema: {request.schema_name}")
            logger.info(f"License type: {license_info.get('license_type', 'unknown')}")
            
            # Get full schema snapshot for knowledge graph (if enabled)
            schema_snapshot = None
            try:
                schema_snapshot = db_service.get_database_snapshot()
            except Exception as e:
                logger.warning(f"Failed to get schema snapshot for knowledge graph: {e}")
            
            # Get optimized schema context - only relevant tables
            schema_context = db_service.get_relevant_tables_context(request.question, max_tables=15)
            
            # Add schema name hint to context if provided
            if request.schema_name:
                schema_context = f"Schema: {request.schema_name}\nNote: Prefix all table names with '{request.schema_name}.' (e.g., {request.schema_name}.table_name)\n\n" + schema_context
            
            # Run the SQL agent with schema snapshot for knowledge graph
            result = agent.run(
                question=request.question,
                schema_context=schema_context,
                max_retries=request.max_retries or 3,
                schema_name=request.schema_name,
                schema_snapshot=schema_snapshot
            )
            return result
        except Exception as e:
            logger.error(f"Error in query processing thread: {e}")
            raise
    
    try:
        # Run in thread pool with timeout (5 minutes max)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, _process_query),
                timeout=300.0  # 5 minutes timeout
            )
        
        if not result['success']:
            # Agent failed after all retries
            error_msg = "Failed to generate valid SQL after all retries"
            if result['errors_encountered']:
                error_msg += f"\nLast error: {result['errors_encountered'][-1]}"
            
            logger.error(error_msg)
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": error_msg,
                    "retry_count": result['retry_count'],
                    "errors": result['errors_encountered'],
                    "sql_query": result['sql_query']
                }
            )
        
        return QueryResponse(
            question=request.question,
            sql_query=result['sql_query'],
            results=result['results'],
            columns=result['columns'],
            row_count=len(result['results']),
            execution_time=result['execution_time'],
            explanation=result['explanation'],
            retry_count=result['retry_count'],
            errors_encountered=result['errors_encountered']
        )
        
    except asyncio.TimeoutError:
        logger.error("Query processing timed out after 5 minutes")
        raise HTTPException(
            status_code=504,
            detail="Query processing timed out after 5 minutes. Please try a simpler query or reduce the dataset."
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/configure")
async def configure_llm(config: LLMConfigUpdate, llm: LLMService = Depends(get_llm_service)):
    """
    Update LLM configuration
    """
    try:
        llm.set_provider(config.provider.value)
        
        return {
            "success": True,
            "message": f"LLM provider set to {config.provider.value}",
            "current_provider": config.provider.value
        }
        
    except Exception as e:
        logger.error(f"Failed to configure LLM: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/database/disconnect")
async def disconnect_database():
    """
    Disconnect from database and clear session
    """
    try:
        # Clear database connection
        db_service.connection_params = None
        db_service.schema_cache = None
        db_service.cache_timestamp = None
        
        return {
            "success": True,
            "message": "Database disconnected successfully"
        }
    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check(llm: LLMService = Depends(get_llm_service)):
    """
    Health check endpoint
    """
    try:
        # Check database connection
        db_connected = False
        try:
            success, _, _ = db_service.test_connection()
            db_connected = success
        except:
            pass
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            llm_provider=llm.current_provider,
            database_connected=db_connected
        )
    except:
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            llm_provider="unknown",
            database_connected=False
        )
