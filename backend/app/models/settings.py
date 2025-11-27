"""
Settings management models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class LLMProviderConfig(BaseModel):
    """LLM Provider configuration"""
    provider: str = Field("openai", description="Provider name: openai, vllm, ollama")
    fallback_to_rules: bool = Field(True, description="Fallback to rule-based parser")
    context_strategy: str = Field("auto", description="Context strategy")
    max_tokens: int = Field(4000, description="Max tokens for context")


class OpenAIConfig(BaseModel):
    """OpenAI configuration"""
    api_key: str = Field("", description="OpenAI API key")
    model: str = Field("gpt-4o-mini-2024-07-18", description="Model name")
    temperature: float = Field(1.0, ge=0.0, le=2.0)
    max_tokens: int = Field(16000, description="Max tokens")
    top_p: float = Field(1.0, ge=0.0, le=1.0)


class VLLMConfig(BaseModel):
    """vLLM configuration"""
    api_url: str = Field("http://localhost:8000/v1/chat/completions", description="API URL")
    model: str = Field("/models", description="Model path")
    max_tokens: int = Field(2048, description="Max tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)


class OllamaConfig(BaseModel):
    """Ollama configuration"""
    api_url: str = Field("http://localhost:11434/api/chat", description="API URL")
    model: str = Field("mistral:latest", description="Model name")
    max_tokens: int = Field(2048, description="Max tokens")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    stream: bool = Field(False, description="Enable streaming")


class Neo4jConfig(BaseModel):
    """Neo4j Knowledge Graph configuration"""
    enabled: bool = Field(False, description="Enable Neo4j knowledge graph")
    uri: str = Field("bolt://localhost:7687", description="Neo4j connection URI")
    username: str = Field("neo4j", description="Neo4j username")
    password: str = Field("password", description="Neo4j password")
    database: str = Field("neo4j", description="Neo4j database name")
    auto_sync: bool = Field(True, description="Auto-sync schema to graph")
    max_relationship_depth: int = Field(2, ge=1, le=5, description="Max relationship depth")
    include_in_context: bool = Field(True, description="Include graph insights in context")


class GeneralSettings(BaseModel):
    """General application settings"""
    schema_name: Optional[str] = Field(None, description="Default schema name")
    max_retry_attempts: int = Field(3, ge=1, le=10, description="Max retry attempts")
    enable_cache: bool = Field(False, description="Enable caching")
    schema_cache_ttl: int = Field(3600, ge=60, description="Cache TTL in seconds")


class AppSettings(BaseModel):
    """Complete application settings"""
    general: GeneralSettings
    llm: LLMProviderConfig
    openai: OpenAIConfig
    vllm: VLLMConfig
    ollama: OllamaConfig
    neo4j: Neo4jConfig


class SettingsUpdateRequest(BaseModel):
    """Request to update settings"""
    section: str = Field(..., description="Section to update: general, llm, openai, vllm, ollama, neo4j")
    settings: Dict[str, Any] = Field(..., description="Settings to update")


class SettingsResponse(BaseModel):
    """Settings response"""
    success: bool
    message: str
    settings: Optional[Dict[str, Any]] = None


class Neo4jConnectionTest(BaseModel):
    """Neo4j connection test request"""
    uri: str
    username: str
    password: str
    database: str = "neo4j"


class Neo4jSyncRequest(BaseModel):
    """Request to sync database schema to Neo4j"""
    clear_existing: bool = Field(False, description="Clear existing graph before sync")


class Neo4jStatusResponse(BaseModel):
    """Neo4j status response"""
    enabled: bool
    connected: bool
    statistics: Optional[Dict[str, Any]] = None
    message: str

