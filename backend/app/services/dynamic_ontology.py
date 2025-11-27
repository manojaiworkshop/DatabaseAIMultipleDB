"""
Dynamic Ontology Generation Service
Automatically generates domain-specific ontologies using LLM analysis
"""
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class DynamicConcept:
    """Dynamically generated domain concept"""
    name: str
    description: str
    tables: List[str]  # Related database tables
    properties: List[str]  # Key properties/attributes
    relationships: List[str]  # Relations to other concepts
    confidence: float = 0.0


@dataclass
class DynamicProperty:
    """Dynamically inferred property mapping"""
    concept: str
    property_name: str
    table: str
    column: str
    data_type: str
    semantic_meaning: str
    examples: List[str]
    confidence: float = 0.0


@dataclass
class DynamicRelationship:
    """Dynamically discovered relationship"""
    from_concept: str
    to_concept: str
    relationship_type: str  # e.g., "has_many", "belongs_to", "purchases"
    via_tables: List[str]
    via_columns: List[Tuple[str, str]]  # [(from_table, from_col), (to_table, to_col)]
    confidence: float = 0.0


class DynamicOntologyService:
    """
    Generates database-specific ontologies using LLM analysis
    
    For each database connection, analyzes schema and generates:
    1. Domain concepts (entities)
    2. Property mappings (columns → concept attributes)
    3. Relationships (foreign keys, semantic connections)
    4. Business rules and constraints
    """
    
    def __init__(self, llm_service, config: Dict[str, Any]):
        self.llm = llm_service
        self.config = config.get('ontology', {})
        self.dynamic_mode = self.config.get('dynamic_generation', {}).get('enabled', True)
        
        # Cache for generated ontologies (per session/schema)
        self.ontology_cache: Dict[str, Dict[str, Any]] = {}
        
        # Initialize OWL exporter for W3C format export
        from .ontology_export import get_owl_exporter
        self.owl_exporter = get_owl_exporter(output_dir="ontology")
        
        logger.info(f"Dynamic Ontology Service initialized (mode: {'dynamic' if self.dynamic_mode else 'static'})")
        logger.info(f"OWL export enabled: ontologies will be saved to 'ontology/' folder")
    
    def _normalize_schema_snapshot(self, schema_snapshot: Any) -> Dict[str, Any]:
        """
        Normalize schema_snapshot to dict format with 'tables' key
        
        Handles both list format [{'table_name': 'table1', ...}, ...] 
        and dict format {'tables': {...}}
        """
        if isinstance(schema_snapshot, list):
            # Convert list format to dict format
            # Keep as list in dict, don't convert to nested dict
            return {'tables': schema_snapshot}
            
        elif isinstance(schema_snapshot, dict):
            # Check if 'tables' key exists and what type it is
            if 'tables' in schema_snapshot:
                tables = schema_snapshot['tables']
                # If tables is a list, keep it as list (don't convert to dict!)
                if isinstance(tables, list):
                    # Already in correct format
                    return schema_snapshot
                # If tables is a dict, convert values to list
                elif isinstance(tables, dict):
                    return {
                        **schema_snapshot,
                        'tables': list(tables.values())
                    }
            # If no 'tables' key, assume top-level keys are table names
            elif len(schema_snapshot) > 0:
                # Convert dict to list format
                return {'tables': list(schema_snapshot.values())}
            return schema_snapshot
        else:
            return {'tables': []}
    
    def generate_ontology(
        self, 
        schema_snapshot: Any,
        connection_id: Optional[str] = None,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete ontology for the given database schema
        
        Args:
            schema_snapshot: Database schema information
            connection_id: Unique identifier for this database connection/session
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Complete ontology with concepts, properties, and relationships
        """
        # Normalize schema to dict format
        schema_snapshot = self._normalize_schema_snapshot(schema_snapshot)
        
        # Generate cache key based on schema structure
        cache_key = self._generate_cache_key(schema_snapshot, connection_id)
        
        # Check cache
        if not force_regenerate and cache_key in self.ontology_cache:
            logger.info(f"Using cached ontology for connection: {connection_id}")
            return self.ontology_cache[cache_key]
        
        logger.info(f"🔄 Generating dynamic ontology for {len(schema_snapshot.get('tables', {}))} tables...")
        
        # DEBUG: Print what we received
        tables = schema_snapshot.get('tables', [])
        tables_list = list(tables.values()) if isinstance(tables, dict) else tables
        logger.info("="*80)
        logger.info("🔍 DEBUG: SCHEMA SNAPSHOT RECEIVED")
        logger.info("="*80)
        logger.info(f"Schema snapshot keys: {list(schema_snapshot.keys())}")
        logger.info(f"Tables type: {type(tables)}")
        logger.info(f"Tables count: {len(tables_list)}")
        if tables_list:
            logger.info("First 3 tables:")
            for i, table in enumerate(tables_list[:3], 1):
                table_name = table.get('table_name', table.get('full_name', 'unknown'))
                col_count = len(table.get('columns', []))
                logger.info(f"  {i}. {table_name} ({col_count} columns)")
        else:
            logger.warning("⚠️  NO TABLES FOUND IN SCHEMA SNAPSHOT!")
        logger.info("="*80)
        
        try:
            tables = schema_snapshot.get('tables', [])
            tables_list = list(tables.values()) if isinstance(tables, dict) else tables
            num_tables = len(tables_list)
            
            # Determine batch size based on number of tables
            # For large schemas, process in batches to avoid token limits
            BATCH_SIZE = 10  # Process 10 tables at a time
            
            if num_tables <= BATCH_SIZE:
                # Small schema - process all at once
                logger.info(f"Processing all {num_tables} tables in single batch")
                schema_summary = self._summarize_schema(schema_snapshot)
                concepts = self._generate_concepts(schema_summary)
            else:
                # Large schema - process in batches
                logger.info(f"Large schema detected ({num_tables} tables). Processing in batches of {BATCH_SIZE}")
                all_concepts = []
                
                for batch_start in range(0, num_tables, BATCH_SIZE):
                    batch_end = min(batch_start + BATCH_SIZE, num_tables)
                    batch_tables = tables_list[batch_start:batch_end]
                    
                    logger.info(f"Processing batch {batch_start//BATCH_SIZE + 1}: tables {batch_start+1}-{batch_end}")
                    
                    # Create snapshot for this batch
                    batch_snapshot = {
                        'tables': batch_tables,
                        'database_name': schema_snapshot.get('database_name', '')
                    }
                    
                    batch_summary = self._summarize_schema(batch_snapshot)
                    batch_concepts = self._generate_concepts(batch_summary)
                    all_concepts.extend(batch_concepts)
                
                # Merge duplicate concepts (same name from different batches)
                concepts = self._merge_concepts(all_concepts)
                logger.info(f"Merged {len(all_concepts)} batch concepts into {len(concepts)} unique concepts")
            
            # Step 3: Map columns to concept properties
            properties = self._generate_property_mappings(schema_snapshot, concepts)
            
            # Step 4: Discover relationships between concepts
            relationships = self._generate_relationships(schema_snapshot, concepts)
            
            # Step 5: Generate business rules
            rules = self._generate_business_rules(schema_snapshot, concepts, relationships)
            
            # Compile complete ontology
            ontology = {
                'connection_id': connection_id,
                'cache_key': cache_key,
                'concepts': [asdict(c) for c in concepts],
                'properties': [asdict(p) for p in properties],
                'relationships': [asdict(r) for r in relationships],
                'rules': rules,
                'metadata': {
                    'table_count': len(schema_snapshot.get('tables', {})),
                    'concept_count': len(concepts),
                    'property_count': len(properties),
                    'relationship_count': len(relationships),
                    'generated_at': self._get_timestamp()
                }
            }
            
            # Cache the result
            self.ontology_cache[cache_key] = ontology
            
            # Export to requested format(s)
            export_format = self.config.get('dynamic_generation', {}).get('export_format', 'both')  # 'yml', 'owl', or 'both'
            
            # 📄 Export to YAML format
            if export_format in ['yml', 'yaml', 'both']:
                try:
                    yml_path = self._export_to_yaml(ontology, connection_id)
                    ontology['yaml_export_path'] = yml_path
                    logger.info(f"📄 Ontology exported to YAML: {yml_path}")
                    
                    # 🔄 AUTO-SYNC: Sync ontology to Knowledge Graph (Neo4j)
                    if self.config.get('neo4j', {}).get('enabled', False):
                        try:
                            from backend.app.services.ontology_kg_sync import get_ontology_kg_sync_service
                            
                            sync_service = get_ontology_kg_sync_service(self.config)
                            if sync_service.enabled:
                                logger.info(f"🔄 Auto-syncing ontology to Knowledge Graph...")
                                sync_result = sync_service.sync_ontology_file(yml_path)
                                
                                if sync_result.get('success'):
                                    logger.info(
                                        f"✅ Knowledge Graph synced: "
                                        f"{sync_result.get('concepts_synced', 0)} concepts, "
                                        f"{sync_result.get('mappings_created', 0)} semantic mappings"
                                    )
                                    ontology['kg_sync_status'] = 'success'
                                    ontology['kg_sync_result'] = sync_result
                                else:
                                    logger.warning(f"⚠️  Knowledge Graph sync failed: {sync_result.get('error')}")
                                    ontology['kg_sync_status'] = 'failed'
                        except Exception as sync_error:
                            logger.warning(f"Knowledge Graph auto-sync skipped: {sync_error}")
                            ontology['kg_sync_status'] = 'skipped'
                    
                except Exception as e:
                    logger.warning(f"Failed to export ontology to YAML: {e}")
            
            # 🦉 Export to W3C OWL format
            if export_format in ['owl', 'both']:
                try:
                    owl_path = self.owl_exporter.export_to_owl(
                        ontology=ontology,
                        session_id=connection_id
                    )
                    ontology['owl_export_path'] = owl_path
                    logger.info(f"🦉 Ontology exported to OWL: {owl_path}")
                except Exception as e:
                    logger.warning(f"Failed to export ontology to OWL: {e}")
            
            logger.info(
                f"✅ Dynamic ontology generated: "
                f"{len(concepts)} concepts, "
                f"{len(properties)} properties, "
                f"{len(relationships)} relationships"
            )
            
            return ontology
            
        except Exception as e:
            logger.error(f"Failed to generate dynamic ontology: {e}", exc_info=True)
            # Return minimal fallback ontology
            return self._create_fallback_ontology(schema_snapshot)
    
    def _summarize_schema(self, schema_snapshot: Dict[str, Any]) -> str:
        """Create a concise summary of the schema for LLM analysis"""
        tables = schema_snapshot.get('tables', [])
        
        # Handle both list and dict formats
        if isinstance(tables, dict):
            tables_list = list(tables.values())
        else:
            tables_list = tables
        
        logger.info(f"📊 Summarizing schema: {len(tables_list)} tables found")
        
        # Log table names for debugging
        table_names = [t.get('table_name', t.get('full_name', 'unknown')) for t in tables_list]
        logger.info(f"📋 Tables to summarize: {', '.join(table_names)}")
        
        summary = f"DATABASE SCHEMA SUMMARY:\n"
        summary += f"Total tables: {len(tables_list)}\n\n"
        
        for table in tables_list:
            # Get table name (handle different formats)
            table_name = table.get('table_name', 'Unknown')
            full_name = table.get('full_name', table_name)
            schema_name = table.get('schema_name', '')
            
            columns = table.get('columns', [])
            
            summary += f"Table: {full_name}\n"
            if schema_name and schema_name != 'public':
                summary += f"  Schema: {schema_name}\n"
            summary += f"  Columns ({len(columns)}):\n"
            
            # Show ALL columns with full details
            for col in columns:
                # Handle both dict and RealDictRow formats
                if hasattr(col, 'get'):
                    col_name = col.get('column_name', col.get('name', ''))
                    col_type = col.get('data_type', col.get('type', ''))
                    nullable = col.get('is_nullable', col.get('nullable', True))
                    default = col.get('column_default', col.get('default'))
                else:
                    col_name = getattr(col, 'column_name', getattr(col, 'name', ''))
                    col_type = getattr(col, 'data_type', getattr(col, 'type', ''))
                    nullable = getattr(col, 'is_nullable', True)
                    default = getattr(col, 'column_default', None)
                
                flags = []
                if col.get('primary_key') if hasattr(col, 'get') else getattr(col, 'primary_key', False):
                    flags.append('PK')
                if col.get('foreign_key') if hasattr(col, 'get') else getattr(col, 'foreign_key', None):
                    fk = col.get('foreign_key') if hasattr(col, 'get') else getattr(col, 'foreign_key')
                    flags.append(f"FK→{fk}")
                if nullable == 'NO' or not nullable:
                    flags.append('NOT NULL')
                if default:
                    flags.append(f"default={default}")
                
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                summary += f"    - {col_name} ({col_type}){flag_str}\n"
            
            summary += "\n"
        
        # Log summary length for debugging
        logger.info(f"📝 Schema summary generated: {len(summary)} characters")
        if len(summary) < 500:
            logger.warning(f"⚠️  Schema summary is suspiciously short! Content:\n{summary}")
        
        return summary
    
    def _generate_concepts(self, schema_summary: str) -> List[DynamicConcept]:
        """Use LLM to identify domain concepts from schema"""
        
        prompt = f"""Analyze this ACTUAL database schema and identify the key DOMAIN CONCEPTS based ONLY on what you see in the schema below.

{schema_summary}

CRITICAL INSTRUCTIONS:
1. Use ONLY the table names and columns shown above - DO NOT invent tables that don't exist
2. Base concepts DIRECTLY on the actual table names (e.g., if you see "network_devices", create a "NetworkDevice" concept)
3. DO NOT generate generic e-commerce concepts (Customer, Order, Product) unless those tables actually exist
4. If tables have technical names, translate them to business concepts (e.g., "tbl_usr" → "User")
5. **For properties, list the ACTUAL COLUMN NAMES from the schema (e.g., "device_id", "device_name", "ip_address")**
6. DO NOT create generic property names - use the exact column names shown in the schema

For each concept, provide:
1. Name - derive from actual table names in the schema
2. Description - what this table/concept represents in business terms
3. Related tables - list the ACTUAL table names from the schema (schema.table format if needed)
4. Key properties - list the ACTUAL COLUMN NAMES (not made-up property names)
5. Relationships - inferred from foreign keys and table relationships

Return ONLY a valid JSON array (no markdown, no other text):
[
  {{
    "name": "ConceptName",
    "description": "What this represents in business terms",
    "tables": ["actual_table_1", "actual_table_2"],
    "properties": ["actual_column_1", "actual_column_2", "actual_column_3"],
    "relationships": ["has RelatedConcept", "belongs to AnotherConcept"],
    "confidence": 0.95
  }}
]

IMPORTANT: 
- Base your analysis ONLY on the tables listed in the schema above
- Use ACTUAL column names as they appear in the schema (e.g., "device_id", NOT "DeviceID")
- Do not hallucinate concepts or column names"""

        # DEBUG: Print full schema summary and prompt
        logger.info("="*80)
        logger.info("🔍 DEBUG: FULL SCHEMA SUMMARY BEING SENT TO LLM")
        logger.info("="*80)
        logger.info(f"\n{schema_summary}")
        logger.info("="*80)
        logger.info(f"🤖 Prompt length: {len(prompt)} characters")
        logger.info(f"� Schema summary length: {len(schema_summary)} characters")
        
        # Save to file for inspection
        try:
            with open('debug_ontology_prompt.txt', 'w') as f:
                f.write("FULL PROMPT SENT TO LLM:\n")
                f.write("="*80 + "\n")
                f.write(prompt)
                f.write("\n" + "="*80 + "\n")
            logger.info("💾 Full prompt saved to: debug_ontology_prompt.txt")
        except Exception as e:
            logger.warning(f"Could not save debug prompt: {e}")
        
        try:
            # Build messages for structured generation
            messages = [
                {"role": "system", "content": "You are a database ontology expert. Return ONLY valid JSON, no markdown, no explanation."},
                {"role": "user", "content": prompt}
            ]
            
            # Use generate_structured for JSON response
            concepts_data = self.llm.generate_structured(messages, max_tokens=2048)
            
            if not isinstance(concepts_data, list):
                logger.warning(f"Expected list of concepts, got {type(concepts_data)}")
                concepts_data = []
            
            logger.info(f"LLM returned {len(concepts_data)} concepts")
            
            if not concepts_data:
                logger.warning("LLM returned empty concept list, using fallback heuristics")
                # Fallback: Create concepts from table names
                concepts_data = self._generate_concepts_from_tables(schema_summary)
            
            concepts = []
            for item in concepts_data:
                concept = DynamicConcept(
                    name=item.get('name', ''),
                    description=item.get('description', ''),
                    tables=item.get('tables', []),
                    properties=item.get('properties', []),
                    relationships=item.get('relationships', []),
                    confidence=item.get('confidence', 0.8)
                )
                if concept.name:  # Only add if has a name
                    concepts.append(concept)
            
            logger.info(f"Generated {len(concepts)} domain concepts")
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to generate concepts: {e}", exc_info=True)
            # Fallback to heuristic approach
            return self._generate_concepts_from_tables_fallback(schema_summary)
    
    def _generate_concepts_from_tables(self, schema_summary: str) -> List[Dict[str, Any]]:
        """Fallback: Generate basic concepts from table names"""
        import re
        concepts = []
        
        # Extract table names from summary
        table_pattern = r'Table:\s+(\w+)'
        tables = re.findall(table_pattern, schema_summary)
        
        for table in tables[:10]:  # Limit to 10 tables
            # Convert snake_case to Title Case
            concept_name = table.replace('_', ' ').title().replace(' ', '')
            concepts.append({
                'name': concept_name,
                'description': f'Represents {table.replace("_", " ")} data',
                'tables': [table],
                'properties': ['id', 'name'],
                'relationships': [],
                'confidence': 0.6
            })
        
        return concepts
    
    def _generate_concepts_from_tables_fallback(self, schema_summary: str) -> List[DynamicConcept]:
        """Final fallback: Create DynamicConcept objects from tables"""
        concepts_data = self._generate_concepts_from_tables(schema_summary)
        return [
            DynamicConcept(
                name=item['name'],
                description=item['description'],
                tables=item['tables'],
                properties=item['properties'],
                relationships=item['relationships'],
                confidence=item['confidence']
            )
            for item in concepts_data
        ]
    
    def _generate_property_mappings(
        self, 
        schema_snapshot: Dict[str, Any], 
        concepts: List[DynamicConcept]
    ) -> List[DynamicProperty]:
        """Map database columns to concept properties using LLM"""
        
        properties = []
        tables = schema_snapshot.get('tables', {})
        
        # Process each concept
        for concept in concepts:
            concept_tables = [t for t in concept.tables if t in tables]
            
            for table_name in concept_tables[:3]:  # Limit to 3 tables per concept
                table_info = tables[table_name]
                columns = table_info.get('columns', [])
                
                # Build column summary
                col_summary = "\n".join([
                    f"  - {col.get('name')} ({col.get('type')})"
                    for col in columns[:15]
                ])
                
                prompt = f"""Map these database columns to properties of the "{concept.name}" concept:

Concept: {concept.name}
Description: {concept.description}
Key Properties: {', '.join(concept.properties)}

Table: {table_name}
Columns:
{col_summary}

For each column, identify:
1. Which concept property it represents
2. The semantic meaning (what it really means in business terms)
3. Confidence (0.0-1.0)

Return JSON array:
[
  {{
    "column": "column_name",
    "property": "property_name",
    "semantic_meaning": "What this column represents",
    "confidence": 0.9
  }}
]

Only include columns clearly related to {concept.name}."""

                try:
                    messages = [
                        {"role": "system", "content": "You are a database ontology expert. Return ONLY valid JSON, no markdown, no explanation."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    mappings = self.llm.generate_structured(messages, max_tokens=1024)
                    
                    if not isinstance(mappings, list):
                        logger.warning(f"Expected list of mappings, got {type(mappings)}")
                        mappings = []
                    
                    for mapping in mappings:
                        col_name = mapping.get('column', '')
                        # Find column details
                        col_info = next((c for c in columns if c.get('name') == col_name), None)
                        if col_info:
                            prop = DynamicProperty(
                                concept=concept.name,
                                property_name=mapping.get('property', ''),
                                table=table_name,
                                column=col_name,
                                data_type=col_info.get('type', ''),
                                semantic_meaning=mapping.get('semantic_meaning', ''),
                                examples=col_info.get('sample_values', [])[:3],
                                confidence=mapping.get('confidence', 0.7)
                            )
                            properties.append(prop)
                    
                except Exception as e:
                    logger.warning(f"Failed to map properties for {concept.name}.{table_name}: {e}")
                    continue
        
        logger.info(f"Mapped {len(properties)} column properties")
        return properties
    
    def _generate_relationships(
        self, 
        schema_snapshot: Dict[str, Any], 
        concepts: List[DynamicConcept]
    ) -> List[DynamicRelationship]:
        """Discover relationships between concepts using LLM and schema analysis"""
        
        relationships = []
        tables = schema_snapshot.get('tables', [])
        
        # Handle both list and dict formats
        tables_dict = {}
        if isinstance(tables, list):
            for table in tables:
                table_name = table.get('table_name', table.get('full_name', ''))
                if table_name:
                    tables_dict[table_name] = table
        else:
            tables_dict = tables
        
        # Build foreign key map
        fk_map = {}
        for table_name, table_info in tables_dict.items():
            for col in table_info.get('columns', []):
                if col.get('foreign_key'):
                    fk_map.setdefault(table_name, []).append({
                        'column': col.get('column_name', col.get('name', '')),
                        'references': col['foreign_key']
                    })
        
        # Build concept summary
        concept_summary = "\n".join([
            f"- {c.name}: {c.description} (tables: {', '.join(c.tables[:3])})"
            for c in concepts
        ])
        
        # Build FK summary
        fk_summary = "\n".join([
            f"- {table}.{fk['column']} → {fk['references']}"
            for table, fks in fk_map.items()
            for fk in fks[:2]
        ])
        
        prompt = f"""Identify relationships between these ACTUAL domain concepts based on foreign keys and business logic:

CONCEPTS:
{concept_summary}

FOREIGN KEYS (from actual database):
{fk_summary}

CRITICAL INSTRUCTIONS:
1. Use ONLY the concept names listed above - do not invent new concepts
2. Base relationships on the ACTUAL foreign keys shown
3. Relationship names should reflect the business meaning (e.g., "monitors", "generates", "belongs_to")

For each relationship, provide:
1. From concept - must match a concept name from the list above
2. To concept - must match a concept name from the list above
3. Relationship type (e.g., "has_many", "belongs_to", "monitors", "generates")
4. Tables involved - use actual table names
5. Confidence (0.0-1.0)

Return ONLY valid JSON array (no markdown, no explanation):
[
  {{
    "from_concept": "ActualConceptName",
    "to_concept": "AnotherActualConceptName",
    "relationship_type": "relationship_verb",
    "via_tables": ["actual_table_name"],
    "confidence": 0.95
  }}
]

Base relationships on the foreign keys listed above."""

        try:
            messages = [
                {"role": "system", "content": "You are a database ontology expert. Return ONLY valid JSON, no markdown, no explanation."},
                {"role": "user", "content": prompt}
            ]
            
            rels_data = self.llm.generate_structured(messages, max_tokens=1024)
            
            if not isinstance(rels_data, list):
                logger.warning(f"Expected list of relationships, got {type(rels_data)}")
                rels_data = []
            
            for rel in rels_data:
                relationship = DynamicRelationship(
                    from_concept=rel.get('from_concept', ''),
                    to_concept=rel.get('to_concept', ''),
                    relationship_type=rel.get('relationship_type', ''),
                    via_tables=rel.get('via_tables', []),
                    via_columns=[],  # Could be extracted if needed
                    confidence=rel.get('confidence', 0.7)
                )
                relationships.append(relationship)
            
            logger.info(f"Discovered {len(relationships)} relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to generate relationships: {e}")
            return []
    
    def _generate_business_rules(
        self,
        schema_snapshot: Dict[str, Any],
        concepts: List[DynamicConcept],
        relationships: List[DynamicRelationship]
    ) -> List[Dict[str, Any]]:
        """Generate business rules and constraints"""
        
        # This could be expanded to use LLM for rule generation
        # For now, extract basic rules from schema constraints
        
        rules = []
        tables = schema_snapshot.get('tables', [])
        
        # Handle both list and dict formats
        tables_dict = {}
        if isinstance(tables, list):
            for table in tables:
                table_name = table.get('table_name', table.get('full_name', ''))
                if table_name:
                    tables_dict[table_name] = table
        else:
            tables_dict = tables
        
        for table_name, table_info in tables_dict.items():
            for col in table_info.get('columns', []):
                col_name = col.get('column_name', col.get('name', ''))
                
                # NOT NULL rules
                if col.get('is_nullable') == 'NO' or not col.get('nullable', True):
                    rules.append({
                        'type': 'required_field',
                        'table': table_name,
                        'column': col_name,
                        'description': f"{table_name}.{col_name} is required"
                    })
                
                # UNIQUE constraints
                if col.get('unique'):
                    rules.append({
                        'type': 'uniqueness',
                        'table': table_name,
                        'column': col_name,
                        'description': f"{table_name}.{col_name} must be unique"
                    })
        
        return rules
    
    def _export_to_yaml(self, ontology: Dict[str, Any], session_id: Optional[str] = None) -> str:
        """Export ontology to YAML format"""
        import yaml
        import os
        from datetime import datetime
        
        # Generate filename
        session_id = session_id or ontology.get('connection_id', 'default')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{session_id}_ontology_{timestamp}.yml"
        filepath = os.path.join("ontology", filename)
        
        # Build YAML structure
        yaml_content = {
            'ontology': {
                'metadata': {
                    'connection_id': ontology.get('connection_id'),
                    'generated_at': ontology.get('metadata', {}).get('generated_at'),
                    'table_count': ontology.get('metadata', {}).get('table_count', 0),
                    'concept_count': ontology.get('metadata', {}).get('concept_count', 0),
                    'property_count': ontology.get('metadata', {}).get('property_count', 0),
                    'relationship_count': ontology.get('metadata', {}).get('relationship_count', 0)
                },
                'concepts': {}
            }
        }
        
        # Add concepts
        for concept in ontology.get('concepts', []):
            yaml_content['ontology']['concepts'][concept['name']] = {
                'description': concept.get('description', ''),
                'tables': concept.get('tables', []),
                'properties': concept.get('properties', []),
                'relationships': concept.get('relationships', []),
                'confidence': concept.get('confidence', 0.0)
            }
        
        # Add property mappings
        if ontology.get('properties'):
            yaml_content['ontology']['property_mappings'] = []
            for prop in ontology.get('properties', []):
                yaml_content['ontology']['property_mappings'].append({
                    'concept': prop['concept'],
                    'property': prop['property_name'],
                    'table': prop['table'],
                    'column': prop['column'],
                    'type': prop['data_type'],
                    'semantic_meaning': prop.get('semantic_meaning', ''),
                    'examples': prop.get('examples', []),
                    'confidence': prop.get('confidence', 0.0)
                })
        
        # Add relationships
        if ontology.get('relationships'):
            yaml_content['ontology']['relationships'] = []
            for rel in ontology.get('relationships', []):
                yaml_content['ontology']['relationships'].append({
                    'from': rel['from_concept'],
                    'to': rel['to_concept'],
                    'type': rel['relationship_type'],
                    'via_tables': rel.get('via_tables', []),
                    'confidence': rel.get('confidence', 0.0)
                })
        
        # Add rules
        if ontology.get('rules'):
            yaml_content['ontology']['rules'] = ontology['rules']
        
        # Save to file
        os.makedirs("ontology", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        return filepath
    
    def _generate_cache_key(self, schema_snapshot: Dict[str, Any], connection_id: Optional[str]) -> str:
        """Generate a unique cache key based on schema structure"""
        # Create hash from table names and column counts
        tables = schema_snapshot.get('tables', [])
        
        # Handle both list and dict formats
        if isinstance(tables, list):
            # List format: [{'table_name': 'x', 'columns': [...]}]
            schema_dict = {
                table.get('table_name', table.get('full_name', f'table_{i}')): len(table.get('columns', []))
                for i, table in enumerate(tables)
            }
        else:
            # Dict format: {'table_name': {'columns': [...]}}
            schema_dict = {
                table_name: len(info.get('columns', []))
                for table_name, info in tables.items()
            }
        
        schema_str = json.dumps(schema_dict, sort_keys=True)
        hash_str = hashlib.md5(schema_str.encode()).hexdigest()
        
        if connection_id:
            return f"{connection_id}_{hash_str}"
        return hash_str
    
    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        import re
        
        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse entire response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Could not parse LLM JSON response")
            return []
    
    def _create_fallback_ontology(self, schema_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Create a minimal ontology if LLM generation fails"""
        tables = schema_snapshot.get('tables', [])
        
        # Handle both list and dict formats
        if isinstance(tables, list):
            table_names = [t.get('table_name', t.get('full_name', f'table_{i}')) for i, t in enumerate(tables)]
        else:
            table_names = list(tables.keys())
        
        # Create one concept per table
        concepts = []
        for table_name in table_names:
            concepts.append({
                'name': table_name.title().replace('_', ''),
                'description': f'Represents {table_name} data',
                'tables': [table_name],
                'properties': [],
                'relationships': [],
                'confidence': 0.5
            })
        
        return {
            'connection_id': None,
            'cache_key': 'fallback',
            'concepts': concepts,
            'properties': [],
            'relationships': [],
            'rules': [],
            'metadata': {
                'table_count': len(tables),
                'concept_count': len(concepts),
                'generated_at': self._get_timestamp(),
                'mode': 'fallback'
            }
        }
    
    def _merge_concepts(self, concepts_list: List[DynamicConcept]) -> List[DynamicConcept]:
        """Merge duplicate concepts from batch processing"""
        merged = {}
        
        for concept in concepts_list:
            if concept.name in merged:
                # Merge tables and properties
                merged[concept.name].tables = list(set(merged[concept.name].tables + concept.tables))
                merged[concept.name].properties = list(set(merged[concept.name].properties + concept.properties))
                merged[concept.name].relationships = list(set(merged[concept.name].relationships + concept.relationships))
                # Use higher confidence
                merged[concept.name].confidence = max(merged[concept.name].confidence, concept.confidence)
            else:
                merged[concept.name] = concept
        
        return list(merged.values())
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_cached_ontology(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached ontology for a connection"""
        for cache_key, ontology in self.ontology_cache.items():
            if ontology.get('connection_id') == connection_id:
                return ontology
        return None
    
    def clear_cache(self, connection_id: Optional[str] = None):
        """Clear ontology cache"""
        if connection_id:
            # Clear specific connection
            to_remove = [
                key for key, ont in self.ontology_cache.items()
                if ont.get('connection_id') == connection_id
            ]
            for key in to_remove:
                del self.ontology_cache[key]
            logger.info(f"Cleared ontology cache for connection: {connection_id}")
        else:
            # Clear all
            self.ontology_cache.clear()
            logger.info("Cleared all ontology cache")


# Singleton instance
_dynamic_ontology_service = None

def get_dynamic_ontology_service(llm_service, config: Dict[str, Any]) -> DynamicOntologyService:
    """Get or create dynamic ontology service"""
    global _dynamic_ontology_service
    if _dynamic_ontology_service is None:
        _dynamic_ontology_service = DynamicOntologyService(llm_service, config)
    return _dynamic_ontology_service
