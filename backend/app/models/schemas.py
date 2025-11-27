"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    VLLM = "vllm"


class DatabaseType(str, Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class DatabaseConnection(BaseModel):
    """Database connection model"""
    database_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL, description="Database type")
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    use_docker: bool = Field(default=False, description="Use Docker container")
    docker_container: Optional[str] = Field(None, description="Docker container name")
    
    # Oracle-specific fields
    sid: Optional[str] = Field(None, description="Oracle SID")
    service_name: Optional[str] = Field(None, description="Oracle Service Name")
    
    # SQLite-specific field
    file_path: Optional[str] = Field(None, description="SQLite database file path")


class ConnectionTestResponse(BaseModel):
    """Connection test response"""
    success: bool
    message: str
    database_info: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = Field(None, description="Session ID for subsequent requests")


class TableSchema(BaseModel):
    """Table schema model"""
    table_name: str
    columns: List[Dict[str, Any]]  # Changed from str to Any to allow None values
    sample_data: Optional[List[Dict[str, Any]]] = None


class DatabaseSnapshot(BaseModel):
    """Database snapshot model"""
    database_name: str
    tables: List[TableSchema]
    total_tables: int
    timestamp: str


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class QueryRequest(BaseModel):
    """Query request model"""
    question: str = Field(..., description="User's natural language question")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[], description="Previous conversation context"
    )
    max_retries: Optional[int] = Field(default=3, description="Maximum retry attempts")
    schema_name: Optional[str] = Field(default=None, description="Database schema name (e.g., 'public', 'nmsclient')")
    session_id: Optional[str] = Field(default=None, description="Session ID from connection")


class QueryResponse(BaseModel):
    """Query response model"""
    question: str
    sql_query: str
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time: float
    explanation: Optional[str] = None
    retry_count: Optional[int] = Field(default=0, description="Number of retries")
    errors_encountered: Optional[List[str]] = Field(default=[], description="Errors during retries")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None


class LLMConfigUpdate(BaseModel):
    """LLM configuration update model"""
    provider: LLMProvider
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    llm_provider: str
    database_connected: bool


class PoolStats(BaseModel):
    """Connection pool statistics"""
    total_pools: int
    pools: List[Dict[str, Any]]


class SessionStats(BaseModel):
    """Session statistics"""
    total_sessions: int
    sessions: List[Dict[str, Any]]
