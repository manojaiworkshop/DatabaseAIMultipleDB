# W3C OWL Export Feature Guide

## Overview

DatabaseAI automatically exports generated ontologies to **W3C OWL (Web Ontology Language)** format, the international standard for semantic ontologies.

## What is OWL?

**OWL (Web Ontology Language)** is a W3C standard for representing rich and complex knowledge about things, groups of things, and relations between things.

### Why OWL?
- ✅ **Interoperability**: Use with any OWL-compatible tool
- ✅ **Semantic Reasoning**: Enable automatic inference
- ✅ **Knowledge Sharing**: Exchange ontologies with other systems
- ✅ **Standardization**: Based on RDF/XML, widely supported
- ✅ **Tool Ecosystem**: Protégé, TopBraid, Jena, RDFLib, etc.

## Automatic Export

### When Ontologies are Exported

Every time a dynamic ontology is generated, it's automatically exported to:
```
ontology/{session_id}_ontology_{timestamp}.owl
```

**Triggers:**
1. First database connection (generates initial ontology)
2. Schema changes detection
3. Manual regeneration request
4. New user session with different database

### File Naming

Format: `{session_id}_ontology_{YYYYMMDD_HHMMSS}.owl`

Examples:
- `conn_abc12345_ontology_20251028_155630.owl`
- `user_john_ontology_20251028_160245.owl`
- `conn_default_ontology_20251028_161000.owl`

## OWL Structure

### 1. Ontology Header
```xml
<owl:Ontology rdf:about="">
  <rdfs:label>DatabaseAI Dynamic Ontology - conn_abc12345</rdfs:label>
  <rdfs:comment>Auto-generated ontology for database schema...</rdfs:comment>
  <dc:created rdf:datatype="xsd:dateTime">2025-10-28T15:56:30Z</dc:created>
  <dc:creator>DatabaseAI Dynamic Ontology Generator</dc:creator>
</owl:Ontology>
```

### 2. OWL Classes (Concepts)
```xml
<owl:Class rdf:about="http://databaseai.io/ontology/conn_abc12345#Vendor">
  <rdfs:label>Vendor</rdfs:label>
  <rdfs:comment>Represents vendor/supplier information</rdfs:comment>
  <rdfs:seeAlso>Database tables: purchase_order, vendor_master</rdfs:seeAlso>
  <databaseai:confidence rdf:datatype="xsd:float">0.95</databaseai:confidence>
</owl:Class>
```

### 3. Datatype Properties (Attributes)
```xml
<owl:DatatypeProperty rdf:about="http://databaseai.io/ontology/conn_abc12345#Vendor_name">
  <rdfs:label>Vendor.name</rdfs:label>
  <rdfs:comment>Vendor identifier or company name</rdfs:comment>
  <rdfs:domain rdf:resource="http://databaseai.io/ontology/conn_abc12345#Vendor"/>
  <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
  <databaseai:databaseMapping>purchase_order.vendorgroup</databaseai:databaseMapping>
  <databaseai:confidence rdf:datatype="xsd:float">0.90</databaseai:confidence>
  <skos:example>ACME Corp, TechSupply Inc, Global Vendors</skos:example>
</owl:DatatypeProperty>
```

### 4. Object Properties (Relationships)
```xml
<owl:ObjectProperty rdf:about="http://databaseai.io/ontology/conn_abc12345#purchases">
  <rdfs:label>purchases</rdfs:label>
  <rdfs:domain rdf:resource="http://databaseai.io/ontology/conn_abc12345#Customer"/>
  <rdfs:range rdf:resource="http://databaseai.io/ontology/conn_abc12345#Product"/>
  <databaseai:viaTables>orders, order_items</databaseai:viaTables>
  <databaseai:confidence rdf:datatype="xsd:float">0.85</databaseai:confidence>
</owl:ObjectProperty>
```

## Using OWL Files

### 1. Protégé (Desktop Application)

**Best for**: Ontology visualization, editing, reasoning

```bash
# Download from https://protege.stanford.edu/
# Then:
1. Open Protégé
2. File → Open
3. Select your .owl file
4. Explore Classes, Object Properties, Data Properties tabs
```

