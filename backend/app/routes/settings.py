"""
Settings management routes
"""
from fastapi import APIRouter, HTTPException
from ..models.settings import (
    AppSettings,
    GeneralSettings,
    LLMProviderConfig,
    OpenAIConfig,
    VLLMConfig,
    OllamaConfig,
    Neo4jConfig,
    SettingsUpdateRequest,
    SettingsResponse,
    Neo4jConnectionTest,
    Neo4jSyncRequest,
    Neo4jStatusResponse
)
from typing import Dict, Any
import yaml
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

CONFIG_FILE = "app_config.yml"


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file"""
    if not os.path.exists(CONFIG_FILE):
        raise HTTPException(status_code=404, detail="Configuration file not found")
    
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def save_config(config: Dict[str, Any]):
    """Save configuration to YAML file"""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


@router.get("/all")
async def get_all_settings():
    """Get all application settings"""
    try:
        config = load_config()
        
        return {
            "success": True,
            "settings": {
                "general": {
                    "schema_name": config.get("general", {}).get("schema_name"),
                    "max_retry_attempts": config.get("general", {}).get("max_retry_attempts", 3),
                    "enable_cache": config.get("chat", {}).get("enable_cache", False),
                    "schema_cache_ttl": config.get("cache", {}).get("schema_cache_ttl", 3600)
                },
                "llm": config.get("llm", {}),
                "openai": config.get("openai", {}),
                "vllm": config.get("vllm", {}),
                "ollama": config.get("ollama", {}),
                "neo4j": config.get("neo4j", {}),
                "rag": config.get("rag", {})
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")


@router.get("/{section}")
async def get_section_settings(section: str):
    """Get settings for a specific section"""
    try:
        config = load_config()
        
        if section == "general":
            return {
                "success": True,
                "settings": {
                    "schema_name": config.get("general", {}).get("schema_name"),
                    "max_retry_attempts": config.get("general", {}).get("max_retry_attempts", 3),
                    "enable_cache": config.get("chat", {}).get("enable_cache", False),
                    "schema_cache_ttl": config.get("cache", {}).get("schema_cache_ttl", 3600)
                }
            }
        elif section in ["llm", "openai", "vllm", "ollama", "neo4j", "rag"]:
            return {
                "success": True,
                "settings": config.get(section, {})
            }
        else:
            raise HTTPException(status_code=404, detail=f"Section '{section}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")


@router.put("/update")
async def update_settings(request: SettingsUpdateRequest):
    """Update settings for a specific section"""
    try:
        config = load_config()
        section = request.section
        settings = request.settings
        
        # Track if LLM settings were updated
        llm_settings_updated = False
        
        # Update the appropriate section
        if section == "general":
            # Update general settings across multiple config sections
            if "schema_name" in settings:
                if "general" not in config:
                    config["general"] = {}
                config["general"]["schema_name"] = settings["schema_name"]
            
            if "max_retry_attempts" in settings:
                if "general" not in config:
                    config["general"] = {}
                config["general"]["max_retry_attempts"] = settings["max_retry_attempts"]
            
            if "enable_cache" in settings:
                if "chat" not in config:
                    config["chat"] = {}
                config["chat"]["enable_cache"] = settings["enable_cache"]
            
            if "schema_cache_ttl" in settings:
                if "cache" not in config:
                    config["cache"] = {}
                config["cache"]["schema_cache_ttl"] = settings["schema_cache_ttl"]
            
            # Check if LLM provider was changed in general settings
            if "llm_provider" in settings:
                if "llm" not in config:
                    config["llm"] = {}
                config["llm"]["provider"] = settings["llm_provider"]
                llm_settings_updated = True
                
        elif section in ["llm", "openai", "vllm", "ollama", "neo4j", "rag"]:
            # Update LLM provider settings
            if section not in config:
                config[section] = {}
            config[section].update(settings)
            
            # Mark as needing reload if LLM or knowledge graph settings changed
            if section in ["llm", "openai", "vllm", "ollama"]:
                llm_settings_updated = True
            elif section == "neo4j":
                # Neo4j settings changed - will reload SQLAgent after saving config below
                pass
            elif section == "rag":
                # RAG settings changed - will reload RAG service after saving config below
                pass
        else:
            raise HTTPException(status_code=400, detail=f"Unknown section: {section}")
        
        # Save updated configuration
        save_config(config)
        
        # 🔄 Reload RAG service if RAG settings were changed
        if section == "rag":
            try:
                from ..services.rag_service import reload_rag_service
                updated_config = load_config()
                reload_rag_service(updated_config)
                logger.info(f"✅ RAG service reloaded - RAG is now {'ENABLED' if settings.get('enabled', False) else 'DISABLED'}")
            except Exception as e:
                logger.error(f"Failed to reload RAG service: {e}", exc_info=True)
        
        # 🔄 Reload SQLAgent if Neo4j settings were changed
        if section == "neo4j":
            try:
                from . import api
                if api.sql_agent:
                    updated_config = load_config()
                    api.sql_agent.reload_config(updated_config)
                    logger.info(f"✅ SQLAgent reloaded - Neo4j is now {'ENABLED' if settings.get('enabled', False) else 'DISABLED'}")
                else:
                    logger.warning("SQLAgent not initialized, skipping reload")
                
                # If Neo4j was just enabled, initialize the service
                if settings.get('enabled', False):
                    try:
                        from ..services.knowledge_graph import get_knowledge_graph_service
                        kg_service = get_knowledge_graph_service(updated_config)
                        logger.info("Neo4j knowledge graph service initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize Neo4j service: {e}")
            except Exception as e:
                logger.error(f"Failed to reload services for Neo4j settings: {e}", exc_info=True)
        
        # Reload LLM service if LLM settings were updated
        if llm_settings_updated:
            try:
                from . import api
                
                # Reload configuration and reinitialize LLM service
                updated_config = load_config()
                
                # Use the reload_config method instead of creating new instances
                if api.llm_service:
                    api.llm_service.reload_config(updated_config)
                    logger.info(f"LLM service reloaded with provider: {updated_config['llm']['provider']}")
                else:
                    logger.warning("LLM service not initialized, skipping reload")
                    
            except Exception as e:
                logger.error(f"Failed to reload LLM service: {e}", exc_info=True)
                # Continue anyway - settings were saved
        
        return {
            "success": True,
            "message": f"Settings updated successfully for section: {section}",
            "settings": settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.post("/reset/{section}")
async def reset_section_settings(section: str):
    """Reset settings to default for a specific section"""
    defaults = {
        "general": {
            "schema_name": None,
            "max_retry_attempts": 3,
            "enable_cache": False,
            "schema_cache_ttl": 3600
        },
        "llm": {
            "provider": "openai",
            "fallback_to_rules": True,
            "context_strategy": "auto",
            "max_tokens": 4000
        },
        "openai": {
            "api_key": "",
            "model": "gpt-4o-mini-2024-07-18",
            "temperature": 1.0,
            "max_tokens": 16000,
            "top_p": 1.0
        },
        "vllm": {
            "api_url": "http://localhost:8000/v1/chat/completions",
            "model": "/models",
            "max_tokens": 2048,
            "temperature": 0.7,
            "top_p": 1.0
        },
        "ollama": {
            "api_url": "http://localhost:11434/api/chat",
            "model": "mistral:latest",
            "max_tokens": 2048,
            "temperature": 0.7,
            "stream": False
        }
    }
    
    if section not in defaults:
        raise HTTPException(status_code=400, detail=f"Unknown section: {section}")
    
    try:
        config = load_config()
        
        if section == "general":
            config["general"] = {"schema_name": None, "max_retry_attempts": 3}
            config["chat"]["enable_cache"] = False
            config["cache"]["schema_cache_ttl"] = 3600
        else:
            config[section] = defaults[section]
        
        save_config(config)
        
        return {
            "success": True,
            "message": f"Settings reset to defaults for section: {section}",
            "settings": defaults[section]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")


# ===== Neo4j Knowledge Graph Endpoints =====

@router.post("/neo4j/test")
async def test_neo4j_connection(test_config: Neo4jConnectionTest):
    """Test Neo4j connection with provided credentials - async with timeout"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def _test_connection():
        """Run test in thread pool"""
        try:
            from ..services.knowledge_graph import KnowledgeGraphService
            
            # Create temporary config for testing
            temp_config = {
                'neo4j': {
                    'enabled': True,
                    'uri': test_config.uri,
                    'username': test_config.username,
                    'password': test_config.password,
                    'database': test_config.database
                }
            }
            
            # Create temporary service instance
            kg_service = KnowledgeGraphService(temp_config)
            result = kg_service.test_connection(timeout=5.0)  # 5 second timeout
            kg_service.close()
            
            return {
                "success": result['status'] == 'connected',
                "message": result.get('message', ''),
                "details": result
            }
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
    
    try:
        # Run in thread pool with overall timeout of 10 seconds
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, _test_connection),
                timeout=10.0
            )
        return result
        
    except asyncio.TimeoutError:
        logger.error("Neo4j connection test timed out")
        return {
            "success": False,
            "message": "Connection test timed out after 10 seconds"
        }
    except Exception as e:
        logger.error(f"Neo4j connection test error: {e}")
        return {
            "success": False,
            "message": f"Test failed: {str(e)}"
        }


