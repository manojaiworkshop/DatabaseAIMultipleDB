"""
SQL Agent using LangGraph for intelligent query generation and error recovery
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import logging
from datetime import datetime
from .context_manager import ContextManager, create_context_manager
from .knowledge_graph import get_knowledge_graph_service

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the SQL Agent"""
    # Input
    question: str
    schema_context: str
    max_retries: int
    schema_name: Optional[str]
    schema_snapshot: Optional[Dict[str, Any]]  # Full schema snapshot for knowledge graph
    
    # Processing
    current_retry: int
    sql_query: Optional[str]
    error_message: Optional[str]
    error_history: List[str]
    graph_insights: Optional[Dict[str, Any]]  # Knowledge graph insights
    
    # Output
    results: Optional[List[Dict[str, Any]]]
    columns: Optional[List[str]]
    execution_time: Optional[float]
    explanation: Optional[str]
    success: bool


class SQLAgent:
    """SQL Agent with retry logic and error handling"""
    
    def __init__(self, llm_service, db_service, config: Optional[Dict] = None):
        self.llm_service = llm_service
        self.db_service = db_service
        self.config = config or {}
        
        # Initialize context manager for intelligent token budgeting
        self.context_manager = create_context_manager(self.config)
        logger.info(f"SQLAgent initialized with context strategy: {self.context_manager.strategy.value}")
        logger.info(f"Token budget - Schema: {self.context_manager.budget.schema}, "
                   f"Error: {self.context_manager.budget.error_context}")
        
        # Initialize knowledge graph service
        self.knowledge_graph = get_knowledge_graph_service(self.config)
        self.use_knowledge_graph = (
            self.knowledge_graph and 
            self.knowledge_graph.enabled and 
            self.config.get('neo4j', {}).get('include_in_context', True)
        )
        
        if self.use_knowledge_graph:
            logger.info("🔗 Knowledge Graph enabled for enhanced SQL generation")
        else:
            logger.info("Knowledge Graph disabled or not configured")
        
        # Initialize ontology service (static ontology mappings)
        from .ontology import get_ontology_service
        self.ontology = get_ontology_service(self.config)
        self.use_ontology = (
            self.ontology and 
            self.ontology.enabled and
            self.config.get('ontology', {}).get('enabled', True)
        )
        
        if self.use_ontology:
            logger.info("🧠 Static ontology enabled for semantic understanding")
        else:
            logger.info("Static ontology disabled")
        
        self.graph = self._build_graph()
    
    def reload_config(self, new_config: Dict[str, Any]):
        """
        Reload configuration and reinitialize services dynamically
        This allows settings changes to take effect without restarting the backend
        """
        logger.info("🔄 Reloading SQLAgent configuration...")
        self.config = new_config
        
        # Reinitialize Knowledge Graph service
        try:
            from .knowledge_graph import get_knowledge_graph_service
            self.knowledge_graph = get_knowledge_graph_service(self.config)
            self.use_knowledge_graph = (
                self.knowledge_graph and 
                self.knowledge_graph.enabled and 
                self.config.get('neo4j', {}).get('include_in_context', True)
            )
            if self.use_knowledge_graph:
                logger.info("✅ Knowledge Graph ENABLED after reload")
            else:
                logger.info("⚠️  Knowledge Graph DISABLED after reload")
        except Exception as e:
            logger.error(f"Failed to reload Knowledge Graph: {e}")
            self.knowledge_graph = None
            self.use_knowledge_graph = False
        
        # Reinitialize Ontology service
        try:
            from .ontology import get_ontology_service
            self.ontology = get_ontology_service(self.config)
            self.use_ontology = (
                self.ontology and 
                self.ontology.enabled and
                self.config.get('ontology', {}).get('enabled', True)
            )
            if self.use_ontology:
                logger.info("✅ Ontology ENABLED after reload")
            else:
                logger.info("⚠️  Ontology DISABLED after reload")
        except Exception as e:
            logger.error(f"Failed to reload Ontology: {e}")
            self.ontology = None
            self.use_ontology = False
        
        logger.info("🔄 SQLAgent configuration reload complete")
        
    def _build_graph(self) -> StateGraph:
        """Build the agent graph"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("validate_sql", self._validate_sql_node)
        workflow.add_node("execute_sql", self._execute_sql_node)
        workflow.add_node("handle_error", self._handle_error_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("generate_sql")
        
        # Add edges
        workflow.add_edge("generate_sql", "validate_sql")
        workflow.add_conditional_edges(
            "validate_sql",
            self._should_execute_or_retry,
            {
                "execute": "execute_sql",
                "retry": "handle_error",
                "end": "finalize"
            }
        )
        workflow.add_conditional_edges(
            "execute_sql",
            self._check_execution_result,
            {
                "success": "finalize",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "handle_error",
            self._should_retry,
            {
                "retry": "generate_sql",
                "end": "finalize"
            }
        )
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _normalize_schema_snapshot(self, schema_snapshot: Any) -> Dict[str, Any]:
        """
        Normalize schema_snapshot to dict format with 'tables' key
        Handles: list format, {'tables': [...]}, {'tables': {...}}
        Preserves metadata: database_name, connection_info, views, etc.
        """
        if isinstance(schema_snapshot, list):
            # Convert list to dict keyed by table_name
            schema_dict = {'tables': {}}
            for table in schema_snapshot:
                table_name = table.get('table_name', table.get('full_name', ''))
                if table_name:
                    schema_dict['tables'][table_name] = table
            return schema_dict
        elif isinstance(schema_snapshot, dict):
            if 'tables' in schema_snapshot:
                tables = schema_snapshot['tables']
                if isinstance(tables, list):
                    # Convert list to dict keyed by table_name
                    # Preserve all metadata from original snapshot
                    schema_dict = {
                        'tables': {},
                        'database_name': schema_snapshot.get('database_name', 'unknown'),
                        'connection_info': schema_snapshot.get('connection_info', {}),
                        'views': schema_snapshot.get('views', []),
                        'total_tables': schema_snapshot.get('total_tables', 0),
                        'total_views': schema_snapshot.get('total_views', 0),
                        'timestamp': schema_snapshot.get('timestamp', '')
                    }
                    for table in tables:
                        table_name = table.get('table_name', table.get('full_name', ''))
                        if table_name:
                            schema_dict['tables'][table_name] = table
                    return schema_dict
                elif isinstance(tables, dict):
                    return schema_snapshot
            elif len(schema_snapshot) > 0:
                return {'tables': schema_snapshot}
        return {'tables': {}}
    
    def _generate_sql_node(self, state: AgentState) -> AgentState:
        """Generate SQL query using LLM with dynamic context management and knowledge graph"""
        logger.info(f"🔄 Generating SQL (attempt {state['current_retry'] + 1}/{state['max_retries']})")
        logger.info(f"📝 QUESTION: {state['question']}")
        
        # Normalize schema_snapshot to handle both list and dict formats
        schema_snapshot_normalized = None
        if state.get('schema_snapshot'):
            logger.info("="*80)
            logger.info("🔍 TRACE: Schema Snapshot Normalization")
            logger.info("="*80)
            logger.info(f"Input snapshot keys: {list(state['schema_snapshot'].keys())}")
            logger.info(f"Input tables type: {type(state['schema_snapshot'].get('tables', []))}")
            
            schema_snapshot_normalized = self._normalize_schema_snapshot(state['schema_snapshot'])
            
            tables = schema_snapshot_normalized.get('tables', [])
            tables_count = len(tables.values()) if isinstance(tables, dict) else len(tables)
            
            logger.info(f"Output snapshot keys: {list(schema_snapshot_normalized.keys())}")
            logger.info(f"Output tables type: {type(tables)}")
            logger.info(f"✅ Schema normalized: {tables_count} tables")
            
            if tables_count > 0:
                if isinstance(tables, dict):
                    table_names = list(tables.keys())[:5]
                else:
                    table_names = [t.get('table_name', t.get('full_name', '?')) for t in tables[:5]]
                logger.info(f"📋 Tables available: {', '.join(table_names)}")
            else:
                logger.warning("⚠️  NO TABLES after normalization!")
            logger.info("="*80)
        
        # 🧠 STEP 1: ONTOLOGY - Semantic understanding
        logger.info("\n" + "="*80)
        logger.info("🔍 TRACE STEP 1: ONTOLOGY SEMANTIC RESOLUTION")
        logger.info("="*80)
        
        ontology_context = ""
        if self.use_ontology and schema_snapshot_normalized:
            try:
                logger.info("✅ Ontology is ENABLED")
                from .ontology import get_ontology_service
                ontology = get_ontology_service(self.config)
                
                logger.info(f"Ontology service: {ontology.__class__.__name__}")
                logger.info(f"Current column mappings count: {len(ontology.column_mappings)}")
                
                # Register schema mappings if not done
                if not ontology.column_mappings:
                    logger.info("📝 Registering schema mappings...")
                    ontology.register_schema_mappings(schema_snapshot_normalized)
                    
                    # Count total mappings
                    total_mappings = sum(len(mappings) for mappings in ontology.column_mappings.values())
                    logger.info(f"🧠 Registered {total_mappings} ontology column mappings across {len(ontology.column_mappings)} tables")
                    
                    # Show sample mappings
                    if ontology.column_mappings:
                        logger.info("📋 Sample column mappings (first 3):")
                        count = 0
                        for table_name, mappings_list in list(ontology.column_mappings.items())[:3]:
                            for mapping in mappings_list[:2]:  # Show max 2 per table
                                count += 1
                                logger.info(f"  {count}. {table_name}.{mapping.column} → {mapping.concept}.{mapping.property}")
                                if count >= 3:
                                    break
                            if count >= 3:
                                break
                else:
                    total_mappings = sum(len(mappings) for mappings in ontology.column_mappings.values())
                    logger.info(f"♻️  Using existing {total_mappings} mappings across {len(ontology.column_mappings)} tables")
                
                # Get available tables
                tables = schema_snapshot_normalized.get('tables', [])
                if isinstance(tables, dict):
                    available_tables = list(tables.keys())
                else:
                    available_tables = [t.get('table_name', t.get('full_name', '')) for t in tables if t.get('table_name') or t.get('full_name')]
                
                logger.info(f"📊 Available tables for resolution: {available_tables}")
                
                # Resolve query semantics
                logger.info(f"🔍 Resolving query: '{state['question']}'")
                semantic_resolution = ontology.resolve_query(state['question'], available_tables)
                
                if semantic_resolution:
                    logger.info(f"✅ Semantic resolution found!")
                    logger.info(f"   Confidence: {semantic_resolution.confidence:.0%}")
                    logger.info(f"   Reasoning: {semantic_resolution.reasoning[:100]}...")
                    logger.info(f"   Column mappings: {len(semantic_resolution.column_mappings)}")
                else:
                    logger.warning("❌ No semantic resolution returned")
                
                if semantic_resolution and semantic_resolution.column_mappings:
                    ontology_context = "\n\n🧠 ===ONTOLOGY SEMANTIC GUIDANCE (VERY IMPORTANT)=== \n"
                    ontology_context += f"Query Understanding: {semantic_resolution.reasoning}\n"
                    ontology_context += f"Confidence: {semantic_resolution.confidence:.0%}\n\n"
                    
                    ontology_context += "✅ RECOMMENDED COLUMNS TO USE:\n"
                    for i, mapping in enumerate(semantic_resolution.column_mappings[:5], 1):
                        ontology_context += f"{i}. USE: {mapping.table}.{mapping.column}\n"
                        ontology_context += f"   Reason: Maps to {mapping.concept}.{mapping.property}\n"
                        ontology_context += f"   Meaning: {mapping.description}\n"
                        ontology_context += f"   Confidence: {mapping.confidence:.0%}\n\n"
                    
                    logger.info(f"🎯 ONTOLOGY RECOMMENDATIONS:")
                    for i, mapping in enumerate(semantic_resolution.column_mappings[:3], 1):
                        logger.info(f"   {i}. {mapping.table}.{mapping.column} (confidence: {mapping.confidence:.0%})")
                else:
                    logger.warning("🧠 ONTOLOGY: No column mappings found")
            except Exception as e:
                logger.error(f"🧠 ONTOLOGY ERROR: {e}", exc_info=True)
                ontology_context = ""
        else:
            if not self.use_ontology:
                logger.info("⚠️  Ontology is DISABLED in config")
            if not schema_snapshot_normalized:
                logger.info("⚠️  No schema snapshot available")
        
        logger.info("="*80)
        
        # 📊 STEP 2: KNOWLEDGE GRAPH - Relationship insights
        logger.info("\n" + "="*80)
        logger.info("� TRACE STEP 2: KNOWLEDGE GRAPH INSIGHTS")
        logger.info("="*80)
        
        graph_insights_text = ""
        if self.use_knowledge_graph and schema_snapshot_normalized:
            try:
                logger.info("✅ Knowledge Graph is ENABLED")
                logger.info(f"🔍 Getting insights for question: '{state['question']}'")
                
                insights = self.knowledge_graph.get_graph_insights(
                    state['question'], 
                    schema_snapshot_normalized
                )
                state['graph_insights'] = insights
                
                logger.info(f"📊 Insights received:")
                logger.info(f"   Suggested columns: {len(insights.get('suggested_columns', {}))} tables")
                logger.info(f"   Suggested joins: {len(insights.get('suggested_joins', []))} paths")
                logger.info(f"   Related tables: {len(insights.get('related_tables', []))} tables")
                logger.info(f"   Recommendations: {len(insights.get('recommendations', []))}")
                
                # Format insights for LLM - ENHANCED with column suggestions
                if insights.get('suggested_columns'):
                    graph_insights_text += "\n\n🎯 **Relevant Columns for Your Query:**\n"
                    logger.info("📋 Column suggestions by table:")
                    for table, columns in insights['suggested_columns'].items():
                        col_names = [c['name'] for c in columns[:5]]
                        graph_insights_text += f"  • Table '{table}': {', '.join(col_names)}\n"
                        logger.info(f"   {table}: {col_names}")
                
                if insights.get('suggested_joins'):
                    graph_insights_text += "\n🔗 **Knowledge Graph Join Suggestions:**\n"
                    logger.info("🔗 Join suggestions:")
                    for join in insights['suggested_joins']:
                        path_str = ' → '.join(join['path'])
                        graph_insights_text += f"  • Join path: {path_str}\n"
                        logger.info(f"   {path_str}")
                
                if insights.get('related_tables'):
                    graph_insights_text += f"\n📊 Related tables: {', '.join(insights['related_tables'][:5])}\n"
                    logger.info(f"📊 Related tables: {insights['related_tables']}")
                
                if insights.get('recommendations'):
                    graph_insights_text += "\n💡 **Smart Recommendations:**\n"
                    logger.info("💡 Recommendations:")
                    for rec in insights['recommendations']:
                        graph_insights_text += f"  • {rec['message']}\n"
                        logger.info(f"   - {rec['message']}")
                
                logger.info(f"✅ Knowledge graph context generated ({len(graph_insights_text)} chars)")
                
            except Exception as e:
                logger.error(f"📊 KNOWLEDGE GRAPH ERROR: {e}", exc_info=True)
                graph_insights_text = ""
        else:
            if not self.use_knowledge_graph:
                logger.info("⚠️  Knowledge Graph is DISABLED in config")
            if not schema_snapshot_normalized:
                logger.info("⚠️  No schema snapshot available")
        
        logger.info("="*80)
        
        # 📚 STEP 3: RAG - Similar Past Queries
        logger.info("\n" + "="*80)
        logger.info("📚 TRACE STEP 3: RAG SIMILAR QUERIES")
        logger.info("="*80)
        
        rag_context = ""
        if self.config.get('rag', {}).get('enabled', False) and self.config.get('rag', {}).get('include_in_context', True):
            try:
                logger.info("✅ RAG is ENABLED")
                from .rag_service import get_rag_service
                rag_service = get_rag_service(self.config)
                
                if rag_service and rag_service.enabled:
                    logger.info(f"🔍 Searching for similar queries: '{state['question']}'")
                    
                    # Get database type for filtering
                    db_type = self.db_service.get_database_type() if hasattr(self.db_service, 'get_database_type') else None
                    schema_name = state.get('schema_name')
                    
                    logger.info(f"   Filters - DB Type: {db_type}, Schema: {schema_name}")
                    
                    # Get RAG context
                    rag_context = rag_service.get_rag_context(
                        user_query=state['question'],
                        database_type=db_type,
                        schema_name=schema_name
                    )
                    
                    if rag_context:
                        # Count similar queries
                        similar_count = rag_context.count("Example ")
                        logger.info(f"✅ Found {similar_count} similar past queries")
                        logger.info(f"📚 RAG context generated ({len(rag_context)} chars)")
                        
                        # Log first example for verification
                        if "Example 1" in rag_context:
                            first_example_end = rag_context.find("Example 2") if "Example 2" in rag_context else len(rag_context)
                            first_example = rag_context[rag_context.find("Example 1"):first_example_end].strip()
                            logger.info(f"📋 First similar query preview:\n{first_example[:200]}...")
                    else:
                        logger.info("⚠️  No similar queries found in RAG database")
                else:
                    logger.warning("⚠️  RAG service not available")
            except Exception as e:
                logger.error(f"📚 RAG ERROR: {e}", exc_info=True)
                rag_context = ""
        else:
            if not self.config.get('rag', {}).get('enabled', False):
                logger.info("⚠️  RAG is DISABLED in config")
            elif not self.config.get('rag', {}).get('include_in_context', True):
                logger.info("⚠️  RAG include_in_context is FALSE")
        
        logger.info("="*80)
        
        # Use ContextManager to build optimized prompt
        system_prompt = self.context_manager.build_system_prompt()
        
        # Build schema context (focused if retrying with error)
        if state['error_message'] and state['current_retry'] > 0:
            # For retries, extract relevant tables and include focused schema
            error_analysis = self._analyze_error(state['error_message'], state['schema_context'])
            
            # Extract table names from error
            mentioned_tables = self._extract_mentioned_tables(state['error_message'])
            
            # Parse schema to dict format for ContextManager
            schema_dict = self._parse_schema_to_dict(state['schema_context'])
            
            # Build focused schema using ContextManager
            schema_for_llm = self.context_manager.build_schema_context(
                schema=schema_dict,
                focused_tables=mentioned_tables,
                include_samples=False
            )
            
            # Build error context using ContextManager
            error_context = self.context_manager.build_error_context(
                error_msg=state['error_message'],
                analysis={
                    'hints': error_analysis.split('\n'),
                    'mentioned_tables': mentioned_tables
                },
                previous_sql=state.get('sql_query'),
                attempt_number=state['current_retry']
            )
            
            # Build final prompt
            prompt = f"""{system_prompt}

