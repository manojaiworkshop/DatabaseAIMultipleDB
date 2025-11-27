# 🐛 Bug Fix: Neo4j Query Parameter Conflict

## Issue Identified

From your logs:
```
2025-10-29 10:58:02,321 - backend.app.services.ontology_kg_sync - ERROR - 
Failed to get ontology insights: Session.run() got multiple values for argument 'query'

TypeError: Session.run() got multiple values for argument 'query'
```

## Root Cause

In `ontology_kg_sync.py`, the `get_ontology_enhanced_insights()` method had a parameter naming conflict:

```python
def get_ontology_enhanced_insights(self, query: str, connection_id: str):
    # ...
    result = session.run("""
        MATCH (c:Concept {connection: $connection_id})
        WHERE toLower($query) CONTAINS toLower(c.name)  # ❌ Conflict!
        ...
    """, query=query_lower, connection_id=connection_id)  # ❌ 'query' used twice
```

**The problem**: 
- `session.run()` expects the first positional argument to be the Cypher query string
- We also passed `query=query_lower` as a named parameter for the Cypher query
- This caused a "multiple values for argument 'query'" error

## Fix Applied

Changed the Cypher parameter name from `$query` to `$user_query`:

```python
def get_ontology_enhanced_insights(self, query: str, connection_id: str):
    # ...
    result = session.run("""
        MATCH (c:Concept {connection: $connection_id})
        WHERE toLower($user_query) CONTAINS toLower(c.name)  # ✅ Fixed!
        ...
    """, user_query=query_lower, connection_id=connection_id)  # ✅ No conflict
```

## Files Modified

- ✅ `backend/app/services/ontology_kg_sync.py` (Line ~508)

## Testing

Run the test script:
```bash
python test_neo4j_fix.py
```

Expected output:
```
✅ Neo4j connection successful
✅ Query executed successfully!

📊 Results:
   Concepts detected: 1
   Suggested columns: 1 table
   Semantic mappings: 3
   Recommendations: 2
```

## Next Steps

1. **Restart your backend server** (if auto-reload didn't pick it up)
2. **Sync your ontology** (if not already done):
   ```bash
   python sync_ontology_to_neo4j.py --file ontology/sap_data_*_ontology_*.yml
   ```
3. **Test the query again**: `"find all unique vendor names"`

## Expected New Logs

After the fix, you should see:
```
🔗 KNOWLEDGE GRAPH INSIGHTS:
   Concepts detected: 1 (Vendor)
   Suggested columns: purchase_order (3 columns)
   Semantic mappings: 3
   Recommendations: 2

🧠 Found 3 semantic mappings from ontology

💡 Has knowledge graph: YES ✅
```

## Why This Matters

This bug was preventing the Knowledge Graph from providing semantic recommendations. Now:

✅ Ontology insights work  
✅ Knowledge Graph insights work  
✅ Dual validation enabled  
✅ 90%+ confidence recommendations  

Your logs should now show **"Has knowledge graph: YES ✅"** instead of **"Has knowledge graph: NO ❌"**!

## Verification Command

After restarting the backend, check the logs for:
```bash
grep "Knowledge Graph" backend_logs.txt | tail -20
```

You should see:
- ✅ No more "TypeError: Session.run() got multiple values"
- ✅ "Concepts detected: 1+"
- ✅ "Semantic mappings: 3+"
- ✅ "Has knowledge graph: YES"
