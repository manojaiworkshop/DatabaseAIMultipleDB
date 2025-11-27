# Ontology Export Directory

This directory contains automatically generated ontologies in W3C OWL format.

## About OWL (Web Ontology Language)

OWL is the W3C standard for representing ontologies. These files can be:
- Opened in ontology editors (Protégé, TopBraid Composer)
- Used for semantic reasoning
- Integrated with semantic web applications
- Visualized using ontology visualization tools

## File Naming Convention

Files are named: `{session_id}_ontology_{timestamp}.owl`

Example: `conn_abc12345_ontology_20251028_155630.owl`

## What's Inside

Each OWL file contains:

### 1. **OWL Classes** (Domain Concepts)
- Business entities identified from your database
- Examples: Customer, Order, Product, Vendor
- Includes descriptions and confidence scores

### 2. **OWL Properties** (Attributes)
- DatatypeProperties: Map database columns to concept attributes
- ObjectProperties: Relationships between concepts
- Includes semantic meanings and database mappings

### 3. **Relationships**
- How concepts relate to each other
- Examples: "Order contains Product", "Customer places Order"
- Derived from foreign keys and semantic analysis

### 4. **Metadata**
- Generation timestamp
- Source database information
- Concept/property statistics

## Using the OWL Files

### With Protégé (Desktop)
1. Download Protégé: https://protege.stanford.edu/
2. Open File → Open
3. Select the .owl file
4. Explore classes, properties, and relationships

### With TopBraid Composer
1. Import OWL file
2. Visualize ontology graph
3. Run SPARQL queries
4. Perform semantic reasoning

### Programmatically (Python)
```python
from rdflib import Graph

# Load OWL file
g = Graph()
g.parse("conn_abc12345_ontology_20251028_155630.owl", format="xml")

# Query with SPARQL
query = """
    SELECT ?concept ?description
    WHERE {
        ?concept a owl:Class .
        ?concept rdfs:comment ?description .
    }
"""
results = g.query(query)
```

### With RDF Libraries (Java)
```java
import org.apache.jena.rdf.model.*;

Model model = ModelFactory.createDefaultModel();
model.read("conn_abc12345_ontology_20251028_155630.owl");

// Query the model
// ...
```

## Ontology Features

### Semantic Annotations
- **rdfs:label** - Human-readable names
- **rdfs:comment** - Descriptions and explanations
- **rdfs:seeAlso** - Links to database tables
- **custom:confidence** - AI confidence scores (0.0-1.0)
- **custom:databaseMapping** - Table.column mappings
- **skos:example** - Sample values

### Namespaces
- **rdf**: http://www.w3.org/1999/02/22-rdf-syntax-ns#
- **rdfs**: http://www.w3.org/2000/01/rdf-schema#
- **owl**: http://www.w3.org/2002/07/owl#
- **xsd**: http://www.w3.org/2001/XMLSchema#
- **base**: http://databaseai.io/ontology/{session_id}#

## File Management

### Cleanup
Old ontology files can be safely deleted. The system will regenerate them as needed.

### Versioning
Each generation creates a new timestamped file. Keep the most recent for each session.

### Backup
OWL files are self-contained. Copy them to backup important ontologies.

## Integration with DatabaseAI

The ontologies are automatically generated when:
1. You connect to a database (first query)
2. The schema changes significantly
3. You force regeneration via API

They are used to:
- Improve SQL query generation accuracy
- Map natural language to database columns
- Discover semantic relationships
- Provide intelligent query suggestions

## Further Reading

- W3C OWL 2 Specification: https://www.w3.org/TR/owl2-overview/
- OWL Tutorial: https://www.w3.org/TR/owl-guide/
- Protégé Documentation: https://protegewiki.stanford.edu/
- RDF Primer: https://www.w3.org/TR/rdf-primer/