{error_context}

🎯 ORIGINAL QUESTION: {state['question']}

{schema_for_llm}
{ontology_context}
{graph_insights_text}
{rag_context}

Generate the CORRECTED SQL query:"""
        else:
            # First attempt - use full schema with SAMPLES for better column understanding
            schema_dict = self._parse_schema_to_dict(state['schema_context'])
            
            # CRITICAL: Include samples to help LLM understand column semantics
            schema_for_llm = self.context_manager.build_schema_context(
                schema=schema_dict,
                focused_tables=None,
                include_samples=True  # Changed from False to True
            )
            
            # Add column semantics hints based on the question
            column_hints = self._extract_column_hints(state['question'], schema_dict)
            
            prompt = f"""{system_prompt}

🎯 QUESTION: {state['question']}

{schema_for_llm}
{ontology_context}
{graph_insights_text}
{rag_context}
{column_hints}

Generate the SQL query:"""
        
        # Generate SQL
        logger.info("\n" + "="*80)
        logger.info("🔍 TRACE STEP 3: LLM SQL GENERATION")
        logger.info("="*80)
        logger.info(f"📝 Final prompt length: {len(prompt)} characters")
        logger.info(f"📊 Components:")
        logger.info(f"   - System prompt: {len(system_prompt)} chars")
        logger.info(f"   - Schema context: {len(schema_for_llm)} chars")
        logger.info(f"   - Ontology context: {len(ontology_context)} chars")
        logger.info(f"   - Knowledge graph context: {len(graph_insights_text)} chars")
        logger.info(f"💡 Has ontology guidance: {'YES ✅' if ontology_context else 'NO ❌'}")
        logger.info(f"💡 Has knowledge graph: {'YES ✅' if graph_insights_text else 'NO ❌'}")
        logger.info("="*80)
        
        try:
            logger.info("🤖 Calling LLM to generate SQL...")
            
            # Get database type from db_service
            database_type = self.db_service.get_database_type() if hasattr(self.db_service, 'get_database_type') else 'postgresql'
            logger.info(f"   Database type: {database_type.upper()}")
            
            llm_response = self.llm_service.generate_sql(
                question=prompt,
                schema_context=schema_for_llm,
                conversation_history=None,
                database_type=database_type
            )
            
            new_sql = llm_response.get('sql', '').strip()
            
            logger.info(f"✅ LLM response received")
            logger.info(f"   SQL length: {len(new_sql)} characters")
            logger.info(f"   Has explanation: {'YES' if llm_response.get('explanation') else 'NO'}")
            
            # Validate we got actual SQL
            if not new_sql or len(new_sql) == 0:
                logger.error("❌ LLM returned EMPTY SQL")
                raise ValueError("LLM returned empty SQL")
            
            # Check if SQL starts with valid keywords
            sql_upper = new_sql.upper().strip()
            valid_starts = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
            if not any(sql_upper.startswith(kw) for kw in valid_starts):
                logger.error(f"❌ LLM returned invalid SQL (doesn't start with SQL keyword)")
                logger.error(f"   SQL preview: {new_sql[:100]}")
                raise ValueError(f"LLM returned invalid SQL (doesn't start with SQL keyword): {new_sql[:100]}")
            
            state['sql_query'] = new_sql
            state['explanation'] = llm_response.get('explanation', '')
            state['error_message'] = None  # Clear error on successful generation
            
            # Log final SQL query with details
            logger.info("="*80)
            logger.info("🎯 FINAL SQL QUERY GENERATED:")
            logger.info("="*80)
            logger.info(f"Query:\n{state['sql_query']}")
            logger.info(f"\nLength: {len(state['sql_query'])} chars")
            logger.info(f"Prompt size: {len(prompt)} chars")
            logger.info(f"Compression ratio: {len(prompt)/len(state['sql_query']):.1f}:1")
            if state.get('explanation'):
                logger.info(f"\nExplanation: {state['explanation']}")
            logger.info("="*80)
            
            logger.info(f"Generated SQL: {state['sql_query'][:200]}...")
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            
            if not state.get('sql_query'):
                state['sql_query'] = ""  # Empty SQL will be caught by validation
            
            state['error_message'] = f"LLM generation error: {str(e)}"
            state['success'] = False
        
        return state
    
    def _analyze_error(self, error_message: str, schema_context: str) -> str:
        """Analyze error message and provide specific hints with actual table/column names"""
        import re
        hints = []
        
        # Column does not exist - ENHANCED with actual columns from table
        if "column" in error_message.lower() and "does not exist" in error_message.lower():
            # Try to extract the problematic column name
            match = re.search(r'column\s+["\']?(\w+)\.(\w+)["\']?\s+does not exist', error_message, re.IGNORECASE)
            if match:
                table_alias = match.group(1)
                col_name = match.group(2)
                
                # Try to find the actual table from the error context or SQL
                # Look for the table in the JOIN clause
                table_actual = self._find_table_for_alias(table_alias, schema_context)
                
                if table_actual:
                    # Get actual columns for this table
                    actual_cols = self._get_columns_for_table(table_actual, schema_context)
                    
                    hints.append(f"❌ Column '{table_alias}.{col_name}' does NOT exist!")
                    hints.append(f"✓ Table '{table_actual}' has these columns: {', '.join(actual_cols[:10])}")
                    
                    # Find similar column names
                    similar = self._find_similar_names(col_name, actual_cols, threshold=2)
                    if similar:
                        hints.append(f"💡 Did you mean: {', '.join(similar[:3])}?")
                else:
                    hints.append(f"❌ Column '{table_alias}.{col_name}' does NOT exist! Check the table schema carefully.")
            else:
                # Try without alias
                match = re.search(r'column\s+["\']?(\w+)["\']?\s+does not exist', error_message, re.IGNORECASE)
                if match:
                    col_name = match.group(1)
                    hints.append(f"❌ Column '{col_name}' does NOT exist! Review schema for correct column names.")
        
        # Table/Relation does not exist - ENHANCED with suggestions
        elif ("table" in error_message.lower() or "relation" in error_message.lower()) and "does not exist" in error_message.lower():
            # Try to extract the problematic table name
            match = re.search(r'(?:table|relation)\s+["\']?(\w+)["\']?\s+does not exist', error_message, re.IGNORECASE)
            if match:
                problematic_table = match.group(1)
                
                # Extract actual table names from schema
                actual_tables = self._extract_table_names(schema_context)
                
                hints.append(f"❌ Table '{problematic_table}' DOES NOT EXIST!")
                
                # Try to find similar table names
                similar = self._find_similar_names(problematic_table, actual_tables, threshold=3)
                if similar:
                    # Show actual columns for suggested tables
                    suggestions = []
                    for suggested_table in similar[:2]:
                        cols = self._get_columns_for_table(suggested_table, schema_context)
                        suggestions.append(f"{suggested_table}({', '.join(cols[:5])})")
                    
                    hints.append(f"💡 Did you mean: {' OR '.join(suggestions)}?")
                else:
                    hints.append(f"✓ Available tables: {', '.join(actual_tables[:8])}")
            else:
                actual_tables = self._extract_table_names(schema_context)
                hints.append(f"❌ Table name error! Available: {', '.join(actual_tables[:8])}")
        
        # Join/foreign key issues - TYPE MISMATCH (most common issue!)
        elif "no operator matches" in error_message.lower() or "operator does not exist" in error_message.lower():
            # Extract the data types from error message
            type_match = re.search(r'(integer|character varying|text|bigint|smallint|numeric|varchar)\s*=\s*(integer|character varying|text|bigint|smallint|numeric|varchar)', error_message, re.IGNORECASE)
            
            hints.append("❌ TYPE MISMATCH ERROR - Cannot compare different data types!")
            
            if type_match:
                type1 = type_match.group(1)
                type2 = type_match.group(2)
                hints.append(f"   Trying to compare: {type1} = {type2}")
            
            # Extract the problematic line
            line_match = re.search(r'LINE \d+:\s*(.+?)(?:\^|$)', error_message, re.DOTALL)
            if line_match:
                problem_line = line_match.group(1).strip()
                hints.append(f"   Problem in: {problem_line[:100]}")
            
            # Extract column names from the error context
            # Look for patterns like "table.column = table.column"
            col_match = re.findall(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', error_message)
            if col_match:
                for match in col_match[:1]:  # Just first match
                    table1, col1, table2, col2 = match
                    hints.append(f"\n🔍 COMPARING: {table1}.{col1} = {table2}.{col2}")
                    
                    # Get data types for these columns
                    type1_info = self._get_column_type(table1, col1, schema_context)
                    type2_info = self._get_column_type(table2, col2, schema_context)
                    
                    if type1_info:
                        hints.append(f"   • {table1}.{col1} is type: {type1_info}")
                    if type2_info:
                        hints.append(f"   • {table2}.{col2} is type: {type2_info}")
                    
                    # Suggest type casting
                    hints.append(f"\n💡 SOLUTION: Add type cast!")
                    if type_match:
                        type1_lower = type_match.group(1).lower()
                        if 'integer' in type1_lower or 'bigint' in type1_lower or 'smallint' in type1_lower:
                            hints.append(f"   Try: {table1}.{col1} = {table2}.{col2}::INTEGER")
                        elif 'varchar' in type1_lower or 'character' in type1_lower or 'text' in type1_lower:
                            hints.append(f"   Try: {table1}.{col1}::VARCHAR = {table2}.{col2}")
                            hints.append(f"   Or:  {table1}.{col1} = {table2}.{col2}::VARCHAR")
            else:
                hints.append("\n💡 SOLUTION: You need to cast one column to match the other's type")
                hints.append("   Examples:")
                hints.append("   - column_name::INTEGER (cast to integer)")
                hints.append("   - column_name::VARCHAR (cast to varchar)")
                hints.append("   - CAST(column_name AS INTEGER)")
            
            hints.append("\n⚠️ IMPORTANT: Check the schema below for EXACT column data types!")
        
        # Syntax errors
        elif "syntax error" in error_message.lower():
            # Extract what's near the syntax error
            match = re.search(r'syntax error at or near ["\']?(\w+)["\']?', error_message, re.IGNORECASE)
            if match:
                problem_word = match.group(1)
                hints.append(f"❌ Syntax error near '{problem_word}'")
                hints.append("💡 Check PostgreSQL syntax - ensure proper use of keywords, parentheses, and semicolons")
            else:
                hints.append("❌ SQL syntax error - check PostgreSQL syntax carefully")
        
        if hints:
            return "\n".join(hints)
        else:
            return "⚠️ Review the error message and check your SQL against the schema"
    
    def _validate_sql_node(self, state: AgentState) -> AgentState:
        """Validate SQL query syntax"""
        logger.info("Validating SQL query")
        
        # CRITICAL: If we already have an LLM generation error, don't proceed
        # This prevents reusing old bad SQL
        if state.get('error_message') and 'LLM generation error' in state.get('error_message', ''):
            logger.warning(f"Skipping validation due to LLM error: {state['error_message']}")
            return state
        
        sql_query = state['sql_query']
        
        # Check for empty or None SQL
        if not sql_query or sql_query.strip() == '':
            state['error_message'] = "Empty SQL query generated by LLM"
            return state
        
        # Basic validation
        sql_lower = sql_query.lower().strip()
        sql_upper = sql_query.upper().strip()
        
        # Check if SQL starts with valid keyword
        valid_sql_starts = ['select', 'with', 'insert', 'update', 'delete', 'create', 'drop', 'alter']
        if not any(sql_lower.startswith(kw) for kw in valid_sql_starts):
            state['error_message'] = f"Invalid SQL: Query must start with SQL keyword (SELECT, WITH, etc.), but starts with: {sql_query[:50]}"
            return state
        
        # Check for common LLM mistakes - explanatory text in SQL
        bad_patterns = [
            'based on', 'here are', 'there are', 'the following', 
            'here is', 'this query', 'you can', 'i apologize'
        ]
        if any(pattern in sql_lower for pattern in bad_patterns):
            state['error_message'] = f"Invalid SQL: Contains explanatory text instead of pure SQL. LLM returned: {sql_query[:100]}"
            return state
        
        # Check for dangerous operations
        dangerous_keywords = ['drop', 'truncate', 'delete', 'update', 'insert', 'alter']
        if any(keyword in sql_lower for keyword in dangerous_keywords):
            # Allow if explicitly in question
            question_lower = state['question'].lower()
            if not any(keyword in question_lower for keyword in dangerous_keywords):
                state['error_message'] = "Query contains potentially dangerous operation not requested"
                return state
        
        # If schema_name provided, check if it's used
        if state.get('schema_name'):
            schema_name = state['schema_name']
            # Try to add schema prefix if not present
            if schema_name not in sql_query and 'FROM' in sql_query.upper():
                logger.info(f"Adding schema prefix: {schema_name}")
                # This is a simple heuristic - the LLM should ideally handle this
                state['error_message'] = f"Hint: Use schema prefix like {schema_name}.table_name"
                return state
        
        # Clear error message if validation passed - ready for execution
        state['error_message'] = None
        
        return state
    
    def _execute_sql_node(self, state: AgentState) -> AgentState:
        """Execute SQL query against database"""
        logger.info("Executing SQL query")
        
        try:
            import time
            start_time = time.time()
            
            results, columns, execution_time = self.db_service.execute_query(state['sql_query'])
            
            state['results'] = results
            state['columns'] = columns
            state['execution_time'] = execution_time
            state['success'] = True
            state['error_message'] = None
            
            logger.info(f"Query executed successfully: {len(results)} rows in {execution_time:.3f}s")
            
            # Store successful query in RAG database
            if self.config.get('rag', {}).get('enabled', False):
                try:
                    from .rag_service import get_rag_service
                    rag_service = get_rag_service(self.config)
                    
                    if rag_service and rag_service.enabled:
                        db_type = self.db_service.get_database_type() if hasattr(self.db_service, 'get_database_type') else None
                        schema_name = state.get('schema_name')
                        
                        rag_service.add_query(
                            user_query=state['question'],
                            sql_query=state['sql_query'],
                            database_type=db_type or 'postgresql',
                            schema_name=schema_name,
                            success=True,
                            metadata={
                                'execution_time': execution_time,
                                'row_count': len(results),
                                'retry_count': state['current_retry']
                            }
                        )
                        logger.info("✅ Successful query stored in RAG database")
                except Exception as e:
                    logger.warning(f"Failed to store query in RAG: {e}")
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"Query execution failed: {error_str}")
            
            state['error_message'] = error_str
            state['error_history'].append(error_str)
            state['success'] = False
        
        return state
    
    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Handle error and prepare for retry"""
        logger.warning(f"Handling error (retry {state['current_retry']}/{state['max_retries']})")
        
        # Store current error in history before clearing
        if state['error_message']:
            logger.info(f"Error: {state['error_message']}")
            # Only add to history if it's not already there (avoid duplicates)
            if not state['error_history'] or state['error_message'] != state['error_history'][-1]:
                state['error_history'].append(state['error_message'])
        
        state['current_retry'] += 1
        
        # Note: Don't clear error_message here - it's used in the next generate attempt
        # It will be cleared after successful generation
        
        return state
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize the result"""
        logger.info(f"Finalizing result. Success: {state['success']}")
        return state
    
    def _should_execute_or_retry(self, state: AgentState) -> str:
        """Decide whether to execute or retry after validation"""
        if state.get('error_message'):
            # Validation failed
            if state['current_retry'] >= state['max_retries']:
                return "end"
            return "retry"
        return "execute"
    
    def _check_execution_result(self, state: AgentState) -> str:
        """Check if execution was successful"""
        if state['success']:
            return "success"
        return "error"
    
    def _should_retry(self, state: AgentState) -> str:
        """Decide whether to retry or end"""
        if state['current_retry'] < state['max_retries']:
            return "retry"
        return "end"
    
    def run(self, question: str, schema_context: str, max_retries: int = 3, 
            schema_name: Optional[str] = None, schema_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the agent"""
        logger.info(f"Starting SQL Agent for question: {question}")
        
        initial_state: AgentState = {
            'question': question,
            'schema_context': schema_context,
            'max_retries': max_retries,
            'schema_name': schema_name,
            'schema_snapshot': schema_snapshot,  # Pass schema snapshot for knowledge graph
            'current_retry': 0,
            'sql_query': None,
            'error_message': None,
            'error_history': [],
            'graph_insights': None,
            'results': None,
            'columns': None,
            'execution_time': None,
            'explanation': None,
            'success': False
        }
        
        try:
            # Set recursion limit higher than max_retries to avoid issues
            # Each retry can go through multiple nodes: generate -> validate -> execute -> handle_error
            # So we need at least (max_retries + 1) * 5 steps
            recursion_limit = (max_retries + 1) * 10
            
            final_state = self.graph.invoke(
                initial_state,
                {"recursion_limit": recursion_limit}
            )
            
            return {
                'success': final_state['success'],
                'sql_query': final_state['sql_query'],
                'results': final_state['results'] or [],
                'columns': final_state['columns'] or [],
                'execution_time': final_state['execution_time'] or 0.0,
                'explanation': final_state['explanation'],
                'retry_count': final_state['current_retry'],
                'errors_encountered': final_state['error_history']
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                'success': False,
                'sql_query': '',
                'results': [],
                'columns': [],
                'execution_time': 0.0,
                'explanation': None,
                'retry_count': 0,
                'errors_encountered': [str(e)]
            }
    
    def _extract_table_names(self, schema_context: str) -> List[str]:
        """Extract table names from schema context"""
        import re
        # Look for pattern like "Table: table_name" or "table_name(...)"
        tables = []
        
        # Pattern 1: "Table: table_name"
        table_matches = re.findall(r'Table:\s*(\w+)', schema_context, re.IGNORECASE)
        tables.extend(table_matches)
        
        # Pattern 2: "table_name(...)" format
        if not tables:
            table_matches = re.findall(r'^(\w+)\(', schema_context, re.MULTILINE)
            tables.extend(table_matches)
        
        return list(set(tables))  # Remove duplicates
    
    def _get_columns_for_table(self, table_name: str, schema_context: str) -> List[str]:
        """Extract column names for a specific table from schema context"""
        import re
        columns = []
        
        # Look for pattern: "Table: table_name\nColumns:\n - col1\n - col2..."
        pattern = rf'Table:\s*{re.escape(table_name)}\s*\n\s*Columns:\s*\n((?:\s*-\s*\w+.*\n?)+)'
        match = re.search(pattern, schema_context, re.IGNORECASE | re.MULTILINE)
        
        if match:
            columns_text = match.group(1)
            # Extract column names (format: "- column_name (type) ...")
            col_names = re.findall(r'-\s*(\w+)', columns_text)
            columns.extend(col_names)
        
        # Alternative format: "table_name(col1, col2, col3)"
        if not columns:
            pattern = rf'{re.escape(table_name)}\s*\(([^)]+)\)'
            match = re.search(pattern, schema_context, re.IGNORECASE)
            if match:
                cols_text = match.group(1)
                # Split by comma and extract column names (may have types like "col:type")
                col_parts = [c.strip().split(':')[0] for c in cols_text.split(',')]
                columns.extend(col_parts)
        
        return columns
    
    def _find_table_for_alias(self, alias: str, schema_context: str) -> Optional[str]:
        """Try to find the actual table name from an alias by checking schema"""
        import re
        
        # Common patterns: 
        # - Single letter alias often matches first letter of table (w = web_user, r = role_permissions)
        # - Or it's just the table name itself
        
        tables = self._extract_table_names(schema_context)
        
        # First check if alias is actually a full table name
        if alias in tables:
            return alias
        
        # Check if alias is first letter(s) of a table
        alias_lower = alias.lower()
        for table in tables:
            table_lower = table.lower()
            # Check if table starts with alias
            if table_lower.startswith(alias_lower):
                return table
            # Check if alias matches table initials
            initials = ''.join([word[0] for word in re.split(r'[_-]', table_lower) if word])
            if initials == alias_lower:
                return table
        
        return None
    
    def _find_similar_names(self, target: str, candidates: List[str], threshold: int = 3) -> List[str]:
        """Find similar names using simple edit distance"""
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        similar = []
        target_lower = target.lower()
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            
            # Check substring match
            if target_lower in candidate_lower or candidate_lower in target_lower:
                similar.append((0, candidate))
                continue
            
            # Check edit distance
            distance = levenshtein_distance(target_lower, candidate_lower)
            if distance <= threshold:
                similar.append((distance, candidate))
        
        # Sort by distance and return names only
        similar.sort(key=lambda x: x[0])
        return [name for _, name in similar]
    
    def _get_compact_schema(self, schema_context: str) -> str:
        """Get compact version of schema with just table and column names"""
        import re
        
        # Extract table information
        compact_lines = []
        
        # Look for "Table: name" followed by "Columns:"
        table_pattern = r'Table:\s*(\w+)\s*\n\s*Columns:\s*\n((?:\s*-\s*\w+.*\n?)+)'
        matches = re.finditer(table_pattern, schema_context, re.MULTILINE)
        
        for match in matches:
            table_name = match.group(1)
            columns_text = match.group(2)
            
            # Extract column names only (ignore types)
            col_names = re.findall(r'-\s*(\w+)', columns_text)
            
            if col_names:
                compact_lines.append(f"{table_name}({', '.join(col_names[:8])})")  # Limit to 8 columns
        
        if compact_lines:
            return "Tables:\n" + "\n".join(compact_lines)
        else:
            # Fallback: return first 500 chars of schema
            return schema_context[:500]
    
    def _get_focused_schema(self, error_message: str, schema_context: str) -> str:
        """Get detailed schema for only the tables mentioned in the error"""
        import re
        
        # Check if it's a type mismatch error - we need full column details with types
        is_type_error = "operator does not exist" in error_message.lower() or "no operator matches" in error_message.lower()
        
        # Extract table names mentioned in the error
        error_lower = error_message.lower()
        all_tables = self._extract_table_names(schema_context)
        
        # Find which tables are relevant to this error
        relevant_tables = []
        for table in all_tables:
            if table.lower() in error_lower:
                relevant_tables.append(table)
        
        # If no tables found in error, look for JOIN keyword to get tables from query context
        if not relevant_tables:
            # Try to extract table names from common patterns
            table_patterns = [
                r'FROM\s+(\w+)',
                r'JOIN\s+(\w+)',
                r'relation\s+"?(\w+)"?',
                r'table\s+"?(\w+)"?'
            ]
            for pattern in table_patterns:
                matches = re.findall(pattern, error_message, re.IGNORECASE)
                for match in matches:
                    if match in all_tables:
                        relevant_tables.append(match)
        
        # If still no relevant tables, return compact schema for all
        if not relevant_tables:
            return self._get_compact_schema(schema_context)
        
        # Build detailed schema for relevant tables only
        focused_schema = []
        for table in list(set(relevant_tables))[:3]:  # Limit to 3 unique tables to save tokens
            # For type errors, show full detail with types
            if is_type_error:
                # Extract full table schema with types
                pattern = rf'Table:\s*{re.escape(table)}\s*\n\s*Columns:\s*\n((?:\s*-\s*\w+.*\n?)+)'
                match = re.search(pattern, schema_context, re.IGNORECASE | re.MULTILINE)
                
                if match:
                    focused_schema.append(f"Table: {table}")
                    focused_schema.append("Columns:")
                    columns_text = match.group(1)
                    # Keep the full column details with types
                    focused_schema.append(columns_text.strip())
                    focused_schema.append("")
            else:
                # For other errors, just show column names
                cols = self._get_columns_for_table(table, schema_context)
                if cols:
                    focused_schema.append(f"Table: {table}")
                    focused_schema.append(f"Columns: {', '.join(cols)}")
                    focused_schema.append("")
        
        if focused_schema:
            return "\n".join(focused_schema)
        else:
            return self._get_compact_schema(schema_context)
    
    def _get_column_type(self, table_name: str, column_name: str, schema_context: str) -> Optional[str]:
        """Get the data type of a specific column in a table"""
        import re
        
        # Look for pattern: "Table: table_name\nColumns:\n - col_name (type) ..."
        pattern = rf'Table:\s*{re.escape(table_name)}\s*\n\s*Columns:\s*\n((?:\s*-\s*\w+.*\n?)+)'
        match = re.search(pattern, schema_context, re.IGNORECASE | re.MULTILINE)
        
        if match:
            columns_text = match.group(1)
            # Look for the specific column with its type
            # Format: "- column_name (type) NULL/NOT NULL"
            col_pattern = rf'-\s*{re.escape(column_name)}\s*\(([^)]+)\)'
            col_match = re.search(col_pattern, columns_text, re.IGNORECASE)
            if col_match:
                return col_match.group(1).strip()
        
        return None

    def _parse_schema_to_dict(self, schema_context: str) -> Dict:
        """
        Parse text schema to dictionary format for ContextManager
        
        Returns:
            Dict with 'tables' key containing table definitions
        """
        import re
        
        schema_dict = {'tables': {}}
        
        # Extract tables from schema context
        # Format: "Table: table_name\nColumns:\n - col_name (type) ..."
        table_pattern = r'Table:\s*(\w+)\s*\n\s*Columns:\s*\n((?:\s*-\s*\w+.*\n?)+)'
        
        for match in re.finditer(table_pattern, schema_context, re.IGNORECASE | re.MULTILINE):
            table_name = match.group(1)
            columns_text = match.group(2)
            
            columns = []
            # Parse each column line
            for col_line in columns_text.strip().split('\n'):
                col_match = re.match(r'\s*-\s*(\w+)\s*\(([^)]+)\)\s*(.*)', col_line.strip())
                if col_match:
                    col_name = col_match.group(1)
                    col_type = col_match.group(2)
                    col_flags = col_match.group(3)
                    
                    column_info = {
                        'name': col_name,
                        'type': col_type,
                        'nullable': 'NOT NULL' not in col_flags,
                        'primary_key': 'PRIMARY KEY' in col_flags or 'PK' in col_flags,
                        'unique': 'UNIQUE' in col_flags
                    }
                    columns.append(column_info)
            
            schema_dict['tables'][table_name] = {
                'columns': columns,
                'foreign_keys': []  # Could be extracted if needed
            }
        
        return schema_dict
    
    def _extract_mentioned_tables(self, error_message: str) -> List[str]:
        """Extract table names mentioned in error message"""
        import re
        
        mentioned = []
        
        # Common patterns for table names in errors
        patterns = [
            r'table\s+["\']?(\w+)["\']?',
            r'relation\s+["\']?(\w+)["\']?',
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'(\w+)\.(\w+)',  # table.column pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            if pattern == r'(\w+)\.(\w+)':
                # Extract table name from table.column
                mentioned.extend([m[0] for m in matches])
            else:
                mentioned.extend(matches)
        
        # Remove duplicates and return
        return list(set(mentioned))
    
    def _extract_column_hints(self, question: str, schema: Dict) -> str:
        """
        Extract column hints from the question to help LLM find the right columns
        
        This is CRITICAL for semantic understanding - helps LLM match question terms
        to actual column names (e.g., "vendor" -> vendorgroup, vendorcategory, etc.)
        """
        import re
        
        hints = []
        question_lower = question.lower()
        
        # Define common semantic mappings
        semantic_keywords = {
            'vendor': ['vendor', 'supplier', 'provider'],
            'customer': ['customer', 'client', 'buyer'],
            'product': ['product', 'item', 'sku', 'material'],
            'order': ['order', 'purchase', 'sales'],
            'date': ['date', 'time', 'created', 'updated', 'timestamp'],
            'price': ['price', 'cost', 'amount', 'value', 'total'],
            'quantity': ['quantity', 'qty', 'count', 'amount'],
            'name': ['name', 'title', 'description'],
            'id': ['id', 'number', 'code'],
            'status': ['status', 'state', 'condition'],
            'type': ['type', 'category', 'class', 'group'],
            'country': ['country', 'nation', 'location', 'region'],
            'currency': ['currency', 'cur', 'exchange'],
        }
        
        # Find which keywords appear in the question
        mentioned_concepts = []
        for concept, keywords in semantic_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    mentioned_concepts.append(concept)
                    break
        
        if not mentioned_concepts:
            return ""
        
        # Find matching columns across all tables
        hints.append("\n💡 **Column Suggestions Based on Your Question:**")
        
        for concept in mentioned_concepts:
            matching_columns = []
            keywords = semantic_keywords[concept]
            
            # Search all tables for matching columns
            for table_name, table_info in schema.get('tables', {}).items():
                for column in table_info.get('columns', []):
                    col_name_lower = column['name'].lower()
                    
                    # Check if any keyword appears in column name
                    if any(kw in col_name_lower for kw in keywords):
                        matching_columns.append(f"{table_name}.{column['name']}")
            
            if matching_columns:
                keywords_str = ', '.join(keywords[:3])
                columns_str = ', '.join(matching_columns[:5])  # Limit to 5
                hints.append(f"  • For '{keywords_str}': Consider columns: {columns_str}")
        
        return '\n'.join(hints) if len(hints) > 1 else ""