**Features:**
- Visual class hierarchy
- Property matrix
- Reasoning (infer new facts)
- SPARQL queries
- Export to various formats

### 2. Python (RDFLib)

```python
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, OWL

# Load ontology
g = Graph()
g.parse("ontology/conn_abc12345_ontology_20251028_155630.owl", format="xml")

# Query all classes
print("=== OWL Classes ===")
for cls in g.subjects(RDF.type, OWL.Class):
    label = g.value(cls, RDFS.label)
    comment = g.value(cls, RDFS.comment)
    print(f"{label}: {comment}")

# Query all properties
print("\n=== Properties ===")
for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
    label = g.value(prop, RDFS.label)
    domain = g.value(prop, RDFS.domain)
    print(f"Property: {label}, Domain: {domain}")

# SPARQL Query
query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX databaseai: <http://databaseai.io/ontology/>
    
    SELECT ?concept ?property ?mapping ?confidence
    WHERE {
        ?property a owl:DatatypeProperty .
        ?property rdfs:domain ?concept .
        ?property databaseai:databaseMapping ?mapping .
        ?property databaseai:confidence ?confidence .
        FILTER (?confidence > 0.8)
    }
    ORDER BY DESC(?confidence)
"""

results = g.query(query)
for row in results:
    print(f"Concept: {row.concept}, Property: {row.property}")
    print(f"  DB Mapping: {row.mapping}, Confidence: {row.confidence}")
```

### 3. Java (Apache Jena)

```java
import org.apache.jena.rdf.model.*;
import org.apache.jena.vocabulary.*;

public class OntologyLoader {
    public static void main(String[] args) {
        // Load OWL file
        Model model = ModelFactory.createDefaultModel();
        model.read("ontology/conn_abc12345_ontology_20251028_155630.owl");
        
        // List all classes
        System.out.println("=== OWL Classes ===");
        ResIterator classes = model.listSubjectsWithProperty(RDF.type, OWL.Class);
        while (classes.hasNext()) {
            Resource cls = classes.next();
            String label = cls.getProperty(RDFS.label).getString();
            System.out.println("Class: " + label);
        }
        
        // SPARQL Query
        String queryString = """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?class ?label ?comment
            WHERE {
                ?class a owl:Class .
                ?class rdfs:label ?label .
                ?class rdfs:comment ?comment .
            }
        """;
        
        Query query = QueryFactory.create(queryString);
        QueryExecution qexec = QueryExecutionFactory.create(query, model);
        ResultSet results = qexec.execSelect();
        ResultSetFormatter.out(System.out, results, query);
        qexec.close();
    }
}
```

### 4. JavaScript (rdflib.js)

```javascript
const $rdf = require('rdflib');
const fs = require('fs');

// Load OWL file
const store = $rdf.graph();
const fetcher = new $rdf.Fetcher(store);

fs.readFile('ontology/conn_abc12345_ontology_20251028_155630.owl', 'utf8', (err, data) => {
    if (err) throw err;
    
    $rdf.parse(data, store, 'http://example.org/', 'application/rdf+xml');
    
    // Query classes
    const OWL = $rdf.Namespace('http://www.w3.org/2002/07/owl#');
    const RDFS = $rdf.Namespace('http://www.w3.org/2000/01/rdf-schema#');
    
    const classes = store.each(null, $rdf.sym('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), OWL('Class'));
    
    console.log('=== OWL Classes ===');
    classes.forEach(cls => {
        const label = store.any(cls, RDFS('label'));
        console.log(`Class: ${label}`);
    });
});
```

## API Endpoints (Optional)

### Get Ontology Export Path
```http
GET /api/v1/ontology/export/{session_id}
```

Response:
```json
{
  "success": true,
  "session_id": "conn_abc12345",
  "owl_path": "ontology/conn_abc12345_ontology_20251028_155630.owl",
  "exists": true,
  "size_bytes": 45320,
  "generated_at": "2025-10-28T15:56:30Z"
}
```

### Download OWL File
```http
GET /api/v1/ontology/download/{session_id}
```

