# SQL Agent Query Flow - Complete Trace 🔍

## Overview
This document explains how a natural language query flows through the SQL Agent, using Ontology and Knowledge Graph to generate accurate SQL.

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  USER QUERY: "find all network device"                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 0: Entry Point (routes/api.py)                            │
│  ─────────────────────────────────────────────────────────────  │
│  • Receives NLP query from frontend                             │
│  • Gets database snapshot (5 tables)                            │
│  • Creates AgentState with schema_snapshot                      │
│  • Calls sql_agent.query()                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Schema Normalization (sql_agent.py)                    │
│  ─────────────────────────────────────────────────────────────  │
│  INPUT:  schema_snapshot with 'tables' as LIST                  │
│          [{'table_name': 'device_status', columns: [...]}, ...]  │
│                                                                  │
│  PROCESS: _normalize_schema_snapshot()                          │
│           - Handles both list and dict formats                   │
│           - Converts to consistent dict format                   │
│           - Returns: {'tables': {...}}                          │
│                                                                  │
│  OUTPUT:  schema_snapshot_normalized                            │
│           {                                                      │
│             'tables': {                                          │
│               'device_status': {...},                            │
│               'hardware_info': {...},                            │
│               'maintenance_logs': {...},                         │
│               'network_alerts': {...},                           │
│               'network_devices': {...}                           │
│             }                                                    │
│           }                                                      │
│                                                                  │
│  LOGS:   ✅ Schema normalized: 5 tables                          │
│          📋 Tables: device_status, hardware_info, ...           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Ontology Semantic Resolution (ontology.py)             │
│  ─────────────────────────────────────────────────────────────  │
│  PURPOSE: Map natural language concepts to database columns     │
│                                                                  │
│  2.1 Register Schema Mappings                                   │
│      • Loads ontology YAML file (if exists)                     │
│      • Maps concepts → tables → columns                         │
│      • Creates column_mappings dict                             │
│                                                                  │
│  2.2 Resolve Query Semantics                                    │
│      INPUT:  "find all network device"                          │
│      PROCESS:                                                    │
│        - Extracts keywords: ["network", "device"]               │
│        - Searches ontology for matching concepts                │
│        - Finds: NetworkDevice concept                           │
│        - Maps to table: network_devices                         │
│        - Identifies relevant columns:                           │
│          * device_id (identifier)                               │
│          * device_name (name property)                          │
│          * device_type (classification)                         │
│          * ip_address (network property)                        │
│                                                                  │
│      OUTPUT: SemanticResolution                                 │
│        {                                                         │
│          "confidence": 0.95,                                     │
│          "reasoning": "Query maps to NetworkDevice concept",    │
│          "column_mappings": [                                    │
│            {                                                     │
│              "table": "network_devices",                         │
│              "column": "device_name",                            │
│              "concept": "NetworkDevice",                         │
│              "property": "name",                                 │
│              "confidence": 0.95                                  │
│            },                                                    │
│            ...                                                   │
│          ]                                                       │
│        }                                                         │
│                                                                  │
│  2.3 Build Ontology Context for LLM                             │
│      CONTEXT TEXT:                                               │
│      "🧠 ===ONTOLOGY SEMANTIC GUIDANCE===                       │
│       Query Understanding: User wants NetworkDevice data        │
│       Confidence: 95%                                            │
│                                                                  │
│       ✅ RECOMMENDED COLUMNS TO USE:                             │
│       1. USE: network_devices.device_name                        │
│          Reason: Maps to NetworkDevice.name                      │
│          Confidence: 95%                                         │
│       2. USE: network_devices.device_type                        │
│          Reason: Maps to NetworkDevice.type                      │
│          Confidence: 90%"                                        │
│                                                                  │
│  LOGS:   ✅ Ontology is ENABLED                                  │
│          📝 Registering schema mappings...                       │
│          🧠 Registered 54 column mappings                        │
│          🔍 Resolving query: 'find all network device'          │
│          ✅ Semantic resolution found!                           │
│          🎯 Recommendations:                                     │
│             1. network_devices.device_name (95%)                 │
│             2. network_devices.device_type (90%)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Knowledge Graph Insights (knowledge_graph.py)          │
│  ─────────────────────────────────────────────────────────────  │
│  PURPOSE: Provide relationship context and join suggestions     │
│                                                                  │
│  3.1 Extract Query Keywords                                     │
│      • Tokenizes: "find all network device"                     │
│      • Keywords: ["network", "device"]                          │
│                                                                  │
│  3.2 Query Neo4j Graph Database                                 │
│      CYPHER QUERY:                                               │
│      MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)                  │
│      WHERE t.name CONTAINS 'network'                            │
│         OR c.name CONTAINS 'device'                             │
│      RETURN t, c                                                 │
│                                                                  │
│      RESULTS:                                                    │
│      • Table: network_devices (15 columns)                      │
│      • Table: network_alerts (13 columns, references devices)   │
│      • Table: device_status (5 columns, references devices)     │
│                                                                  │
│  3.3 Rank Columns by Relevance                                  │
│      SCORING:                                                    │
│      • Exact match: device_name (score: 1.0)                    │
│      • Contains keyword: device_type (score: 0.8)               │
│      • Related table: device_id (score: 0.6)                    │
│                                                                  │
│  3.4 Find Join Paths                                            │
│      RELATIONSHIPS:                                              │
│      • network_devices ←[device_id]→ device_status              │
│      • network_devices ←[device_id]→ network_alerts             │
│      • network_devices ←[device_id]→ maintenance_logs           │
│                                                                  │
│  3.5 Generate Smart Recommendations                             │
│      • "Include device_status for current status"               │
│      • "Join network_alerts for recent alerts"                  │
│                                                                  │
│  OUTPUT: Graph Insights                                         │
│    {                                                             │
│      "suggested_columns": {                                      │
│        "network_devices": [                                      │
│          {"name": "device_name", "score": 1.0},                 │
│          {"name": "device_type", "score": 0.8},                 │
│          {"name": "ip_address", "score": 0.7}                   │
│        ]                                                         │
│      },                                                          │
│      "suggested_joins": [                                        │
│        {                                                         │
│          "path": ["network_devices", "device_status"],          │
│          "via": "device_id"                                      │
│        }                                                         │
│      ],                                                          │
│      "related_tables": [                                         │
│        "network_alerts", "maintenance_logs"                      │
│      ],                                                          │
│      "recommendations": [                                        │
│        {"message": "Consider joining device_status"}            │
│      ]                                                           │
│    }                                                             │
│                                                                  │
│  LOGS:   ✅ Knowledge Graph is ENABLED                           │
│          🔍 Getting insights for: 'find all network device'     │
│          📊 Insights received:                                   │
│             Suggested columns: 1 table                           │
│             Suggested joins: 2 paths                             │
│             Related tables: 3 tables                             │
│             Recommendations: 2                                   │
│          📋 Column suggestions:                                  │
│             network_devices: [device_name, device_type, ...]    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Build LLM Prompt (sql_agent.py)                        │
│  ─────────────────────────────────────────────────────────────  │
│  4.1 System Prompt (context_manager.py)                         │
│      "You are a PostgreSQL expert. Generate accurate SQL..."    │
│                                                                  │
│  4.2 Schema Context (with samples)                              │
│      TABLE: network_devices                                     │
│      COLUMNS:                                                    │
│        - device_id (integer) PK                                  │
│        - device_name (varchar)                                   │
│        - device_type (varchar)                                   │
│        - ip_address (inet)                                       │
│        ...                                                       │
│      SAMPLE DATA (3 rows):                                       │
│        device_id | device_name   | device_type | ip_address     │
│        ---------|---------------|-------------|------------      │
│        1        | Router-Core-1 | Router      | 192.168.1.1     │
│        2        | Switch-Floor2 | Switch      | 192.168.1.2     │
│        3        | AP-Lobby      | AccessPoint | 192.168.1.3     │
│                                                                  │
│  4.3 Ontology Context (from Step 2)                             │
│      "🧠 RECOMMENDED COLUMNS:                                    │
│       1. USE: network_devices.device_name..."                   │
│                                                                  │
│  4.4 Knowledge Graph Context (from Step 3)                      │
│      "🎯 Relevant Columns:                                       │
│       • Table 'network_devices': device_name, device_type..."   │
│                                                                  │
│  FINAL PROMPT:                                                   │
│    [System] + [Question] + [Schema] + [Ontology] + [Graph]     │
│    Total: ~3500 characters                                       │
│                                                                  │
│  LOGS:   📝 Final prompt length: 3482 chars                      │
│          📊 Components:                                          │
│             - System: 250 chars                                  │
│             - Schema: 2100 chars                                 │
│             - Ontology: 650 chars                                │
│             - Knowledge graph: 482 chars                         │
│          💡 Has ontology guidance: YES ✅                        │
│          💡 Has knowledge graph: YES ✅                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: LLM SQL Generation (llm.py)                            │
│  ─────────────────────────────────────────────────────────────  │
│  5.1 Call Ollama API                                            │
│      MODEL: mistral:latest                                       │
│      ENDPOINT: http://localhost:11434/api/chat                  │
│      PAYLOAD: {                                                  │
│        "model": "mistral:latest",                               │
│        "messages": [{"role": "user", "content": prompt}],       │
│        "stream": false,                                          │
│        "format": "json"                                          │
│      }                                                           │
│                                                                  │
│  5.2 LLM Processing                                             │
│      • Reads schema structure                                    │
│      • Considers ontology recommendations                        │
│      • Applies knowledge graph insights                          │
│      • Generates SQL query                                       │
│                                                                  │
│  5.3 Response Parsing                                           │
│      RAW RESPONSE:                                               │
│      {                                                           │
│        "sql": "SELECT * FROM network_devices;",                 │
│        "explanation": "Query selects all network devices"       │
│      }                                                           │
│                                                                  │
│  LOGS:   🤖 Calling LLM to generate SQL...                       │
│          ✅ LLM response received                                │
│             SQL length: 35 chars                                 │
│             Has explanation: YES                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: SQL Validation & Execution (sql_agent.py)              │
│  ─────────────────────────────────────────────────────────────  │
│  6.1 Validate SQL                                               │
│      • Check not empty                                           │
│      • Check starts with SELECT/WITH/etc                         │
│      • Basic syntax check                                        │
│                                                                  │
│  6.2 Execute Query (database.py)                                │
│      EXECUTE: SELECT * FROM network_devices;                    │
│      RESULT: 10 rows in 0.010s                                   │
│                                                                  │
│  6.3 Return Results                                             │
│      {                                                           │
│        "success": true,                                          │
│        "sql_query": "SELECT * FROM network_devices;",           │
│        "results": [...10 rows...],                              │
│        "execution_time": 0.010,                                  │
│        "explanation": "Query selects all devices"               │
│      }                                                           │
│                                                                  │
│  LOGS:   🎯 FINAL SQL QUERY GENERATED:                           │
│          =====================================                    │
│          Query: SELECT * FROM network_devices;                   │
│          Length: 35 chars                                        │
│          Compression: 99.5:1                                     │
│          Explanation: Query selects all devices                  │
│          =====================================                    │
│          ✅ Query executed: 10 rows in 0.010s                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  RESULT: Display to User                                         │
│  ─────────────────────────────────────────────────────────────  │
│  10 rows from network_devices table                             │
│  Columns: device_id, device_name, device_type, ip_address, ...  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. **Ontology Service** (`backend/app/services/ontology.py`)
- **Purpose**: Maps business concepts to database schema
- **Data Source**: YAML ontology files in `/ontology/` directory
- **Key Methods**:
  - `register_schema_mappings()` - Loads ontology and creates mappings
  - `resolve_query()` - Analyzes NLP query and suggests columns
