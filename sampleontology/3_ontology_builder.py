"""
Demo 3: Ontology Builder
=========================

This script shows how to programmatically build an ontology for your database.
Use this as a template to create ontologies for your own domains.
"""

import yaml
import json
from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class PropertyDefinition:
    """Define a property of a concept"""
    column: str
    semantic_type: str
    keywords: List[str]
    description: str
    data_type: str = "text"
    required: bool = False


@dataclass
class ConceptDefinition:
    """Define a domain concept"""
    name: str
    description: str
    synonyms: List[str]
    properties: Dict[str, PropertyDefinition]
    table: str = ""


@dataclass
class RelationshipDefinition:
    """Define a relationship between concepts"""
    name: str
    from_concept: str
    to_concept: str
    relationship_type: str
    description: str


class OntologyBuilder:
    """Build domain-specific ontologies programmatically"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.concepts: Dict[str, ConceptDefinition] = {}
        self.relationships: List[RelationshipDefinition] = []
        self.metadata = {
            "domain": domain,
            "version": "1.0",
            "created_by": "OntologyBuilder"
        }
    
    def add_concept(self, concept: ConceptDefinition):
        """Add a concept to the ontology"""
        self.concepts[concept.name] = concept
        print(f"✓ Added concept: {concept.name}")
    
    def add_relationship(self, relationship: RelationshipDefinition):
        """Add a relationship between concepts"""
        self.relationships.append(relationship)
        print(f"✓ Added relationship: {relationship.from_concept} -{relationship.name}-> {relationship.to_concept}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        ontology_dict = {
            "metadata": self.metadata,
            "concepts": {}
        }
        
        # Add concepts
        for concept_name, concept in self.concepts.items():
            properties = {}
            for prop_name, prop in concept.properties.items():
                properties[prop_name] = {
                    "column": prop.column,
                    "semantic_type": prop.semantic_type,
                    "keywords": prop.keywords,
                    "description": prop.description,
                    "data_type": prop.data_type,
                    "required": prop.required
                }
            
            ontology_dict["concepts"][concept_name] = {
                "description": concept.description,
                "synonyms": concept.synonyms,
                "table": concept.table,
                "properties": properties
            }
        
        # Add relationships
        ontology_dict["relationships"] = {}
        for rel in self.relationships:
            ontology_dict["relationships"][rel.name] = {
                "from": rel.from_concept,
                "to": rel.to_concept,
                "type": rel.relationship_type,
                "description": rel.description
            }
        
        return ontology_dict
    
    def save_yaml(self, filename: str):
        """Save ontology to YAML file"""
        ontology_dict = self.to_dict()
        
        with open(filename, 'w') as f:
            yaml.dump(ontology_dict, f, default_flow_style=False, indent=2)
        
        print(f"\n✅ Ontology saved to: {filename}")
    
    def save_json(self, filename: str):
        """Save ontology to JSON file"""
        ontology_dict = self.to_dict()
        
        with open(filename, 'w') as f:
            json.dump(ontology_dict, f, indent=2)
        
        print(f"✅ Ontology saved to: {filename}")
    
    def print_summary(self):
        """Print summary of ontology"""
        print("\n" + "=" * 80)
        print(f"ONTOLOGY SUMMARY: {self.domain}")
        print("=" * 80)
        print(f"\n📊 Statistics:")
        print(f"   - Concepts: {len(self.concepts)}")
        print(f"   - Relationships: {len(self.relationships)}")
        
        total_properties = sum(len(c.properties) for c in self.concepts.values())
        print(f"   - Total Properties: {total_properties}")
        
        print(f"\n🧩 Concepts:")
        for concept_name, concept in self.concepts.items():
            print(f"   - {concept_name}: {concept.description}")
            print(f"     Synonyms: {', '.join(concept.synonyms)}")
            print(f"     Properties: {len(concept.properties)}")
        
        print(f"\n🔗 Relationships:")
        for rel in self.relationships:
            print(f"   - {rel.from_concept} --{rel.name}--> {rel.to_concept}")
        print()


def build_procurement_ontology():
    """
    Example: Build ontology for procurement/purchase order domain
    """
    print("=" * 80)
    print("BUILDING PROCUREMENT DOMAIN ONTOLOGY")
    print("=" * 80)
    print()
    
    builder = OntologyBuilder("procurement")
    
    # ===== CONCEPT 1: Vendor =====
    vendor_concept = ConceptDefinition(
        name="Vendor",
        description="A supplier or seller of products/services",
        synonyms=["supplier", "seller", "merchant", "provider", "supplyer"],
        table="purchase_order",
        properties={
            "name": PropertyDefinition(
                column="vendorgroup",
                semantic_type="identifier",
                keywords=["vendor", "name", "supplier name", "seller", "merchant name"],
                description="Vendor identifier or name",
                data_type="text",
                required=True
            ),
            "category": PropertyDefinition(
                column="vendorcategory",
                semantic_type="classification",
                keywords=["category", "type", "class", "classification"],
                description="Type or category of vendor",
                data_type="text",
                required=False
            ),
            "location": PropertyDefinition(
                column="country",
                semantic_type="geography",
                keywords=["country", "location", "region", "from", "based in"],
                description="Geographical location of vendor",
                data_type="text",
                required=False
            )
        }
    )
    builder.add_concept(vendor_concept)
    
    # ===== CONCEPT 2: Order =====
    order_concept = ConceptDefinition(
        name="Order",
        description="A purchase order or transaction",
        synonyms=["purchase", "po", "purchase order", "transaction"],
        table="purchase_order",
        properties={
            "id": PropertyDefinition(
                column="id",
                semantic_type="identifier",
                keywords=["id", "order id", "po number", "reference"],
                description="Order identifier",
                data_type="integer",
                required=True
            ),
            "total": PropertyDefinition(
                column="totalinrpo",
                semantic_type="currency",
                keywords=["total", "amount", "value", "price", "cost", "sum"],
                description="Total order amount in INR",
                data_type="numeric",
                required=True
            ),
            "date": PropertyDefinition(
                column="createdon",
                semantic_type="temporal",
                keywords=["date", "created", "when", "time", "timestamp"],
                description="Order creation date/time",
                data_type="timestamp",
                required=True
            ),
            "status": PropertyDefinition(
                column="status",
                semantic_type="status",
                keywords=["status", "state", "condition"],
                description="Order status",
                data_type="text",
                required=False
            )
        }
    )
    builder.add_concept(order_concept)
    
    # ===== CONCEPT 3: Product =====
    product_concept = ConceptDefinition(
        name="Product",
        description="An item or product being purchased",
        synonyms=["item", "goods", "merchandise", "sku"],
        table="purchase_order",
        properties={
            "name": PropertyDefinition(
                column="productname",
                semantic_type="identifier",
                keywords=["product", "item", "name", "sku"],
                description="Product name or identifier",
                data_type="text",
                required=False
            ),
            "category": PropertyDefinition(
                column="productcategory",
                semantic_type="classification",
                keywords=["product category", "type", "class"],
                description="Product category or type",
                data_type="text",
                required=False
            )
        }
    )
    builder.add_concept(product_concept)
    
    # ===== RELATIONSHIPS =====
    
    # Vendor supplies Products
    builder.add_relationship(RelationshipDefinition(
        name="supplies",
        from_concept="Vendor",
        to_concept="Product",
        relationship_type="one-to-many",
        description="Vendor provides or sells products"
    ))
    
    # Order contains Products
    builder.add_relationship(RelationshipDefinition(
        name="contains",
        from_concept="Order",
        to_concept="Product",
        relationship_type="many-to-many",
        description="Order includes products"
    ))
    
    # Order from Vendor
    builder.add_relationship(RelationshipDefinition(
        name="purchased_from",
        from_concept="Order",
        to_concept="Vendor",
        relationship_type="many-to-one",
        description="Order was purchased from vendor"
    ))
    
    return builder


def build_custom_ontology_example():
    """
    Template for building your own ontology
    Customize this for your specific domain!
    """
    print("\n" + "=" * 80)
    print("BUILDING CUSTOM ONTOLOGY (Template)")
    print("=" * 80)
    print()
    
    builder = OntologyBuilder("your_domain_here")
    
    # TODO: Add your concepts here
    # Example:
    # customer_concept = ConceptDefinition(
    #     name="Customer",
    #     description="A customer who makes purchases",
    #     synonyms=["client", "buyer", "purchaser"],
    #     table="customers",
    #     properties={
    #         "name": PropertyDefinition(
    #             column="customer_name",
    #             semantic_type="identifier",
    #             keywords=["customer", "name", "client"],
    #             description="Customer name",
    #             data_type="text"
    #         )
    #     }
    # )
    # builder.add_concept(customer_concept)
    
    print("💡 Customize this template with your domain concepts!")
    print("   1. Define your concepts (entities)")
    print("   2. Define properties (attributes) for each concept")
    print("   3. Map properties to database columns")
    print("   4. Add relationships between concepts")
    print("   5. Save to YAML/JSON")
    print()
    
    return builder


def demonstrate_ontology_usage(ontology_dict: Dict[str, Any], query: str):
    """Show how the built ontology is used"""
    print("=" * 80)
    print("HOW ONTOLOGY IS USED FOR QUERY")
    print("=" * 80)
    print()
    print(f"Query: '{query}'")
    print()
    
    query_lower = query.lower()
    
    # Find matching concepts
    print("🔍 Step 1: Find matching concepts")
    matched_concepts = []
    for concept_name, concept_info in ontology_dict['concepts'].items():
        if concept_name.lower() in query_lower or any(syn in query_lower for syn in concept_info['synonyms']):
            matched_concepts.append(concept_name)
            print(f"   ✓ Found: {concept_name}")
    
    # Find matching properties
    print("\n🔍 Step 2: Find matching properties")
    matched_properties = []
    for concept_name in matched_concepts:
        concept = ontology_dict['concepts'][concept_name]
        for prop_name, prop_info in concept['properties'].items():
            if any(kw in query_lower for kw in prop_info['keywords']):
                matched_properties.append((concept_name, prop_name, prop_info['column']))
                print(f"   ✓ {concept_name}.{prop_name} → {prop_info['column']}")
    
    # Generate SQL hint
    print("\n💡 Step 3: Generate SQL hint")
    if matched_properties:
        columns = [prop[2] for prop in matched_properties]
        if "unique" in query_lower or "distinct" in query_lower:
            sql_hint = f"SELECT DISTINCT {columns[0]} FROM purchase_order"
        else:
            sql_hint = f"SELECT {', '.join(columns)} FROM purchase_order"
        print(f"   Suggested: {sql_hint}")
    print()


if __name__ == "__main__":
    # Build procurement ontology
    builder = build_procurement_ontology()
    
    # Print summary
    builder.print_summary()
    
    # Save to files
    print("=" * 80)
    print("SAVING ONTOLOGY")
    print("=" * 80)
    print()
    builder.save_yaml("sample_ontology.yml")
    builder.save_json("sample_ontology.json")
    
    # Demonstrate usage
    print()
    ontology_dict = builder.to_dict()
    demonstrate_ontology_usage(ontology_dict, "Find unique vendor names from India")
    
    # Show template for custom ontology
    custom_builder = build_custom_ontology_example()
    
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. ✓ Review generated sample_ontology.yml")
    print("2. ✓ Customize for your domain using build_custom_ontology_example()")
    print("3. ✓ Load ontology in your application")
    print("4. ✓ Use ontology to enhance NLP to SQL conversion")
    print("5. ✓ Test with real queries and refine")
    print()
