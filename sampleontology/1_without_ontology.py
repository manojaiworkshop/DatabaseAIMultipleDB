"""
Demo 1: NLP to SQL WITHOUT Ontology
====================================

This script demonstrates how NLP to SQL works WITHOUT semantic ontology.
The LLM only receives raw database schema and must guess column meanings.

Expected Accuracy: 40-60%
"""

import json
import requests
from typing import Dict, List, Any


class RealVLLMWithoutOntology:
    """Real VLLM service without ontology context"""
    
    def __init__(self, api_url: str, model: str, max_tokens: int = 2048, temperature: float = 0.7):
        self.api_url = api_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def generate_sql(self, query: str, schema: Dict[str, Any]) -> str:
        """
        Generate SQL with only raw schema (no semantic context)
        This demonstrates lower accuracy due to ambiguity
        """
        # Build minimal context (no ontology)
        context = self._build_minimal_context(query, schema)
        
        # Call real VLLM
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a SQL expert. Generate only the SQL query, no explanation."},
                        {"role": "user", "content": context}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                sql = result['choices'][0]['message']['content'].strip()
                # Clean up SQL
                sql = sql.replace('```sql', '').replace('```', '').strip()
                return sql
            else:
                return f"ERROR: VLLM returned status {response.status_code}"
        
        except requests.exceptions.RequestException as e:
            return f"ERROR: Could not connect to VLLM - {str(e)}"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _build_minimal_context(self, query: str, schema: Dict[str, Any]) -> str:
        """Build minimal context without ontology"""
        context = f"""Generate SQL for this query: {query}

Database Schema:
"""
        for table, info in schema.items():
            context += f"\nTable: {table}\n"
            context += "Columns:\n"
            for col in info['columns']:
                pk = " (PRIMARY KEY)" if col.get('primary_key') else ""
                context += f"  - {col['name']} ({col['type']}){pk}\n"
        
        context += "\nGenerate ONLY the SQL query, nothing else."
        return context


def get_raw_schema() -> Dict[str, Any]:
    """
    Returns raw database schema without semantic context
    This is what LLM sees WITHOUT ontology
    """
    return {
        "purchase_order": {
            "columns": [
                {"name": "id", "type": "integer", "primary_key": True},
                {"name": "vendorgroup", "type": "text"},
                {"name": "vendorcategory", "type": "text"},
                {"name": "country", "type": "text"},
                {"name": "totalinrpo", "type": "numeric"},
                {"name": "createdon", "type": "timestamp"},
                {"name": "status", "type": "text"}
            ]
        }
    }


def build_context_without_ontology(query: str, schema: Dict[str, Any]) -> str:
    """
    Build LLM context WITHOUT ontology
    Only includes raw schema - no semantic information
    """
    context = f"""Generate SQL for this query: {query}

Database Schema:
"""
    
    for table, info in schema.items():
        context += f"\nTable: {table}\n"
        context += "Columns:\n"
        for col in info['columns']:
            pk = " (PRIMARY KEY)" if col.get('primary_key') else ""
            context += f"  - {col['name']} ({col['type']}){pk}\n"
    
    context += "\nGenerate the SQL query."
    
    return context


def demonstrate_without_ontology():
    """Main demonstration"""
    
    print("=" * 80)
    print("DEMO 1: NLP to SQL WITHOUT ONTOLOGY (REAL VLLM)")
    print("=" * 80)
    print()
    
    # VLLM configuration (from vllm_config.yml)
    VLLM_URL = "http://10.197.246.246:8000/v1/chat/completions"
    
    print(f"🔗 Connecting to VLLM: {VLLM_URL}")
    print("❌ NO semantic context provided to LLM")
    print("❌ LLM must guess column meanings from names only")
    print("❌ Expected accuracy: 40-60%")
    print()
    
    # Initialize with REAL VLLM
    llm = RealVLLMWithoutOntology(
        api_url=VLLM_URL,
        model="/models",
        max_tokens=2048,
        temperature=0.7
    )
    schema = get_raw_schema()
    
    # Test queries
    test_queries = [
        "Find unique vendor names",
        "Show vendors from India",
        "Find high value orders",
        "Total amount by vendor"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("-" * 80)
        print(f"Query {i}: {query}")
        print("-" * 80)
        
        # Build context (without ontology)
        context = build_context_without_ontology(query, schema)
        
        print("\n📝 Context Sent to LLM:")
        print(context)
        
        # Generate SQL
        sql = llm.generate_sql(query, schema)
        
        print(f"\n🤖 Generated SQL (WITHOUT ontology):")
        print(f"   {sql}")
        
        # Analyze result
        if "ERROR" in sql:
            print(f"\n⚠️  {sql}")
        else:
            # Check correctness
            query_lower = query.lower()
            
            if "vendor name" in query_lower:
                if "vendorgroup" in sql.lower():
                    print("\n✅ CORRECT! Used 'vendorgroup'")
                elif "vendorcategory" in sql.lower():
                    print("\n❌ WRONG! Used 'vendorcategory' instead of 'vendorgroup'")
                    print("   Why? LLM guessed based on column name containing 'vendor'")
                    print("   Correct SQL: SELECT DISTINCT vendorgroup FROM purchase_order;")
                else:
                    print("\n❓ UNCERTAIN: Check if correct column was used")
            
            elif "high value" in query_lower:
                if "totalinrpo" in sql.lower():
                    print("\n✅ CORRECT! Used 'totalinrpo'")
                else:
                    print("\n❌ LIKELY WRONG! Should use 'totalinrpo' for order value")
                    print("   Correct SQL: SELECT * FROM purchase_order WHERE totalinrpo > 100000;")
            
            elif "total" in query_lower and "amount" in query_lower:
                if "totalinrpo" in sql.lower():
                    print("\n✅ CORRECT! Summing 'totalinrpo'")
                else:
                    print("\n❌ LIKELY WRONG! Should sum 'totalinrpo' column")
                    print("   Correct SQL: SELECT vendorgroup, SUM(totalinrpo) FROM purchase_order GROUP BY vendorgroup;")
            
            elif "india" in query_lower:
                if "country" in sql.lower() and "india" in sql.lower():
                    print("\n✅ PARTIALLY CORRECT! Got country filter")
                else:
                    print("\n❌ MISSING: Should filter by country = 'India'")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY: WITHOUT ONTOLOGY")
    print("=" * 80)
    print()
    print("❌ Problems Observed:")
    print("   1. Column ambiguity: 'vendor' could be vendorgroup OR vendorcategory")
    print("   2. No semantic meaning: LLM doesn't know totalinrpo = order amount")
    print("   3. Wrong column selection: Guesses based on name similarity")
    print("   4. No synonym handling: Can't handle 'supplier' instead of 'vendor'")
    print("   5. No confidence scoring: No way to tell if answer is reliable")
    print()
    print("📊 Estimated Accuracy: 40-60%")
    print()
    print("💡 Solution: Use Ontology! (See 2_with_ontology.py)")
    print()
    
    # Show context size
    sample_context = build_context_without_ontology(test_queries[0], schema)
    print(f"📦 Context Size: {len(sample_context)} characters")
    print(f"   Token estimate: ~{len(sample_context) // 4} tokens")
    print()


if __name__ == "__main__":
    demonstrate_without_ontology()
    
    print("\n" + "=" * 80)
    print("Next: Run '2_with_ontology.py' to see the improvement!")
    print("=" * 80)
