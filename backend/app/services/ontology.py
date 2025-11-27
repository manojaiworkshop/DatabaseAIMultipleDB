"""
Ontology Service - Semantic Layer for DatabaseAI

This service provides semantic understanding of database schemas through
ontology-based mappings, enabling high-accuracy natural language to SQL translation.

Key Features:
- Domain concept definitions (Vendor, Product, Order, etc.)
- Semantic property mappings (vendor name → vendorgroup column)
- Synonym resolution (supplier = vendor)
- Query pattern matching
- Confidence scoring for mappings
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ConceptProperty:
    """Property of a domain concept"""
    name: str
    data_type: str
    required: bool = False
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    semantic_type: Optional[str] = None


@dataclass
class DomainConcept:
    """Represents a business entity/concept in the domain"""
    name: str
    description: str
    synonyms: List[str] = field(default_factory=list)
    properties: Dict[str, ConceptProperty] = field(default_factory=dict)
    parent_concept: Optional[str] = None
    
    def matches_term(self, term: str) -> bool:
        """Check if term matches this concept"""
        term_lower = term.lower().strip()
        if term_lower == self.name.lower():
            return True
        return any(syn.lower() == term_lower for syn in self.synonyms)


@dataclass
class ColumnMapping:
    """Maps a database column to an ontology concept/property"""
    table: str
    column: str
    concept: str
    property: str
    semantic_type: str
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.9
    description: str = ""
    data_type: Optional[str] = None


@dataclass
class SemanticRelationship:
    """Defines relationship between concepts"""
    name: str
    source_concept: str
    target_concept: str
    description: str
    synonyms: List[str] = field(default_factory=list)
    cardinality: str = "many-to-many"  # one-to-one, one-to-many, many-to-many


@dataclass
class QueryPattern:
    """Pattern for matching and resolving natural language queries"""
    pattern: str
    concept: str
    property: str
    operation: str  # SELECT, DISTINCT, COUNT, etc.
    suggested_columns: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.85
    explanation: str = ""


@dataclass
class SemanticResolution:
    """Result of semantic query analysis"""
    concepts: List[str]
    properties: List[str]
    operations: List[str]
    column_mappings: List[ColumnMapping]
    relationships: List[SemanticRelationship]
    confidence: float
    reasoning: str
    suggested_sql_hints: Dict[str, Any]


class OntologyService:
    """
    Semantic layer service that provides domain knowledge for query understanding
    
    This service acts as the "brain" that understands what users mean when they
    say things like "vendor names" or "high-value orders"
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('ontology', {}).get('enabled', True)
        
        # Core ontology components
        self.concepts: Dict[str, DomainConcept] = {}
        self.relationships: Dict[str, SemanticRelationship] = {}
        self.column_mappings: Dict[str, List[ColumnMapping]] = {}  # table -> mappings
        self.query_patterns: List[QueryPattern] = []
        
        # Synonym indexes for fast lookup
        self.synonym_to_concept: Dict[str, str] = {}
        self.keyword_to_columns: Dict[str, List[ColumnMapping]] = {}
        
        # Load ontology
        if self.enabled:
            self._load_default_ontology()
            self._load_custom_ontology()
            logger.info("Ontology service initialized successfully")
    
    def _load_default_ontology(self):
        """Load default procurement domain ontology"""
        
        # Define core concepts
        self.concepts['Vendor'] = DomainConcept(
            name='Vendor',
            description='A supplier or seller of products/services',
            synonyms=['supplier', 'seller', 'merchant', 'provider', 'supplyer', 'vender'],
            properties={
                'name': ConceptProperty(
                    name='name',
                    data_type='string',
                    required=True,
                    description='Vendor identifier or name',
                    keywords=['name', 'identifier', 'title', 'vendor name', 'supplier name'],
                    semantic_type='identifier'
                ),
                'category': ConceptProperty(
                    name='category',
                    data_type='string',
                    description='Type or classification of vendor',
                    keywords=['category', 'type', 'classification', 'class'],
                    semantic_type='classification'
                ),
                'location': ConceptProperty(
                    name='location',
                    data_type='geography',
                    description='Geographical location of vendor',
                    keywords=['location', 'country', 'region', 'from', 'based in', 'located in'],
                    semantic_type='geography'
                ),
                'contact': ConceptProperty(
                    name='contact',
                    data_type='string',
                    description='Contact information',
                    keywords=['contact', 'email', 'phone', 'address'],
                    semantic_type='contact_info'
                )
            }
        )
        
        self.concepts['Product'] = DomainConcept(
            name='Product',
            description='An item that can be purchased or sold',
            synonyms=['item', 'goods', 'merchandise', 'stock', 'sku', 'article'],
            properties={
                'name': ConceptProperty(
                    name='name',
                    data_type='string',
                    required=True,
                    description='Product name or identifier',
                    keywords=['product', 'item name', 'sku', 'article'],
                    semantic_type='identifier'
                ),
                'category': ConceptProperty(
                    name='category',
                    data_type='string',
                    description='Product classification',
                    keywords=['category', 'type', 'class', 'department'],
                    semantic_type='classification'
                ),
                'price': ConceptProperty(
                    name='price',
                    data_type='currency',
                    description='Monetary value of product',
                    keywords=['price', 'cost', 'rate', 'value', 'amount'],
                    semantic_type='currency'
                )
            }
        )
        
        self.concepts['Order'] = DomainConcept(
            name='Order',
            description='A purchase request or transaction',
            synonyms=['purchase', 'transaction', 'requisition', 'po', 'purchase order'],
            properties={
                'id': ConceptProperty(
                    name='id',
                    data_type='identifier',
                    required=True,
                    description='Order identifier',
                    keywords=['order id', 'po number', 'reference', 'order number'],
                    semantic_type='identifier'
                ),
                'date': ConceptProperty(
                    name='date',
                    data_type='timestamp',
                    description='Order date/time',
                    keywords=['date', 'when', 'created', 'placed', 'time', 'timestamp'],
                    semantic_type='temporal'
                ),
                'total': ConceptProperty(
                    name='total',
                    data_type='currency',
                    description='Total order amount',
                    keywords=['total', 'amount', 'value', 'sum', 'cost', 'price'],
                    semantic_type='currency'
                ),
                'status': ConceptProperty(
                    name='status',
                    data_type='enum',
                    description='Order status',
                    keywords=['status', 'state', 'condition'],
                    semantic_type='status'
                )
            }
        )
        
        self.concepts['Customer'] = DomainConcept(
            name='Customer',
            description='A buyer or purchaser',
            synonyms=['buyer', 'client', 'purchaser', 'consumer', 'customer'],
            properties={
                'name': ConceptProperty(
                    name='name',
                    data_type='string',
                    required=True,
                    description='Customer name',
                    keywords=['customer', 'client name', 'buyer name'],
                    semantic_type='identifier'
                )
            }
        )
        
        # Define semantic relationships
        self.relationships['supplies'] = SemanticRelationship(
            name='supplies',
            source_concept='Vendor',
            target_concept='Product',
            description='Vendor provides/sells Product',
            synonyms=['provides', 'sells', 'offers', 'distributes'],
            cardinality='one-to-many'
        )
        
        self.relationships['contains'] = SemanticRelationship(
            name='contains',
            source_concept='Order',
            target_concept='Product',
            description='Order includes Product',
            synonyms=['includes', 'has', 'comprises', 'with'],
            cardinality='many-to-many'
        )
        
        self.relationships['placed_by'] = SemanticRelationship(
            name='placed_by',
            source_concept='Order',
            target_concept='Customer',
            description='Order was made by Customer',
            synonyms=['made by', 'from', 'ordered by', 'by'],
            cardinality='many-to-one'
        )
        
        self.relationships['purchased_from'] = SemanticRelationship(
            name='purchased_from',
            source_concept='Order',
            target_concept='Vendor',
            description='Order was bought from Vendor',
            synonyms=['bought from', 'from vendor', 'supplied by'],
            cardinality='many-to-one'
        )
        
        # Build synonym index
        for concept_name, concept in self.concepts.items():
            self.synonym_to_concept[concept.name.lower()] = concept_name
            for synonym in concept.synonyms:
                self.synonym_to_concept[synonym.lower()] = concept_name
        
        logger.info(f"Loaded {len(self.concepts)} domain concepts and {len(self.relationships)} relationships")
    
    def _load_custom_ontology(self):
        """Load custom ontology from configuration file"""
        ontology_file = self.config.get('ontology', {}).get('custom_file')
        if ontology_file:
            try:
                path = Path(ontology_file)
                if path.exists():
                    with open(path, 'r') as f:
                        custom_ontology = yaml.safe_load(f)
                        # Merge custom concepts
                        logger.info(f"Loaded custom ontology from {ontology_file}")
            except Exception as e:
                logger.error(f"Failed to load custom ontology: {e}")
    
    def register_column_mapping(self, mapping: ColumnMapping):
        """Register a column-to-concept mapping"""
        table = mapping.table
        if table not in self.column_mappings:
            self.column_mappings[table] = []
        self.column_mappings[table].append(mapping)
        
        # Index by keywords
        for keyword in mapping.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower not in self.keyword_to_columns:
                self.keyword_to_columns[keyword_lower] = []
            self.keyword_to_columns[keyword_lower].append(mapping)
        
        logger.debug(f"Registered mapping: {table}.{mapping.column} → {mapping.concept}.{mapping.property}")
    
    def register_schema_mappings(self, schema_snapshot: Dict[str, Any]):
        """
        Automatically register column mappings based on schema analysis
        
        This uses heuristics and pattern matching to map columns to concepts
        """
        tables = schema_snapshot.get('tables', {})
        
        for table_name, table_info in tables.items():
            columns = table_info.get('columns', [])
            
            for column in columns:
                # Handle both 'column_name' (from database) and 'name' (legacy)
                col_name = column.get('column_name', column.get('name', ''))
                col_type = column.get('data_type', column.get('type', ''))
                
                if not col_name:
                    continue
                
                # Try to find matching concept/property
                mapping = self._infer_column_mapping(table_name, col_name, col_type)
                if mapping:
                    self.register_column_mapping(mapping)
        
        logger.info(f"Registered mappings for {len(self.column_mappings)} tables")
    
    def _infer_column_mapping(self, table: str, column: str, col_type: str) -> Optional[ColumnMapping]:
        """
        Infer concept mapping for a column using pattern matching and heuristics
        """
        col_lower = column.lower()
        
        # Pattern matching for common column naming patterns
        patterns = [
            # Vendor patterns
            (r'vendor.*group|vendor.*name|vendor.*id|supplier.*name', 'Vendor', 'name', 'identifier', 
             ['vendor', 'supplier', 'seller', 'merchant', 'provider'], 0.90),
            (r'vendor.*categ|vendor.*type|supplier.*categ', 'Vendor', 'category', 'classification',
             ['vendor category', 'supplier type'], 0.85),
            (r'country|location|region', 'Vendor', 'location', 'geography',
             ['country', 'location', 'region', 'from'], 0.80),
            
            # Product patterns
            (r'product.*name|item.*name|sku|article', 'Product', 'name', 'identifier',
             ['product', 'item', 'sku'], 0.90),
            (r'product.*categ|item.*categ|product.*type', 'Product', 'category', 'classification',
             ['product category', 'item type'], 0.85),
            (r'price|cost|rate|amount', 'Product', 'price', 'currency',
             ['price', 'cost', 'amount'], 0.75),
            
            # Order patterns
            (r'order.*id|po.*number|order.*num', 'Order', 'id', 'identifier',
             ['order id', 'po number'], 0.95),
            (r'created.*on|order.*date|purchase.*date|date', 'Order', 'date', 'temporal',
             ['date', 'created', 'timestamp'], 0.85),
            (r'total.*amount|total.*value|total|net.*amount', 'Order', 'total', 'currency',
             ['total', 'amount', 'value', 'sum'], 0.90),
            (r'status|state|condition', 'Order', 'status', 'status',
             ['status', 'state'], 0.85),
        ]
        
        for pattern, concept, prop, sem_type, keywords, confidence in patterns:
            if re.search(pattern, col_lower):
                return ColumnMapping(
                    table=table,
                    column=column,
                    concept=concept,
                    property=prop,
                    semantic_type=sem_type,
                    keywords=keywords,
                    confidence=confidence,
                    description=f"Auto-mapped {column} to {concept}.{prop}",
                    data_type=col_type
                )
        
        return None
    
    def resolve_query(self, query: str, available_tables: List[str]) -> SemanticResolution:
        """
        Analyze natural language query and resolve to semantic components
        
        This is the KEY method that provides semantic understanding!
        """
        query_lower = query.lower().strip()
        
        # Extract concepts mentioned in query
        concepts = self._extract_concepts(query_lower)
        
        # Extract properties being asked for
        properties = self._extract_properties(query_lower, concepts)
        
        # Detect operations (DISTINCT, COUNT, etc.)
        operations = self._detect_operations(query_lower)
        
        # Find relevant column mappings
        column_mappings = self._find_relevant_mappings(concepts, properties, available_tables)
        
        # Detect relationships
        relationships = self._detect_relationships(query_lower, concepts)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(concepts, properties, column_mappings)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(concepts, properties, column_mappings)
        
        # Generate SQL hints
        sql_hints = self._generate_sql_hints(
            concepts, properties, operations, column_mappings, relationships
        )
        
        return SemanticResolution(
            concepts=concepts,
            properties=properties,
            operations=operations,
            column_mappings=column_mappings,
            relationships=relationships,
            confidence=confidence,
            reasoning=reasoning,
            suggested_sql_hints=sql_hints
        )
    
    def _extract_concepts(self, query: str) -> List[str]:
        """Extract domain concepts mentioned in query"""
        concepts = []
        
        # Check each word/phrase against concepts and synonyms
        words = query.split()
        for word in words:
            word_clean = word.strip('.,!?')
            if word_clean in self.synonym_to_concept:
                concept = self.synonym_to_concept[word_clean]
                if concept not in concepts:
                    concepts.append(concept)
        
        # Multi-word phrases
        for concept_name, concept in self.concepts.items():
            if concept.name.lower() in query:
                if concept_name not in concepts:
                    concepts.append(concept_name)
        
        return concepts
    
    def _extract_properties(self, query: str, concepts: List[str]) -> List[str]:
        """Extract properties being queried"""
        properties = []
        
        # Check property keywords
        for concept_name in concepts:
            if concept_name not in self.concepts:
                continue
            
            concept = self.concepts[concept_name]
            for prop_name, prop in concept.properties.items():
                # Check if any keyword matches
                for keyword in prop.keywords:
                    if keyword.lower() in query:
                        if prop_name not in properties:
                            properties.append(prop_name)
                        break
        
        return properties
    
    def _detect_operations(self, query: str) -> List[str]:
        """Detect SQL operations from query language"""
        operations = []
        
        operation_keywords = {
            'DISTINCT': ['unique', 'distinct', 'different', 'deduplicate'],
            'COUNT': ['count', 'number of', 'how many', 'total count'],
            'SUM': ['sum', 'total', 'add up'],
            'AVG': ['average', 'mean', 'avg'],
            'MAX': ['maximum', 'max', 'highest', 'largest', 'most'],
            'MIN': ['minimum', 'min', 'lowest', 'smallest', 'least'],
            'GROUP BY': ['group by', 'grouped', 'per', 'for each'],
            'ORDER BY': ['sort', 'order', 'arrange', 'sorted by'],
        }
        
        for operation, keywords in operation_keywords.items():
            if any(keyword in query for keyword in keywords):
                operations.append(operation)
        
        return operations
    
    def _find_relevant_mappings(
        self, 
        concepts: List[str], 
        properties: List[str],
        available_tables: List[str]
    ) -> List[ColumnMapping]:
        """Find column mappings relevant to the query"""
        mappings = []
        
        # Filter by available tables
        for table in available_tables:
            if table not in self.column_mappings:
                continue
            
            table_mappings = self.column_mappings[table]
            
            for mapping in table_mappings:
                # Check if mapping matches requested concepts/properties
                if mapping.concept in concepts:
                    if not properties or mapping.property in properties:
                        mappings.append(mapping)
        
        # Sort by confidence
        mappings.sort(key=lambda m: m.confidence, reverse=True)
        
        return mappings
    
    def _detect_relationships(self, query: str, concepts: List[str]) -> List[SemanticRelationship]:
        """Detect relationships between concepts in query"""
        relationships = []
        
        for rel_name, rel in self.relationships.items():
            # Check if both concepts are mentioned
            if rel.source_concept in concepts and rel.target_concept in concepts:
                # Check if relationship keywords are present
                if any(syn in query for syn in [rel.name] + rel.synonyms):
                    relationships.append(rel)
        
        return relationships
    
    def _calculate_confidence(
        self, 
        concepts: List[str], 
        properties: List[str],
        mappings: List[ColumnMapping]
    ) -> float:
        """Calculate confidence score for semantic resolution"""
        
        confidence = 0.5  # Base confidence
        
        # Boost for concepts found
        if concepts:
            confidence += 0.2 * min(len(concepts) / 2, 1.0)
        
        # Boost for properties found
        if properties:
            confidence += 0.15 * min(len(properties) / 2, 1.0)
        
        # Boost for high-confidence mappings
        if mappings:
            avg_mapping_conf = sum(m.confidence for m in mappings[:3]) / min(len(mappings), 3)
            confidence += 0.15 * avg_mapping_conf
        
        return min(confidence, 0.99)  # Cap at 99%
    
    def _generate_reasoning(
        self,
        concepts: List[str],
        properties: List[str],
        mappings: List[ColumnMapping]
    ) -> str:
        """Generate human-readable reasoning for resolution"""
        
        parts = []
        
        if concepts:
            parts.append(f"Detected concepts: {', '.join(concepts)}")
        
        if properties:
            parts.append(f"Querying properties: {', '.join(properties)}")
        
        if mappings:
            top_mapping = mappings[0]
            parts.append(
                f"Best match: {top_mapping.concept}.{top_mapping.property} "
                f"→ {top_mapping.table}.{top_mapping.column} "
                f"(confidence: {top_mapping.confidence:.0%})"
            )
        
        return "; ".join(parts) if parts else "No semantic resolution found"
    
    def _generate_sql_hints(
        self,
        concepts: List[str],
        properties: List[str],
        operations: List[str],
        mappings: List[ColumnMapping],
        relationships: List[SemanticRelationship]
    ) -> Dict[str, Any]:
        """Generate hints for SQL generation"""
        
        hints = {
            'concepts': concepts,
            'properties': properties,
            'operations': operations,
            'suggested_columns': [],
            'suggested_tables': [],
            'joins': [],
            'filters': []
        }
        
        # Add suggested columns
        for mapping in mappings[:5]:  # Top 5
            hints['suggested_columns'].append({
                'table': mapping.table,
                'column': mapping.column,
                'concept': mapping.concept,
                'property': mapping.property,
                'confidence': mapping.confidence
            })
            
            if mapping.table not in hints['suggested_tables']:
                hints['suggested_tables'].append(mapping.table)
        
        # Add join hints from relationships
        for rel in relationships:
            hints['joins'].append({
                'type': rel.name,
                'source': rel.source_concept,
                'target': rel.target_concept,
                'description': rel.description
            })
        
        return hints
    
    def get_concept_info(self, concept_name: str) -> Optional[DomainConcept]:
        """Get information about a domain concept"""
        return self.concepts.get(concept_name)
    
    def get_column_semantics(self, table: str, column: str) -> Optional[ColumnMapping]:
        """Get semantic meaning of a column"""
        if table in self.column_mappings:
            for mapping in self.column_mappings[table]:
                if mapping.column == column:
                    return mapping
        return None
    
    def search_columns_by_keyword(self, keyword: str) -> List[ColumnMapping]:
        """Search columns by semantic keyword"""
        keyword_lower = keyword.lower()
        return self.keyword_to_columns.get(keyword_lower, [])
    
    def explain_query(self, query: str, resolution: SemanticResolution) -> str:
        """Generate detailed explanation of query understanding"""
        
        explanation = f"Query Analysis: '{query}'\n\n"
        
        explanation += f"🎯 Semantic Understanding:\n"
        explanation += f"  - Concepts: {', '.join(resolution.concepts) if resolution.concepts else 'None detected'}\n"
        explanation += f"  - Properties: {', '.join(resolution.properties) if resolution.properties else 'None detected'}\n"
        explanation += f"  - Operations: {', '.join(resolution.operations) if resolution.operations else 'Basic SELECT'}\n"
        explanation += f"  - Confidence: {resolution.confidence:.1%}\n\n"
        
        explanation += f"📊 Column Mappings:\n"
        for mapping in resolution.column_mappings[:3]:
            explanation += f"  - {mapping.table}.{mapping.column} → {mapping.concept}.{mapping.property} ({mapping.confidence:.0%})\n"
        
        explanation += f"\n💡 Reasoning: {resolution.reasoning}\n"
        
        return explanation


# Global instance
_ontology_service: Optional[OntologyService] = None


def get_ontology_service(config: Dict[str, Any]) -> OntologyService:
    """Get or create ontology service singleton"""
    global _ontology_service
    
    if _ontology_service is None:
        _ontology_service = OntologyService(config)
    
    return _ontology_service


def reload_ontology_service(config: Dict[str, Any]) -> OntologyService:
    """Reload ontology service with new configuration"""
    global _ontology_service
    _ontology_service = OntologyService(config)
    return _ontology_service
