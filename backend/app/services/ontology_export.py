"""
Ontology Export to W3C OWL Format
Exports generated ontologies to OWL/RDF format for interoperability
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

logger = logging.getLogger(__name__)


class OWLExporter:
    """
    Export ontology to W3C OWL (Web Ontology Language) format
    
    OWL is the standard format for ontologies, enabling:
    - Interoperability with other tools (Protégé, TopBraid, etc.)
    - Semantic reasoning
    - Knowledge sharing
    - Ontology visualization
    """
    
    def __init__(self, output_dir: str = "ontology"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"OWL Exporter initialized: {output_dir}")
    
    def export_to_owl(
        self, 
        ontology: Dict[str, Any], 
        filename: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Export ontology to OWL/RDF format
        
        Args:
            ontology: Dynamic ontology dict
            filename: Custom filename (without extension)
            session_id: User session ID
            
        Returns:
            Path to saved OWL file
        """
        # Generate filename
        if not filename:
            session_id = session_id or ontology.get('connection_id', 'default')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{session_id}_ontology_{timestamp}"
        
        filepath = os.path.join(self.output_dir, f"{filename}.owl")
        
        # Build OWL/RDF XML
        owl_content = self._build_owl_document(ontology)
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(owl_content)
        
        logger.info(f"✅ Ontology exported to OWL: {filepath}")
        return filepath
    
    def _build_owl_document(self, ontology: Dict[str, Any]) -> str:
        """Build OWL/RDF XML document"""
        
        # Namespaces
        ns_rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        ns_rdfs = "http://www.w3.org/2000/01/rdf-schema#"
        ns_owl = "http://www.w3.org/2002/07/owl#"
        ns_xsd = "http://www.w3.org/2001/XMLSchema#"
        base_uri = f"http://databaseai.io/ontology/{ontology.get('connection_id', 'default')}#"
        
        # Root element
        rdf = Element('rdf:RDF', {
            'xmlns:rdf': ns_rdf,
            'xmlns:rdfs': ns_rdfs,
            'xmlns:owl': ns_owl,
            'xmlns:xsd': ns_xsd,
            'xmlns': base_uri,
            'xml:base': base_uri
        })
        
        # Ontology header
        ont_element = SubElement(rdf, 'owl:Ontology', {'rdf:about': ''})
        
        # Metadata
        metadata = ontology.get('metadata', {})
        
        title = SubElement(ont_element, 'rdfs:label')
        title.text = f"DatabaseAI Dynamic Ontology - {ontology.get('connection_id', 'Unknown')}"
        
        comment = SubElement(ont_element, 'rdfs:comment')
        comment.text = (
            f"Auto-generated ontology for database schema. "
            f"Generated: {metadata.get('generated_at', 'Unknown')}. "
            f"Tables: {metadata.get('table_count', 0)}, "
            f"Concepts: {metadata.get('concept_count', 0)}, "
            f"Properties: {metadata.get('property_count', 0)}"
        )
        
        created = SubElement(ont_element, '{http://purl.org/dc/terms/}created', {
            'rdf:datatype': ns_xsd + 'dateTime'
        })
        created.text = metadata.get('generated_at', datetime.now().isoformat())
        
        creator = SubElement(ont_element, '{http://purl.org/dc/terms/}creator')
        creator.text = 'DatabaseAI Dynamic Ontology Generator'
        
        # Export concepts as OWL Classes
        concepts = ontology.get('concepts', [])
        for concept in concepts:
            self._add_concept_class(rdf, concept, base_uri)
        
        # Export properties as OWL ObjectProperties and DatatypeProperties
        properties = ontology.get('properties', [])
        for prop in properties:
            self._add_property(rdf, prop, base_uri, concepts)
        
        # Export relationships as OWL ObjectProperties
        relationships = ontology.get('relationships', [])
        for rel in relationships:
            self._add_relationship(rdf, rel, base_uri)
        
        # Pretty print XML
        return self._prettify_xml(rdf)
    
    def _add_concept_class(self, rdf: Element, concept: Dict[str, Any], base_uri: str):
        """Add an OWL Class for a concept"""
        class_uri = base_uri + concept['name'].replace(' ', '_')
        
        owl_class = SubElement(rdf, 'owl:Class', {'rdf:about': class_uri})
        
        # Label
        label = SubElement(owl_class, 'rdfs:label')
        label.text = concept['name']
        
        # Comment (description)
        if concept.get('description'):
            comment = SubElement(owl_class, 'rdfs:comment')
            comment.text = concept['description']
        
        # Custom annotations
        if concept.get('tables'):
            tables_anno = SubElement(owl_class, 'rdfs:seeAlso')
            tables_anno.text = f"Database tables: {', '.join(concept['tables'])}"
        
        if concept.get('confidence'):
            conf_anno = SubElement(owl_class, '{http://databaseai.io/ontology/}confidence', {
                'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#float'
            })
            conf_anno.text = str(concept['confidence'])
    
    def _add_property(self, rdf: Element, prop: Dict[str, Any], base_uri: str, concepts: list):
        """Add an OWL Property (DatatypeProperty)"""
        prop_uri = base_uri + f"{prop['concept']}_{prop['property_name']}".replace(' ', '_')
        
        # Most database columns are DatatypeProperties (point to literals)
        owl_prop = SubElement(rdf, 'owl:DatatypeProperty', {'rdf:about': prop_uri})
        
        # Label
        label = SubElement(owl_prop, 'rdfs:label')
        label.text = f"{prop['concept']}.{prop['property_name']}"
        
        # Comment (semantic meaning)
        if prop.get('semantic_meaning'):
            comment = SubElement(owl_prop, 'rdfs:comment')
            comment.text = prop['semantic_meaning']
        
        # Domain (which concept this property belongs to)
        concept_uri = base_uri + prop['concept'].replace(' ', '_')
        domain = SubElement(owl_prop, 'rdfs:domain', {'rdf:resource': concept_uri})
        
        # Range (data type)
        range_type = self._map_db_type_to_xsd(prop.get('data_type', 'string'))
        range_elem = SubElement(owl_prop, 'rdfs:range', {'rdf:resource': range_type})
        
        # Custom annotations
        db_mapping = SubElement(owl_prop, '{http://databaseai.io/ontology/}databaseMapping')
        db_mapping.text = f"{prop['table']}.{prop['column']}"
        
        if prop.get('confidence'):
            conf_anno = SubElement(owl_prop, '{http://databaseai.io/ontology/}confidence', {
                'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#float'
            })
            conf_anno.text = str(prop['confidence'])
        
        # Examples
        if prop.get('examples'):
            examples_anno = SubElement(owl_prop, '{http://www.w3.org/2004/02/skos/core#}example')
            examples_anno.text = ', '.join(str(ex) for ex in prop['examples'][:3])
    
    def _add_relationship(self, rdf: Element, rel: Dict[str, Any], base_uri: str):
        """Add an OWL ObjectProperty for a relationship"""
        rel_type = rel['relationship_type'].replace(' ', '_')
        rel_uri = base_uri + rel_type
        
        owl_prop = SubElement(rdf, 'owl:ObjectProperty', {'rdf:about': rel_uri})
        
        # Label
        label = SubElement(owl_prop, 'rdfs:label')
        label.text = rel['relationship_type']
        
        # Domain (from concept)
        from_concept_uri = base_uri + rel['from_concept'].replace(' ', '_')
        domain = SubElement(owl_prop, 'rdfs:domain', {'rdf:resource': from_concept_uri})
        
        # Range (to concept)
        to_concept_uri = base_uri + rel['to_concept'].replace(' ', '_')
        range_elem = SubElement(owl_prop, 'rdfs:range', {'rdf:resource': to_concept_uri})
        
        # Custom annotations
        if rel.get('via_tables'):
            via_anno = SubElement(owl_prop, '{http://databaseai.io/ontology/}viaTables')
            via_anno.text = ', '.join(rel['via_tables'])
        
        if rel.get('confidence'):
            conf_anno = SubElement(owl_prop, '{http://databaseai.io/ontology/}confidence', {
                'rdf:datatype': 'http://www.w3.org/2001/XMLSchema#float'
            })
            conf_anno.text = str(rel['confidence'])
    
    def _map_db_type_to_xsd(self, db_type: str) -> str:
        """Map database types to XSD datatypes"""
        db_type_lower = db_type.lower()
        
        xsd_base = "http://www.w3.org/2001/XMLSchema#"
        
        type_mapping = {
            'integer': 'integer',
            'int': 'integer',
            'bigint': 'long',
            'smallint': 'short',
            'numeric': 'decimal',
            'decimal': 'decimal',
            'real': 'float',
            'double': 'double',
            'float': 'float',
            'boolean': 'boolean',
            'bool': 'boolean',
            'date': 'date',
            'time': 'time',
            'timestamp': 'dateTime',
            'datetime': 'dateTime',
            'varchar': 'string',
            'char': 'string',
            'text': 'string',
            'string': 'string',
        }
        
        for db_key, xsd_type in type_mapping.items():
            if db_key in db_type_lower:
                return xsd_base + xsd_type
        
        return xsd_base + 'string'  # Default
    
    def _prettify_xml(self, elem: Element) -> str:
        """Return a pretty-printed XML string"""
        rough_string = tostring(elem, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    def list_exported_ontologies(self) -> list:
        """List all exported ontology files (OWL and YAML)"""
        if not os.path.exists(self.output_dir):
            return []
        
        files = [
            f for f in os.listdir(self.output_dir) 
            if f.endswith('.owl') or f.endswith('.yml') or f.endswith('.yaml')
        ]
        return sorted(files, reverse=True)  # Most recent first
    
    def get_ontology_path(self, session_id: str) -> Optional[str]:
        """Get path to most recent ontology for a session"""
        files = self.list_exported_ontologies()
        for f in files:
            if f.startswith(session_id):
                return os.path.join(self.output_dir, f)
        return None


# Singleton instance
_owl_exporter = None

def get_owl_exporter(output_dir: str = "ontology") -> OWLExporter:
    """Get or create OWL exporter"""
    global _owl_exporter
    if _owl_exporter is None:
        _owl_exporter = OWLExporter(output_dir)
    return _owl_exporter
