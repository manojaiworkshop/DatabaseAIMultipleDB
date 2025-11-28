"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml
import logging
from pathlib import Path

from .routes.api import router, llm_service as global_llm_service, sql_agent as global_sql_agent
from .routes.license import router as license_router
from .routes.settings import router as settings_router
from .services.llm import LLMService
from .services.sql_agent import SQLAgent
from .services.database import db_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config_path = Path(__file__).parent.parent.parent / "app_config.yml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Create FastAPI app
app = FastAPI(
    title="DatabaseAI API",
    description="Natural language to SQL query interface",
    version="1.0.0"
)

# Configure CORS
cors_config = config.get('cors', {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('allow_origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
)

# Initialize LLM service and SQL agent
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global global_llm_service, global_sql_agent
    
    logger.info("Initializing LLM service...")
    from .routes import api
    api.llm_service = LLMService(config)
    logger.info(f"LLM service initialized with provider: {config['llm']['provider']}")
    
    logger.info("Initializing SQL Agent with context management...")
    api.sql_agent = SQLAgent(api.llm_service, db_service, config)
    logger.info("SQL Agent initialized successfully")
    
    # Start license validator background thread
    logger.info("Starting license validator...")
    from .services.license_validator import start_license_validator, get_license_validator
    from .routes.license import get_stored_license
    start_license_validator()
    
    # Load and validate current license
    license_key = get_stored_license()
    if license_key:
        validator = get_license_validator()
        validator.set_license_key(license_key)
        logger.info("License validator started with existing license")
    else:
        logger.info("License validator started (no license key found)")
    
    # Initialize RAG service
    logger.info("Initializing RAG service...")
    from .services.rag_service import get_rag_service
    rag_service = get_rag_service(config)
    if rag_service and rag_service.enabled:
        logger.info("RAG service initialized successfully")
    else:
        logger.info("RAG service is disabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Stopping license validator...")
    from .services.license_validator import stop_license_validator
    stop_license_validator()
    
    # Close RAG service connection
    logger.info("Closing RAG service...")
    from .services.rag_service import get_rag_service
    rag_service = get_rag_service(config)
    if rag_service:
        rag_service.close()
    
    logger.info("Application shutdown complete")

# Store config in app state for access in routes
app.state.config = config

# Include routers
app.include_router(router, prefix="/api/v1", tags=["api"])
app.include_router(license_router, prefix="/api/v1", tags=["license"])
app.include_router(settings_router, prefix="/api/v1", tags=["settings"])

# Import and include ontology router
try:
    from .routes.ontology import router as ontology_router
    app.include_router(ontology_router, prefix="/api/v1/ontology", tags=["ontology"])
    logger.info("Ontology router loaded")
except Exception as e:
    logger.warning(f"Ontology router not available: {e}")

# Import and include RAG router
try:
    from .routes.rag import router as rag_router
    app.include_router(rag_router, prefix="/api/v1", tags=["rag"])
    logger.info("RAG router loaded")
except Exception as e:
    logger.warning(f"RAG router not available: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "PGAIView API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    
    server_config = config.get('server', {})
    uvicorn.run(
        "app.main:app",
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 8088)
      
    )
