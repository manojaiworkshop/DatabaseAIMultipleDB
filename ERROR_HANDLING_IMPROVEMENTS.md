# Error Handling Improvements - DatabaseAI

## Date: October 25, 2025

## Issues Fixed

### 1. **LLM Generating Text Instead of SQL**
**Problem:** vLLM was returning explanatory text like "Based on the schema you provided, there are 15 tables..." instead of actual SQL queries.

**Fix:**
- Enhanced SQL extraction logic in all LLM providers
- Added validation to detect explanatory text patterns
- Improved prompt instructions with clear examples
- Added early validation to reject non-SQL responses

### 2. **Old SQL Reused When LLM Generation Fails**
**Problem:** When LLM generation failed (400 error), the agent would reuse the old broken SQL query instead of generating fresh SQL.

**Fix:**
- Modified `_generate_sql_node()` to set empty SQL on generation failure
- Added error flag check in validation to prevent executing with LLM errors
- Clear distinction between generation errors and execution errors

### 3. **vLLM 400 Errors on Retries (Token Overflow)**
**Problem:** Retry prompts were too verbose, causing vLLM to reject requests due to context window limits.

**Fix:**
- Reduced retry prompt from ~1000 tokens to ~200 tokens
- Created `_get_compact_schema()` method for retries (table names + limited columns)
- Limited error messages to first 120 characters
- Removed redundant schema context repetition

### 4. **Poor Error Analysis**
**Problem:** Error hints were generic and didn't help LLM fix the actual problem (e.g., "role_permission" table doesn't exist).

**Fix:**
- Added `_extract_table_names()` to get actual table names from schema
- Added `_find_similar_names()` using Levenshtein distance for suggestions
- Enhanced error messages with actual available tables
- Provide specific "Did you mean X?" suggestions for typos

### 5. **Insufficient Logging**
**Problem:** Hard to debug what's happening, especially with vLLM errors.

**Fix:**
- Added request size logging before sending to vLLM
- Log vLLM error responses (first 500 chars)
- Better error messages explaining the likely cause (e.g., "request too large")
- Track retry attempts and error history

---

## Key Improvements

### SQL Agent (`sql_agent.py`)

#### Before:
```python
# Verbose retry prompt (causes token overflow)
prompt = f"""Previous attempt failed with error:
{state['error_message']}

Previous SQL:
{state['sql_query']}

{error_hints}

IMPORTANT: Please carefully check the schema below...
[FULL SCHEMA REPEATED]
...
"""
```

#### After:
```python
# Compact retry prompt
prompt = f"""RETRY #{state['current_retry']}: Previous SQL failed.

Error: {state['error_message'][:120]}

{error_hints}

Question: {state['question']}

MUST return JSON: {{"sql": "YOUR_QUERY_HERE", "explanation": "brief"}}"""

# Use compact schema (just table names + key columns)
schema_for_llm = self._get_compact_schema(state['schema_context'])
```

#### Error Analysis Enhancement:

**Before:**
```
"ACTION: Use only the table names listed in the schema above"
```

**After:**
```
"Table 'role_permission' DOES NOT EXIST!"
"Available tables: web_user, user_reporting, exams, tasks, tools..."
"Did you mean: user_role_permissions, role_permissions?"
```

### LLM Service (`llm.py`)

#### Added Better Error Logging:
```python
if response.status_code != 200:
    error_detail = response.text[:500]
    logger.error(f"vLLM API error {response.status_code}: {error_detail}")
    raise Exception(f"vLLM API returned {response.status_code}. This usually means the request is too large or malformed.")
```

#### Request Size Tracking:
```python
logger.info(f"Sending request to vLLM with {len(messages)} messages, total chars: {sum(len(str(m)) for m in messages)}")
```

---

## Helper Methods Added

### 1. `_extract_table_names(schema_context: str)`
Extracts actual table names from schema using regex patterns.

### 2. `_find_similar_names(target: str, candidates: List[str])`
Uses Levenshtein distance to find similar table/column names for suggestions.