@router.post("/neo4j/sync")
async def sync_schema_to_neo4j(sync_request: Neo4jSyncRequest):
    """Sync current database schema to Neo4j knowledge graph - async with timeout"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def _sync_schema():
        """Run sync in thread pool"""
        try:
            from ..services.knowledge_graph import KnowledgeGraphService
            from ..services.database import db_service
            
            logger.info("🔄 Starting Neo4j schema sync...")
            
            # Load LATEST runtime configuration (updated via UI)
            config = load_config()
            
            # Create a fresh KG service with the LATEST config (runtime IP)
            kg_service = KnowledgeGraphService(config)
            
            logger.info(f"KG Service - Enabled: {kg_service.enabled}, Driver: {kg_service.driver is not None}")
            logger.info(f"Using Neo4j URI: {config.get('neo4j', {}).get('uri', 'not set')}")
            
            if not kg_service.enabled:
                logger.error("Neo4j is not enabled in configuration")
                return {
                    "success": False,
                    "message": "Neo4j knowledge graph is not enabled. Please enable it in settings first."
                }
            
            if not kg_service.driver:
                logger.error("Neo4j driver not initialized - connection failed")
                return {
                    "success": False,
                    "message": "Neo4j driver not initialized. Please test connection first to ensure Neo4j is reachable."
                }
            
            # Check if database is connected
            if not db_service.connection_params:
                logger.error("No active database connection")
                return {
                    "success": False,
                    "message": "No active database connection. Please connect to a database first."
                }
            
            logger.info(f"Database connected: {db_service.connection_params.get('database')}")
            
            # Get schema snapshot from database service
            try:
                logger.info("Fetching database schema snapshot...")
                schema_snapshot = db_service.get_database_snapshot()
                logger.info(f"Schema snapshot retrieved: {len(schema_snapshot.get('tables', []))} tables")
            except Exception as e:
                logger.error(f"Failed to get database snapshot: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "message": f"Failed to get database schema: {str(e)}"
                }
            
            # Clear existing graph if requested
            if sync_request.clear_existing:
                try:
                    logger.info("Clearing existing knowledge graph...")
                    kg_service.clear_graph()
                    logger.info("✅ Cleared existing knowledge graph")
                except Exception as e:
                    logger.error(f"Failed to clear graph: {e}")
                    return {
                        "success": False,
                        "message": f"Failed to clear graph: {str(e)}"
                    }
            
            # Build graph from schema
            try:
                logger.info("Building knowledge graph from schema...")
                kg_service.build_from_schema(schema_snapshot)
                logger.info("✅ Knowledge graph built successfully")
            except Exception as e:
                logger.error(f"Failed to build graph: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "message": f"Failed to build knowledge graph: {str(e)}"
                }
            
            # Get statistics
            try:
                logger.info("Fetching graph statistics...")
                stats = kg_service.get_graph_statistics()
                logger.info(f"✅ Graph statistics: {stats}")
            except Exception as e:
                logger.error(f"Failed to get statistics: {e}")
                stats = {'error': str(e)}
            
            # Close the connection
            kg_service.close()
            
            return {
                "success": True,
                "message": "Schema successfully synced to Neo4j knowledge graph",
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Neo4j sync error: {e}")
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}"
            }
    
    try:
        # Run in thread pool with 60 second timeout
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, _sync_schema),
                timeout=60.0
            )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except asyncio.TimeoutError:
        logger.error("Neo4j sync timed out after 60 seconds")
        raise HTTPException(
            status_code=504,
            detail="Schema sync timed out after 60 seconds"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync schema to Neo4j: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync schema: {str(e)}"
        )


@router.get("/neo4j/status")
async def get_neo4j_status():
    """Get Neo4j knowledge graph status and statistics"""
    try:
        from ..services.knowledge_graph import KnowledgeGraphService
        
        # Load LATEST runtime configuration
        config = load_config()
        kg_service = KnowledgeGraphService(config)
        
        if not kg_service.enabled:
            return {
                "enabled": False,
                "connected": False,
                "message": "Neo4j knowledge graph is disabled",
                "statistics": None
            }
        
        # Test connection
        connection_test = kg_service.test_connection()
        is_connected = connection_test['status'] == 'connected'
        
        # Get statistics if connected
        stats = None
        if is_connected:
            try:
                stats = kg_service.get_graph_statistics()
            except Exception as e:
                logger.warning(f"Failed to get statistics: {e}")
        
        # Close connection
        kg_service.close()
        
        return {
            "enabled": True,
            "connected": is_connected,
            "message": connection_test.get('message', ''),
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get Neo4j status: {e}")
        return {
            "enabled": False,
            "connected": False,
            "message": f"Error getting status: {str(e)}",
            "statistics": None
        }


@router.get("/neo4j/insights/{table_name}")
async def get_table_insights(table_name: str):
    """Get knowledge graph insights for a specific table"""
    try:
        from ..services.knowledge_graph import KnowledgeGraphService
        
        # Load LATEST runtime configuration
        config = load_config()
        kg_service = KnowledgeGraphService(config)
        
        if not kg_service.enabled:
            raise HTTPException(
                status_code=400,
                detail="Neo4j knowledge graph is not enabled"
            )
        
        relationships = kg_service.get_table_relationships(table_name, max_depth=2)
        
        return {
            "success": True,
            "table": table_name,
            "insights": relationships
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get table insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get insights: {str(e)}"
        )

