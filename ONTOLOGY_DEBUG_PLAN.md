# Ontology Generation Debug Plan 🔍

## Problem Summary
Ontology generation is creating concepts for **tables that don't exist** in the database:
- **Expected tables**: device_status, hardware_info, maintenance_logs, network_alerts, network_devices
- **Generated concepts**: NetworkInterface, NetworkPort, NetworkVlanInterface, Vlan (WRONG!)

## Root Cause Hypothesis
The LLM is hallucinating table names instead of using the actual schema summary provided in the prompt.

## Debug Instrumentation Added

### 1. Entry Point Debug (routes/ontology.py)
**Location**: `/generate` endpoint, right after `get_database_snapshot()`

**What it shows**:
- Schema snapshot structure and keys
- Database name
- Total tables/views count
- First 5 tables with full names and column counts
- Whether tables list is empty

**Look for**:
```
🔍 DEBUG: SCHEMA SNAPSHOT FROM DATABASE SERVICE
================================================================================
Snapshot keys: ['database_name', 'tables', 'views', 'total_tables', 'total_views', 'timestamp']
Database: testing
Total tables: 5
...
📋 First 5 tables in snapshot:
  1. public.device_status (5 columns)
  2. public.hardware_info (9 columns)
  3. public.maintenance_logs (12 columns)
  4. public.network_alerts (13 columns)
  5. public.network_devices (15 columns)
```

### 2. Service Entry Debug (services/dynamic_ontology.py)
**Location**: `generate_ontology()` method, start of function

**What it shows**:
- Schema snapshot keys received by service
- Tables data type (list vs dict)
- Tables count
- First 3 table names

**Look for**:
```
🔍 DEBUG: SCHEMA SNAPSHOT RECEIVED
================================================================================
Schema snapshot keys: ['database_name', 'tables', 'views', 'total_tables', 'total_views', 'timestamp']
Tables type: <class 'list'>
Tables count: 5
First 3 tables:
  1. public.device_status (5 columns)
  2. public.hardware_info (9 columns)
  3. public.maintenance_logs (12 columns)
```

### 3. Schema Summary Debug (services/dynamic_ontology.py)
**Location**: `_generate_concepts()` method, before LLM call

**What it shows**:
- Complete formatted schema summary sent to LLM
- All table names with columns, types, constraints
- Exact prompt being used

**Output**:
- Console logs with full schema
- File: `debug_ontology_prompt.txt` with complete prompt

**Look for**:
```
🔍 DEBUG: FULL SCHEMA SUMMARY BEING SENT TO LLM
================================================================================
DATABASE SCHEMA SUMMARY:
Total tables: 5

Table: public.device_status
  Columns (5):
    - device_id (integer) [PK]
    - status (character varying)
    ...
```

## Testing Steps

### Step 1: Restart Backend
```bash
cd /media/manoj/DriveData5/DATABASEAI
pkill -f "python.*run_backend"
python run_backend.py > backend_debug.log 2>&1 &
```

### Step 2: Tail Logs
```bash
tail -f backend_debug.log | grep -A 50 "DEBUG:"
```

### Step 3: Generate Ontology from UI
1. Open http://localhost:3000/chat
2. Verify database connected (left sidebar shows 5 tables)
3. Go to Settings → Ontology tab
4. Click "Generate Ontology"
5. Wait for completion

### Step 4: Check Debug Output

**A. Console Logs**
```bash
# Check entry point debug
grep -A 30 "SCHEMA SNAPSHOT FROM DATABASE SERVICE" backend_debug.log

# Check service entry debug  
grep -A 20 "SCHEMA SNAPSHOT RECEIVED" backend_debug.log

# Check schema summary debug
grep -A 100 "FULL SCHEMA SUMMARY BEING SENT TO LLM" backend_debug.log
```

**B. Debug File**
```bash
cat debug_ontology_prompt.txt
```

This file contains the exact prompt sent to the LLM, including:
- Full schema summary
- Complete instruction prompt
- All table and column details

## Expected vs Actual Analysis