- **Output**: Column recommendations with confidence scores

### 2. **Knowledge Graph Service** (`backend/app/services/knowledge_graph.py`)
- **Purpose**: Provides relationship context from Neo4j graph database
- **Data Source**: Neo4j database with schema metadata
- **Key Methods**:
  - `get_graph_insights()` - Queries graph for relevant columns/joins
  - `get_column_suggestions()` - Ranks columns by relevance
  - `find_join_paths()` - Discovers table relationships
- **Output**: Column suggestions, join paths, recommendations

### 3. **Context Manager** (`backend/app/services/context_manager.py`)
- **Purpose**: Builds optimized prompts within token budgets
- **Strategies**: MINIMAL, FOCUSED, BALANCED, COMPREHENSIVE
- **Key Methods**:
  - `build_system_prompt()` - Creates base SQL generation instructions
  - `build_schema_context()` - Formats schema with samples
  - `build_error_context()` - Handles retry scenarios

### 4. **SQL Agent** (`backend/app/services/sql_agent.py`)
- **Purpose**: Orchestrates entire query flow
- **Pattern**: LangGraph state machine
- **Nodes**: generate_sql → validate → execute → handle_error → finalize
- **State**: Tracks question, schema, ontology context, graph insights, retries

## Debug Log Examples

### Normal Flow (with Ontology & Graph)
```log
🔍 TRACE: Schema Normalization
✅ Schema normalized: 5 tables
📋 Tables: device_status, hardware_info, maintenance_logs, network_alerts, network_devices

🔍 TRACE STEP 1: ONTOLOGY SEMANTIC RESOLUTION
✅ Ontology is ENABLED
📝 Registering schema mappings...
🧠 Registered 54 ontology column mappings
🔍 Resolving query: 'find all network device'
✅ Semantic resolution found!
   Confidence: 95%
🎯 ONTOLOGY RECOMMENDATIONS:
   1. network_devices.device_name (95%)
   2. network_devices.device_type (90%)

🔍 TRACE STEP 2: KNOWLEDGE GRAPH INSIGHTS
✅ Knowledge Graph is ENABLED
📊 Insights received:
   Suggested columns: 1 table
   Suggested joins: 2 paths
📋 Column suggestions:
   network_devices: [device_name, device_type, ip_address]

🔍 TRACE STEP 3: LLM SQL GENERATION
📝 Final prompt: 3482 chars
💡 Has ontology guidance: YES ✅
💡 Has knowledge graph: YES ✅
🤖 Calling LLM...
✅ LLM response received

🎯 FINAL SQL: SELECT * FROM network_devices;
✅ Query executed: 10 rows in 0.010s
```