### 3. `_get_compact_schema(schema_context: str)`
Creates compact schema representation with just table names and top 8 columns per table.

### 4. Enhanced `_analyze_error(error_message: str, schema_context: str)`
Now provides:
- Specific error identification
- Actual available tables
- Similarity suggestions
- Concise, actionable hints

---

## Testing Recommendations

1. **Test with table name typos:**
   - "Show me data from role_permission" (should suggest similar tables)

2. **Test with column name errors:**
   - "Select userid from web_user" (should suggest correct column name)

3. **Test retry logic:**
   - Force an error and verify SQL is regenerated, not reused

4. **Test vLLM token limits:**
   - Ask complex questions that require multiple retries
   - Verify prompts stay within token limits

5. **Test all LLM providers:**
   - OpenAI
   - vLLM
   - Ollama

---

## Configuration Recommendations

### app_config.yml:
```yaml
# vLLM Configuration - Keep tokens low for retries
vllm:
  api_url: "http://localhost:8000/v1/chat/completions"
  model: "/models"
  max_tokens: 512  # Reduced to fit within context
  temperature: 0.7

# Chat Configuration
chat:
  max_retries: 3  # Good balance
  schema_cache_ttl: 3600  # 1 hour cache
```

---

## Expected Behavior Now

### Scenario 1: Table Name Error
**User:** "Show me data from role_permission table"

**Agent Behavior:**
1. **Attempt 1:** LLM generates SQL with wrong table name
2. **Error:** `relation "role_permission" does not exist`
3. **Retry Prompt:** Compact prompt with:
   - Error: "Table 'role_permission' DOES NOT EXIST!"
   - Available: "web_user, user_reporting, user_role_permissions..."
   - Suggestion: "Did you mean: user_role_permissions?"
4. **Attempt 2:** LLM generates correct SQL
5. **Success!** ✓

### Scenario 2: vLLM Token Overflow (Fixed)
**Previous Behavior:**
- Retry prompt: 2000+ tokens
- vLLM returns 400 error
- Agent reuses old bad SQL
- Fails all retries ❌

**New Behavior:**
- Retry prompt: ~200 tokens (compact)
- vLLM accepts request ✓
- Fresh SQL generated ✓
- Success! ✓

---

## Monitoring

Watch for these log patterns:

### Good:
```
INFO - Generating SQL (attempt 1/3)
INFO - Generated SQL: SELECT COUNT(*) FROM...
INFO - Validating SQL query
INFO - Executing SQL query
INFO - Query executed successfully: 1 rows in 0.003s
```

### Retry (Now Handled):
```
INFO - Generating SQL (attempt 1/3)
ERROR - Query execution failed: relation "role_permission" does not exist
WARNING - Handling error (retry 0/3)
INFO - Error: relation "role_permission" does not exist
INFO - Generating SQL (attempt 2/3)
INFO - Sending request to vLLM with 3 messages, total chars: 1248
INFO - Generated SQL: SELECT * FROM user_role_permissions...
INFO - Query executed successfully!
```

### vLLM Error (Now Better Explained):
```
INFO - Sending request to vLLM with 4 messages, total chars: 3421
ERROR - vLLM API error 400: {"error": "Request exceeds maximum context length..."}
ERROR - LLM generation failed: vLLM API returned 400. This usually means the request is too large or malformed.
```

---

## Future Enhancements

1. **Adaptive Context Window:** Dynamically adjust schema detail based on model capacity
2. **Query Caching:** Cache successful SQL for similar questions
3. **Learning from Errors:** Build a database of common mistakes and fixes
4. **Schema Embeddings:** Use embeddings to find most relevant tables instead of keyword matching
5. **Multi-step Reasoning:** For complex queries, break into sub-queries

---

## Rollback Instructions

If issues arise, revert these files:
```bash
git checkout HEAD -- backend/app/services/sql_agent.py
git checkout HEAD -- backend/app/services/llm.py
```

Then restart backend:
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```