### If Schema Summary is CORRECT (shows 5 real tables)
**Problem**: LLM is ignoring instructions
**Solutions**:
1. Try temperature=0.1 (more deterministic)
2. Use different model (qwen2.5:14b, llama3.1:8b)
3. Add few-shot examples in prompt
4. Use stronger instruction format (e.g., XML tags, numbered rules)

### If Schema Summary is EMPTY or WRONG
**Problem**: Data flow issue before LLM
**Check**:
1. `database.py` - Is `get_database_snapshot()` returning correct data?
2. Cache issue - Clear schema cache: `schema_cache = None` in database.py
3. Connection issue - Verify connected to correct database
4. Format issue - Tables might be in dict format instead of list

### If Tables List is Dict Instead of List
**Problem**: Format mismatch
**Fix**: Already handled in code with:
```python
if isinstance(tables, dict):
    tables_list = list(tables.values())
else:
    tables_list = tables
```

## Quick Diagnostic Commands

```bash
# Check if backend is running
ps aux | grep run_backend

# View last 50 lines of debug output
tail -n 50 backend_debug.log

# Search for all debug markers
grep "🔍 DEBUG:" backend_debug.log

# Count tables in database directly
psql -h 192.168.1.2 -p 5432 -U postgres -d testing -c "\dt"

# Check ontology output files
ls -lh ontology_*.yaml ontology_*.owl
tail -n 50 ontology_*.yaml
```

## Success Criteria

✅ **Checkpoint 1**: Entry point debug shows 5 tables with correct names
✅ **Checkpoint 2**: Service entry debug shows list of 5 tables
✅ **Checkpoint 3**: Schema summary includes all 5 real tables (device_status, hardware_info, maintenance_logs, network_alerts, network_devices)
✅ **Checkpoint 4**: debug_ontology_prompt.txt file shows complete schema with real tables
✅ **Checkpoint 5**: Generated ontology YAML contains concepts matching real table names

## Next Steps Based on Results

### Scenario A: All checkpoints pass, but ontology still wrong
→ **LLM hallucination issue**
→ Need to adjust temperature, model, or prompt format

### Scenario B: Checkpoint 1-2 pass, but Checkpoint 3 fails
→ **Schema summarization issue**
→ Bug in `_summarize_schema()` method

### Scenario C: Checkpoint 1 passes, but Checkpoint 2 fails
→ **Data passing issue**
→ Schema snapshot not being passed correctly to service

### Scenario D: Checkpoint 1 fails
→ **Database connection issue**
→ `get_database_snapshot()` not working correctly

## Additional Diagnostic Tools

### Test Database Connection
```bash
python -c "
from backend.app.services.database import db_service
snapshot = db_service.get_database_snapshot()
print(f'Tables: {len(snapshot[\"tables\"])}')
for t in snapshot['tables']:
    print(f'  - {t[\"full_name\"]} ({len(t[\"columns\"])} cols)')
"
```

### Test Schema Summary Format
```bash
python -c "
from backend.app.services.database import db_service
from backend.app.services.dynamic_ontology import DynamicOntologyService
from backend.app.services.llm import LLMService
from backend.app.config import load_config

config = load_config()
llm = LLMService(config)
onto = DynamicOntologyService(llm, config)

snapshot = db_service.get_database_snapshot()
summary = onto._summarize_schema(snapshot)
print(summary)
"
```

### Test LLM Response Directly
```bash
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral:latest",
    "messages": [{
      "role": "user",
      "content": "List these tables: device_status, hardware_info. Respond with JSON array."
    }],
    "stream": false
  }'
```

## Files Modified

1. **backend/app/routes/ontology.py**
   - Added entry point debug logging
   - Shows snapshot structure before passing to service

2. **backend/app/services/dynamic_ontology.py**
   - Added service entry debug logging
   - Added schema summary debug logging with file output
   - Debug file: `debug_ontology_prompt.txt`

## Contact Information

If issue persists after following this debug plan:
1. Share `backend_debug.log` (specifically the DEBUG sections)
2. Share `debug_ontology_prompt.txt` contents
3. Share generated `ontology_*.yaml` file
4. Share output of `psql -h 192.168.1.2 -p 5432 -U postgres -d testing -c "\dt"`

This will help identify the exact point of failure in the data flow pipeline.
