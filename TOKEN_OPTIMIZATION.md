# Token Optimization Guide for DatabaseAI

## Problem
When using LLMs with limited context windows (e.g., 4096 tokens), sending full database schemas can exceed the token limit.

## Solutions Implemented

### 1. **Optimized Schema Format** (80% token reduction)
**Before:**
```
Table: users
Columns:
  - id: bigint NOT NULL
  - name: character varying(255) NULL
  - email: character varying(255) NULL
Sample data (first 3 rows):
  Row 1: {'id': 1, 'name': 'John', 'email': 'john@example.com', ...}
  Row 2: {'id': 2, 'name': 'Jane', 'email': 'jane@example.com', ...}
```

**After (Compact):**
```
users(id:bigint, name:character varying, email:character varying)
```

### 2. **Relevant Table Selection**
Instead of sending all tables, we now:
- Analyze the user's question
- Score tables based on keyword matching
- Send only top 10-15 most relevant tables

### 3. **Reduced System Prompt**
Shortened instructions from ~200 tokens to ~50 tokens.

### 4. **Limited Conversation History**
Only keep last 2 conversation turns instead of entire history.

### 5. **Sample Data Removal**
Removed sample data from default context (can be enabled if needed).

## Configuration

### For 4096 Token Context Window

```yaml
vllm:
  max_tokens: 512  # Response tokens
```

**Token Budget:**
- System Prompt: ~50 tokens
- Schema Context: ~1500 tokens (15 tables × 100 tokens avg)
- User Question: ~50 tokens
- Conversation History: ~200 tokens (2 messages)
- **Total Input: ~1800 tokens**
- Response: 512 tokens
- **Grand Total: ~2312 tokens** ✓ Fits in 4096

### For 8192 Token Context Window

```yaml
vllm:
  max_tokens: 1024
```

You can increase `max_tables` to 25 in the code.

### For 16K+ Token Context Window

```yaml
vllm:
  max_tokens: 2048
```

Use `get_schema_context(include_samples=True)` for full schema with samples.

## API Methods

### 1. Optimized (Default)
```python
# Only relevant tables, compact format
schema_context = db_service.get_relevant_tables_context(question, max_tables=15)
```

### 2. Compact All Tables
```python
# All tables but compact format
schema_context = db_service.get_schema_context(include_samples=False)
```

### 3. Full Context (High Token)
```python
# All tables with sample data
schema_context = db_service.get_schema_context(include_samples=True)
```

## Tuning Parameters

### In `backend/app/services/database.py`

**Adjust number of relevant tables:**
```python
def get_relevant_tables_context(self, question: str, max_tables: int = 10):
    # Change max_tables: 5-20 recommended
```

**Enable/disable sample data:**
```python
def get_schema_context(self, include_samples: bool = False):
    # Set to True if you have larger context window
```

### In `backend/app/routes/api.py`

**Adjust conversation history:**
```python
# Keep last N messages
limited_history = [msg.dict() for msg in request.conversation_history[-2:]]
# Change -2 to -3, -4, etc. for more context
```

## Token Estimation

Rough estimates:
- **Table name + columns**: ~100 tokens per table
- **Sample data row**: ~50-100 tokens
- **User question**: ~20-100 tokens
- **System prompt (compact)**: ~50 tokens
- **System prompt (verbose)**: ~200 tokens

## Monitoring

Add logging to track token usage:

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Log before LLM call
logger.info(f"Schema context tokens: {count_tokens(schema_context)}")
logger.info(f"Total input tokens: {count_tokens(system_prompt + schema_context + question)}")
```

## Best Practices

1. **Start Small**: Use `max_tables=10` and increase if needed
2. **Cache Schema**: Schema is cached for 1 hour to reduce database queries
3. **Limit History**: Keep only recent conversation turns
4. **Monitor Errors**: Watch for context length errors and adjust
5. **Test Queries**: Try different question types to ensure relevant tables are selected

## Troubleshooting

### Error: "maximum context length is 4096 tokens"
**Solution**: Reduce `max_tables` or `max_tokens` in config

### Query quality decreased
**Solution**: Increase `max_tables` to 15-20

### Missing tables in context
**Solution**: Improve keyword matching or use full schema for complex queries

### Still too many tokens
**Solution**:
1. Reduce max_tables to 5-8
2. Shorten table/column names if possible
3. Use even more compact format
4. Consider upgrading to larger context model

## Advanced: Custom Optimization

For very large databases (100+ tables), consider:

1. **Table Categories**: Group related tables
2. **Dynamic Max Tables**: Adjust based on question complexity
3. **Column Filtering**: Only include important columns
4. **Semantic Search**: Use embeddings to find relevant tables

Example:
```python
def get_smart_context(self, question: str) -> str:
    # Analyze question complexity
    word_count = len(question.split())
    
    if word_count < 10:
        max_tables = 8  # Simple question
    elif word_count < 20:
        max_tables = 15  # Medium complexity
    else:
        max_tables = 25  # Complex question
    
    return self.get_relevant_tables_context(question, max_tables)
```

## Summary

With these optimizations:
- ✅ Reduced token usage by ~80%
- ✅ Fits in 4096 token context window
- ✅ Maintains query quality
- ✅ Faster LLM responses
- ✅ Lower API costs
