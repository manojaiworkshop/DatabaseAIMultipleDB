"""
Ontology management routes
"""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

# Config file path
CONFIG_FILE = "app_config.yml"


def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def save_config(config: Dict[str, Any]):
    """Save configuration to YAML file"""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


@router.get("/status")
async def get_ontology_status():
    """Get ontology system status including database connection state"""
    try:
        from ..services.database import db_service
        
        config = load_config()
        ontology_config = config.get('ontology', {})
        
        # Check database connection
        db_connected = db_service.connection_params is not None
        db_info = None
        if db_connected:
            db_info = {
                'database': db_service.connection_params.get('database'),
                'host': db_service.connection_params.get('host'),
                'port': db_service.connection_params.get('port')
            }
        
        return {
            "success": True,
            "ontology_enabled": ontology_config.get('enabled', False),
            "dynamic_generation_enabled": ontology_config.get('dynamic_generation', {}).get('enabled', False),
            "database_connected": db_connected,
            "database_info": db_info
        }
    except Exception as e:
        logger.error(f"Failed to get ontology status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class OntologySettingsRequest(BaseModel):
    """Request to update ontology settings"""
    enabled: bool
    dynamic_generation: Dict[str, Any]
    content: Optional[str] = None
    format: Optional[str] = 'owl'


class OntologyGenerateRequest(BaseModel):
    """Request to generate dynamic ontology"""
    force_regenerate: bool = False
    export_format: str = 'both'  # 'yml', 'owl', or 'both'


@router.get("/settings")
async def get_ontology_settings():
    """Get current ontology settings"""
    try:
        config = load_config()
        ontology_config = config.get('ontology', {})
        
        # Get stats if available
        stats = None
        try:
            from ..services.dynamic_ontology import get_dynamic_ontology_service
            from ..services.llm_service import get_llm_service
            
            llm_service = get_llm_service(config)
            dynamic_ontology = get_dynamic_ontology_service(llm_service, config)
            
            # Get cached ontology
            cached_ont = None
            for ont in dynamic_ontology.ontology_cache.values():
                cached_ont = ont
                break
            
            if cached_ont:
                stats = {
                    'concepts': cached_ont['metadata'].get('concept_count', 0),
                    'properties': cached_ont['metadata'].get('property_count', 0),
                    'relationships': cached_ont['metadata'].get('relationship_count', 0),
                    'tables': cached_ont['metadata'].get('table_count', 0),
                    'generated_at': cached_ont['metadata'].get('generated_at')
                }
        except Exception as e:
            logger.warning(f"Failed to get ontology stats: {e}")
        
        return {
            "success": True,
            "settings": {
                "enabled": ontology_config.get('enabled', False),
                "dynamic_generation": ontology_config.get('dynamic_generation', {}),
                "content": ontology_config.get('content', ''),
                "format": ontology_config.get('format', 'owl'),
                "stats": stats
            }
        }
    except Exception as e:
        logger.error(f"Failed to get ontology settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_ontology_settings(request: OntologySettingsRequest):
    """Update ontology settings"""
    try:
        config = load_config()
        
        # Update ontology settings
        if 'ontology' not in config:
            config['ontology'] = {}
        
        config['ontology']['enabled'] = request.enabled
        config['ontology']['dynamic_generation'] = request.dynamic_generation
        
        if request.content:
            config['ontology']['content'] = request.content
        
        if request.format:
            config['ontology']['format'] = request.format
        
        # Save config
        save_config(config)
        
        # 🔄 RELOAD SQLAgent with new config
        try:
            from . import api
            if api.sql_agent:
                # Reload config file to ensure we have latest changes
                updated_config = load_config()
                api.sql_agent.reload_config(updated_config)
                logger.info(f"✅ SQLAgent reloaded - Ontology is now {'ENABLED' if request.enabled else 'DISABLED'}")
            else:
                logger.warning("SQLAgent not initialized, skipping reload")
        except Exception as e:
            logger.error(f"Failed to reload SQLAgent: {e}", exc_info=True)
            # Continue anyway - settings were saved
        
        return {
            "success": True,
            "message": "Ontology settings updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update ontology settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_dynamic_ontology(request: OntologyGenerateRequest):
    """Generate dynamic ontology for current database schema"""
    try:
        from . import api  # Import api module to access llm_service
        from ..services.database import db_service
        from ..services.dynamic_ontology import get_dynamic_ontology_service
        
        # Check if database is connected
        if not db_service.connection_params:
            raise HTTPException(
                status_code=400,
                detail="No active database connection. Please connect to a database first."
            )
        
        # Get schema snapshot
        schema_snapshot = db_service.get_database_snapshot()
        
        # DEBUG: Print what database.py returned
        logger.info("="*80)
        logger.info("🔍 DEBUG: SCHEMA SNAPSHOT FROM DATABASE SERVICE")
        logger.info("="*80)
        logger.info(f"Snapshot keys: {list(schema_snapshot.keys())}")
        logger.info(f"Database: {schema_snapshot.get('database_name')}")
        logger.info(f"Total tables: {schema_snapshot.get('total_tables')}")
        logger.info(f"Total views: {schema_snapshot.get('total_views')}")
        logger.info(f"Timestamp: {schema_snapshot.get('timestamp')}")
        
        tables_data = schema_snapshot.get('tables', [])
        logger.info(f"Tables data type: {type(tables_data)}")
        logger.info(f"Tables count: {len(tables_data)}")
        
        if tables_data:
            logger.info("\n📋 First 5 tables in snapshot:")
            for i, table in enumerate(tables_data[:5], 1):
                schema_name = table.get('schema_name', 'public')
                table_name = table.get('table_name', 'unknown')
                full_name = table.get('full_name', f"{schema_name}.{table_name}")
                col_count = len(table.get('columns', []))
                logger.info(f"  {i}. {full_name} ({col_count} columns)")
        else:
            logger.warning("⚠️  NO TABLES IN SNAPSHOT!")
        logger.info("="*80)
        
        # Verify schema has tables
        tables = schema_snapshot.get('tables', [])
        if not tables or len(tables) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"No tables found in database '{db_service.connection_params.get('database', 'unknown')}'. Cannot generate ontology from empty schema."
            )
        
        # Get services - use the global llm_service from api module
        config = load_config()
        
        if not api.llm_service:
            raise HTTPException(
                status_code=500,
                detail="LLM service not initialized. Please restart the application."
            )
        
        # Update config with requested export format
        config['ontology'] = config.get('ontology', {})
        config['ontology']['dynamic_generation'] = config['ontology'].get('dynamic_generation', {})
        config['ontology']['dynamic_generation']['export_format'] = request.export_format
        
        dynamic_ontology = get_dynamic_ontology_service(api.llm_service, config)
        
        # Create a proper connection ID from database connection info
        db_info = db_service.connection_params
        connection_id = f"{db_info['database']}_{db_info['host']}_{db_info['port']}"
        
        logger.info(f"🤖 Generating ontology for database: {db_info['database']} ({len(tables)} tables)")
        
        # Generate ontology
        ontology = dynamic_ontology.generate_ontology(
            schema_snapshot=schema_snapshot,
            connection_id=connection_id,
            force_regenerate=request.force_regenerate
        )
        
        # Prepare response
        response_data = {
            "success": True,
            "message": "Ontology generated successfully",
            "database": db_info['database'],
            "connection_id": connection_id,
            "concepts_count": len(ontology.get('concepts', [])),
            "properties_count": len(ontology.get('properties', [])),
            "relationships_count": len(ontology.get('relationships', [])),
            "tables_analyzed": len(tables),
            "owl_path": ontology.get('owl_export_path'),
            "yaml_path": ontology.get('yaml_export_path')
        }
        
        logger.info(
            f"✅ Ontology generated: {response_data['concepts_count']} concepts, "
            f"{response_data['properties_count']} properties, "
            f"{response_data['relationships_count']} relationships"
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate ontology: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_ontology_files():
    """List exported ontology files for current database connection"""
    try:
        from ..services.ontology_export import get_owl_exporter
        from ..services.database import db_service
        
        exporter = get_owl_exporter()
        files = exporter.list_exported_ontologies()
        
        # Get current connection info to filter files
        current_connection_id = None
        if db_service.connection_params:
            db_info = db_service.connection_params
            current_connection_id = f"{db_info['database']}_{db_info['host']}_{db_info['port']}"
            logger.info(f"Filtering ontology files for connection: {current_connection_id}")
        
        # Get file details and filter by current connection
        file_list = []
        ontology_dir = Path(exporter.output_dir)
        
        for filename in files:
            filepath = ontology_dir / filename
            if filepath.exists():
                # Filter files based on current connection_id
                # Ontology files are named like: {connection_id}_ontology_{timestamp}.owl
                if current_connection_id is None:
                    # If no active connection, don't show any files
                    continue
                
                if not filename.startswith(current_connection_id):
                    # Skip files from other database connections
                    continue
                
                stat = filepath.stat()
                file_list.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'timestamp': stat.st_mtime,
                    'format': 'owl' if filename.endswith('.owl') else 'yml'
                })
        
        return {
            "success": True,
            "files": file_list
        }
        
    except Exception as e:
        logger.error(f"Failed to list ontology files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_ontology_file(filename: str):
    """Download an ontology file"""
    try:
        from ..services.ontology_export import get_owl_exporter
        
        exporter = get_owl_exporter()
        filepath = Path(exporter.output_dir) / filename
        
        # Security: prevent directory traversal
        if not filepath.resolve().is_relative_to(Path(exporter.output_dir).resolve()):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine content type
        content_type = 'application/rdf+xml' if filename.endswith('.owl') else 'text/yaml'
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download ontology file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