### Degraded Mode (No Ontology/Graph)
```log
✅ Schema normalized: 5 tables
⚠️  Ontology is DISABLED in config
⚠️  Knowledge Graph is DISABLED in config
📝 Final prompt: 2100 chars
💡 Has ontology guidance: NO ❌
💡 Has knowledge graph: NO ❌
```

## Configuration

Enable/disable features in `app_config.yml`:

```yaml
# Ontology (static mappings)
ontology:
  enabled: true
  use_llm: false  # false = use YAML files only

# Knowledge Graph (dynamic relationships)
neo4j:
  enabled: true
  include_in_context: true
  uri: "bolt://localhost:7687"
```

## Viewing Logs

### Real-time monitoring:
```bash
tail -f backend_debug.log | grep "TRACE"
```

### Filter by component:
```bash
# Ontology only
grep "ONTOLOGY" backend_debug.log

# Knowledge graph only
grep "KNOWLEDGE GRAPH" backend_debug.log

# Final SQL
grep "FINAL SQL" backend_debug.log
```

### Search for specific query:
```bash
grep -A 50 "find all network device" backend_debug.log
```

## Performance Metrics

With full tracing enabled:
- **Overhead**: ~50ms per query (logging)
- **Log size**: ~2KB per query
- **Context building**: ~200ms (ontology + graph)
- **Total query time**: ~1.5-2s (includes LLM inference)

## Troubleshooting

### No ontology recommendations
- Check: `ontology.enabled = true` in config
- Verify: Ontology YAML files exist in `/ontology/`
- Check logs: "Registered X column mappings"

### No knowledge graph insights
- Check: Neo4j service running on port 7687
- Verify: `neo4j.enabled = true` in config
- Check logs: "Knowledge Graph is ENABLED"

### Schema normalization showing 0 tables
- Check: Database connection active
- Verify: `get_database_snapshot()` returns tables list
- Check logs: "Schema normalized: 0 tables" = BUG

## Files to Monitor

1. **Backend logs**: `/media/manoj/DriveData5/DATABASEAI/backend_debug.log`
2. **Ontology files**: `/media/manoj/DriveData5/DATABASEAI/ontology/*.yml`
3. **Config**: `/media/manoj/DriveData5/DATABASEAI/app_config.yml`