Returns: OWL file download

### List All Exports
```http
GET /api/v1/ontology/list
```

Response:
```json
{
  "success": true,
  "ontologies": [
    {
      "filename": "conn_abc12345_ontology_20251028_155630.owl",
      "session_id": "conn_abc12345",
      "timestamp": "2025-10-28T15:56:30Z",
      "size_bytes": 45320
    }
  ]
}
```

## Advanced Usage

### Ontology Reasoning

Use reasoners to infer new facts:

```python
from owlready2 import *

# Load ontology
onto = get_ontology("file://ontology/conn_abc12345_ontology_20251028_155630.owl").load()

# Run reasoner
with onto:
    sync_reasoner_pellet()  # Or HermiT, Fact++

# Check inferred classes
for individual in onto.individuals():
    print(f"{individual} is a {individual.__class__}")
```

### Ontology Merging

Combine multiple ontologies:

```python
from rdflib import Graph

# Load multiple ontologies
g1 = Graph().parse("ontology/session1_ontology_20251028_155630.owl")
g2 = Graph().parse("ontology/session2_ontology_20251028_160000.owl")

# Merge
merged = g1 + g2

# Save merged ontology
merged.serialize("ontology/merged_ontology.owl", format="xml")
```

### SPARQL Endpoint

Serve ontologies via SPARQL:

```python
from flask import Flask
from rdflib import Graph
from rdflib.plugins.sparql import prepareQuery

app = Flask(__name__)
g = Graph().parse("ontology/conn_abc12345_ontology_20251028_155630.owl")

@app.route('/sparql', methods=['POST'])
def sparql_endpoint():
    query = request.form['query']
    results = g.query(query)
    return results.serialize(format='json')
```

## Configuration

Enable/disable OWL export in `app_config.yml`:

```yaml
ontology:
  dynamic_generation:
    enabled: true
    export_owl: true  # Set to false to disable export
    export_directory: "ontology"  # Custom directory
```

## Benefits

### 1. **Portability**
- Share ontologies between systems
- Version control with Git
- Backup and restore easily

### 2. **Integration**
- Import into knowledge graphs (Neo4j, Stardog)
- Use with semantic reasoners
- Connect to linked data platforms

### 3. **Analysis**
- Visualize in Protégé or WebVOWL
- Run SPARQL queries
- Perform consistency checking

### 4. **Documentation**
- Self-documenting database schemas
- Human-readable semantic model
- Onboard new developers faster

### 5. **AI Enhancement**
- Train ML models on ontologies
- Improve NLP with domain knowledge
- Enable smarter query understanding

## Troubleshooting

### File Not Generated
- Check logs: `backend.app.services.dynamic_ontology`
- Ensure `ontology/` directory exists
- Verify permissions

### Invalid OWL
- Check for special characters in table/column names
- Validate with Protégé or online validators
- Review logs for XML generation errors

### Large File Size
- Limit number of concepts/properties in config
- Filter out system tables
- Use ontology compression tools

## Resources

- **W3C OWL 2**: https://www.w3.org/TR/owl2-overview/
- **Protégé**: https://protege.stanford.edu/
- **RDFLib**: https://rdflib.readthedocs.io/
- **Apache Jena**: https://jena.apache.org/
- **OWLReady2**: https://owlready2.readthedocs.io/
- **WebVOWL**: http://www.visualdataweb.de/webvowl/

## Example: Complete Workflow

```bash
# 1. Connect to database (triggers ontology generation)
curl -X POST http://localhost:8088/api/v1/database/connect \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "pass"
  }'

# 2. Make a query (ontology is used)
curl -X POST http://localhost:8088/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show all unique vendor names"}'

# 3. Check ontology was exported
ls -la ontology/

# 4. Load in Python
python3 << EOF
from rdflib import Graph
g = Graph()
g.parse("ontology/conn_abc12345_ontology_20251028_155630.owl")
print(f"Loaded {len(g)} triples")
EOF

# 5. Open in Protégé
protege ontology/conn_abc12345_ontology_20251028_155630.owl
```

---

**🦉 Your database schemas are now semantic web ready!**
