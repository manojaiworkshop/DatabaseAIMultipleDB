"""
RAG Service using Qdrant Vector Database
Stores and retrieves similar past queries to enhance SQL generation
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class RAGService:
    """Service for managing query history RAG with Qdrant"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize RAG service
        
        Args:
            config: Configuration dictionary with rag settings
        """
        self.config = config
        self.rag_config = config.get('rag', {})
        self.enabled = self.rag_config.get('enabled', False)
        self.client = None
        self.embedder = None
        self.collection_name = self.rag_config.get('collection_name', 'query_history')
        self.top_k = self.rag_config.get('top_k', 3)
        self.similarity_threshold = self.rag_config.get('similarity_threshold', 0.7)
        
        if self.enabled:
            self._connect()
    
    def _connect(self):
        """Establish connection to Qdrant and initialize embedder"""
        try:
            qdrant_url = self.rag_config.get('qdrant_url', 'http://localhost:6333')
            embedding_model = self.rag_config.get('embedding_model', 'all-MiniLM-L6-v2')
            
            # Initialize Qdrant client
            self.client = QdrantClient(url=qdrant_url)
            logger.info(f"Successfully connected to Qdrant at {qdrant_url}")
            
            # Initialize sentence transformer for embeddings
            self.embedder = SentenceTransformer(embedding_model)
            logger.info(f"Loaded embedding model: {embedding_model}")
            
            # Create collection if it doesn't exist
            self._ensure_collection_exists()
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.enabled = False
            self.client = None
            self.embedder = None
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_exists = any(col.name == self.collection_name for col in collections)
            
            if not collection_exists:
                # Get embedding dimension from model
                vector_size = self.embedder.get_sentence_embedding_dimension()
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    def close(self):
        """Close Qdrant connection"""
        if self.client:
            self.client.close()
            logger.info("Qdrant connection closed")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Qdrant connection
        
        Returns:
            Dictionary with connection status and info
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "RAG is disabled in configuration"
            }
        
        try:
            collections = self.client.get_collections()
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "status": "connected",
                "message": "Successfully connected to Qdrant",
                "collection_name": self.collection_name,
                "vector_count": collection_info.points_count,
                "embedding_model": self.rag_config.get('embedding_model')
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }
    
    def add_query(self, user_query: str, sql_query: str, 
                  database_type: str = "postgresql",
                  schema_name: Optional[str] = None,
                  success: bool = True,
                  metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a query to the RAG database
        
        Args:
            user_query: Natural language query
            sql_query: Generated SQL query
            database_type: Type of database (postgresql, oracle, etc.)
            schema_name: Schema name if applicable
            success: Whether the query executed successfully
            metadata: Additional metadata
            
        Returns:
            Boolean indicating success
        """
        if not self.enabled or not self.client:
            logger.warning("RAG is not enabled, skipping query storage")
            return False
        
        try:
            # Generate embedding for user query
            embedding = self.embedder.encode(user_query).tolist()
            
            # Create payload
            payload = {
                "user_query": user_query,
                "sql_query": sql_query,
                "database_type": database_type,
                "schema_name": schema_name,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Generate unique ID
            point_id = str(uuid.uuid4())
            
            # Insert into Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"Added query to RAG: {user_query[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add query to RAG: {e}")
            return False
    
    def search_similar_queries(self, user_query: str,
                               database_type: Optional[str] = None,
                               schema_name: Optional[str] = None,
                               only_successful: bool = True) -> List[Dict[str, Any]]:
        """
        Search for similar past queries
        
        Args:
            user_query: User's natural language query
            database_type: Filter by database type
            schema_name: Filter by schema name
            only_successful: Only return successful queries
            
        Returns:
            List of similar queries with metadata
        """
        if not self.enabled or not self.client:
            logger.warning("RAG is not enabled, returning empty results")
            return []
        
        try:
            # Generate embedding for search query
            query_embedding = self.embedder.encode(user_query).tolist()
            
            # Build filter conditions
            must_conditions = []
            if only_successful:
                must_conditions.append(
                    FieldCondition(key="success", match=MatchValue(value=True))
                )
            if database_type:
                must_conditions.append(
                    FieldCondition(key="database_type", match=MatchValue(value=database_type))
                )
            if schema_name:
                must_conditions.append(
                    FieldCondition(key="schema_name", match=MatchValue(value=schema_name))
                )
            
            query_filter = Filter(must=must_conditions) if must_conditions else None
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=self.top_k,
                score_threshold=self.similarity_threshold
            )
            
            # Format results
            similar_queries = []
            for result in search_results:
                similar_queries.append({
                    "user_query": result.payload.get("user_query"),
                    "sql_query": result.payload.get("sql_query"),
                    "database_type": result.payload.get("database_type"),
                    "schema_name": result.payload.get("schema_name"),
                    "similarity_score": result.score,
                    "timestamp": result.payload.get("timestamp")
                })
            
            logger.info(f"Found {len(similar_queries)} similar queries for: {user_query[:50]}...")
            return similar_queries
            
        except Exception as e:
            logger.error(f"Failed to search similar queries: {e}")
            return []
    
    def get_rag_context(self, user_query: str,
                        database_type: Optional[str] = None,
                        schema_name: Optional[str] = None) -> str:
        """
        Get formatted RAG context for LLM prompt
        
        Args:
            user_query: User's natural language query
            database_type: Database type for filtering
            schema_name: Schema name for filtering
            
        Returns:
            Formatted string with similar queries
        """
        if not self.enabled:
            return ""
        
        similar_queries = self.search_similar_queries(
            user_query=user_query,
            database_type=database_type,
            schema_name=schema_name
        )
        
        if not similar_queries:
            return ""
        
        # Format as context
        context = "\n\n📚 SIMILAR PAST QUERIES (for reference):\n"
        for i, query in enumerate(similar_queries, 1):
            context += f"\nExample {i} (similarity: {query['similarity_score']:.2f}):\n"
            context += f"  Question: {query['user_query']}\n"
            context += f"  SQL: {query['sql_query']}\n"
        
        context += "\nUse these examples as inspiration, but generate SQL specific to the current question.\n"
        
        return context
    
    def bulk_import_csv(self, csv_file_path: str) -> Tuple[int, int, List[str]]:
        """
        Import queries from CSV file
        
        CSV Format: user_query, sql_query, database_type, schema_name, success
        
        Args:
            csv_file_path: Path to CSV file
            
        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        if not self.enabled or not self.client:
            return 0, 0, ["RAG is not enabled"]
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file_path)
            
            # Validate required columns
            required_columns = ['user_query', 'sql_query']
            if not all(col in df.columns for col in required_columns):
                return 0, 0, [f"CSV must contain columns: {required_columns}"]
            
            success_count = 0
            error_count = 0
            error_messages = []
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    self.add_query(
                        user_query=str(row['user_query']),
                        sql_query=str(row['sql_query']),
                        database_type=str(row.get('database_type', 'postgresql')),
                        schema_name=str(row.get('schema_name', None)) if pd.notna(row.get('schema_name')) else None,
                        success=bool(row.get('success', True)),
                        metadata={
                            'imported_from_csv': True,
                            'csv_row': idx
                        }
                    )
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Row {idx}: {str(e)}")
            
            logger.info(f"Bulk import complete: {success_count} success, {error_count} errors")
            return success_count, error_count, error_messages
            
        except Exception as e:
            logger.error(f"Failed to import CSV: {e}")
            return 0, 0, [str(e)]
    
    def bulk_import_data(self, queries: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """
        Import multiple queries from data
        
        Args:
            queries: List of query dictionaries with keys: user_query, sql_query, etc.
            
        Returns:
            Tuple of (success_count, error_count, error_messages)
        """
        if not self.enabled or not self.client:
            return 0, 0, ["RAG is not enabled"]
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for idx, query in enumerate(queries):
            try:
                if 'user_query' not in query or 'sql_query' not in query:
                    error_count += 1
                    error_messages.append(f"Query {idx}: Missing required fields")
                    continue
                
                self.add_query(
                    user_query=query['user_query'],
                    sql_query=query['sql_query'],
                    database_type=query.get('database_type', 'postgresql'),
                    schema_name=query.get('schema_name'),
                    success=query.get('success', True),
                    metadata=query.get('metadata', {})
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                error_messages.append(f"Query {idx}: {str(e)}")
        
        logger.info(f"Bulk import complete: {success_count} success, {error_count} errors")
        return success_count, error_count, error_messages
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG statistics"""
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "enabled": True,
                "collection_name": self.collection_name,
                "total_queries": collection_info.points_count,
                "embedding_model": self.rag_config.get('embedding_model'),
                "top_k": self.top_k,
                "similarity_threshold": self.similarity_threshold
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"enabled": True, "error": str(e)}
    
    def clear_all_queries(self) -> bool:
        """Clear all queries from RAG database"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection_exists()
            logger.info("Cleared all queries from RAG database")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queries: {e}")
            return False
    
    def reload_config(self, new_config: Dict[str, Any]):
        """
        Reload configuration dynamically
        
        Args:
            new_config: New configuration dictionary
        """
        logger.info("🔄 Reloading RAG configuration...")
        self.config = new_config
        self.rag_config = new_config.get('rag', {})
        old_enabled = self.enabled
        self.enabled = self.rag_config.get('enabled', False)
        
        if self.enabled and not old_enabled:
            # RAG was disabled, now enabled
            self._connect()
            logger.info("✅ RAG ENABLED after reload")
        elif not self.enabled and old_enabled:
            # RAG was enabled, now disabled
            self.close()
            self.client = None
            self.embedder = None
            logger.info("⚠️  RAG DISABLED after reload")
        elif self.enabled:
            # RAG was enabled and still enabled, reconnect
            self.close()
            self._connect()
            logger.info("✅ RAG reconnected after reload")
        
        logger.info("🔄 RAG configuration reload complete")


# Global RAG service instance
_rag_service = None


def get_rag_service(config: Dict[str, Any]) -> Optional[RAGService]:
    """Get or create RAG service instance"""
    global _rag_service
    
    if _rag_service is None:
        try:
            _rag_service = RAGService(config)
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            _rag_service = None
    
    return _rag_service


def reload_rag_service(config: Dict[str, Any]):
    """Reload RAG service with new configuration"""
    global _rag_service
    
    if _rag_service:
        _rag_service.reload_config(config)
    else:
        _rag_service = get_rag_service(config)
