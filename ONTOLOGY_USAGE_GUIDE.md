# 🧬 Ontology Feature - Usage Guide

## 🎯 Overview

The **Dynamic Ontology** feature automatically generates semantic mappings between your database schema and business domain concepts, improving SQL generation accuracy.

---

## ⚠️ Important Prerequisites

### **MUST Connect to Database First**

The ontology feature **requires an active database connection** to work. It analyzes your actual database schema to generate meaningful ontologies.

**Steps:**
1. ✅ Go to the **main Connection page** (home page)
2. ✅ Enter your database credentials and **Connect**
3. ✅ Wait for schema to load
4. ✅ Navigate to **Chat page** (connection remains active)
5. ✅ Now open **Settings → Ontology tab**
6. ✅ Click **"Generate Ontology"**

---

## 🚨 Common Error: "No active database connection"

### **Problem:**
```
❌ No active database connection. Please connect to a database first.
```

### **Cause:**
- You opened Settings → Ontology without connecting to a database first
- Your database connection was disconnected
- You navigated away and the session expired

### **Solution:**
1. Go back to the **Connection page** or **Chat page**
2. Connect to your database
3. Keep the connection active
4. Return to Settings → Ontology
5. Try "Generate Ontology" again

---

## 📋 How to Generate Ontology - Step by Step

### **Method 1: Manual Generation (Recommended for Testing)**

```
Step 1: Connect to Database
┌─────────────────────────────┐
│  PGAIView Connection Page   │
│                             │
│  Host: localhost            │
│  Port: 5432                 │
│  Database: mydb             │
│  Username: postgres         │
│  Password: ****             │
│                             │
│  [Connect to Database]      │
└─────────────────────────────┘
         ↓
Step 2: Wait for Schema Load
┌─────────────────────────────┐
│ ✅ Connected successfully!  │
│ Database: mydb              │
│ Tables: 25                  │
└─────────────────────────────┘
         ↓
Step 3: Open Settings
┌─────────────────────────────┐
│  Chat Page                  │
│  [⚙️ Settings] ← Click here │
└─────────────────────────────┘
         ↓
Step 4: Generate Ontology
┌─────────────────────────────┐
│  Settings → Ontology Tab    │
│                             │
│  ☑️ Enable Ontology         │
│  ☑️ Enable Dynamic Gen      │
│                             │
│  [🔄 Generate Ontology]     │
└─────────────────────────────┘
         ↓
Step 5: Wait for Generation (15-30 seconds)
┌─────────────────────────────┐
│ 🤖 Generating ontology...   │
│ Analyzing 25 tables...      │
└─────────────────────────────┘
         ↓
Step 6: Success!
┌─────────────────────────────┐
│ ✅ Ontology generated for   │
│    database "mydb":         │
│    - 8 concepts             │
│    - 45 properties          │
│    - 12 relationships       │
│    from 25 tables           │
└─────────────────────────────┘
```

---

### **Method 2: Automatic Generation (Production Mode)**

Enable in `app_config.yml`:

```yaml
ontology:
  enabled: true
  auto_mapping: true
  dynamic_generation:
    enabled: true
    use_llm: true
    cache_ontologies: true
    export_format: both  # 'yml', 'owl', or 'both'
  include_in_context: true
```

**Behavior:**
- Ontology is **automatically generated on first query**
- Cached per database connection
- Reused for subsequent queries
- No manual intervention needed

---

## 📊 What Gets Generated?

### **1. Concepts (Business Entities)**

```yaml
# Example: E-commerce database
concepts:
  - name: Customer
    tables: [tbl_cust, customers]
    description: "Represents a customer in the system"
    confidence: 0.95
    
  - name: Order
    tables: [orders, ord_hdr]
    description: "Purchase order placed by customer"
    confidence: 0.92
```

### **2. Properties (Column Mappings)**

```yaml
properties:
  - concept: Customer
    business_name: FirstName
    db_column: f_name
    db_table: tbl_cust
    data_type: text
    confidence: 0.90
```

### **3. Relationships**

```yaml
relationships:
  - from_concept: OrderItem
    to_concept: Order
    relationship_type: belongsTo
    foreign_key: order_id
    confidence: 1.0
```

---

## 📁 Generated Files

Ontology files are saved in `/ontology/` directory:

```
ontology/
├── mydb_localhost_5432_ontology_20251028_143520.owl   # W3C OWL format
├── mydb_localhost_5432_ontology_20251028_143520.yml   # YAML format
├── production_db_ontology_20251028_150230.owl
└── production_db_ontology_20251028_150230.yml
```

**File naming format:**
```
{database}_{host}_{port}_ontology_{timestamp}.{format}
```

---

## 🎨 User Interface

### **Ontology Settings Tab**

```
┌────────────────────────────────────────────────────────────┐
│ Ontology Configuration                [🔄 Generate Ontology]│
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ℹ️  Database Connection Required                          │
│    To generate an ontology, you must first connect to a   │
│    database from the main chat page.                       │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Enable Ontology                                  [✓ ON]   │
│ Use ontology for semantic SQL generation                   │
│                                                            │
│ Enable Dynamic Generation                        [✓ ON]   │
│ Auto-generate ontology from database schema                │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Statistics                                                 │
│ • Concepts: 8                                              │
│ • Properties: 45                                           │
│ • Relationships: 12                                        │
│ • Tables: 25                                               │
│ • Generated: 2025-10-28 14:35:20                          │
├────────────────────────────────────────────────────────────┤
│ Exported Files                                             │
│ 📄 mydb_localhost_5432_ontology_20251028_143520.owl       │
│    [Download]                                              │
│ 📄 mydb_localhost_5432_ontology_20251028_143520.yml       │
│    [Download]                                              │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuration Options

### **app_config.yml**

```yaml
ontology:
  # Main toggle
  enabled: true
  
  # Automatic mapping on first query
  auto_mapping: true
  
  # Confidence threshold (0.0 - 1.0)
  # Lower = more lenient, Higher = stricter
  confidence_threshold: 0.7
  
  # Custom ontology file (optional)
  custom_file: null
  
  # Dynamic generation settings
  dynamic_generation:
    enabled: true              # Enable LLM-powered generation
    export_format: both        # 'yml', 'owl', or 'both'
    use_llm: true              # Use LLM for semantic analysis
    cache_ontologies: true     # Cache generated ontologies
  
  # Include ontology in LLM context
  include_in_context: true
  
  # Format preference
  format: yml
```

---

## 💡 Best Practices

### **1. Generate Once, Use Many Times**

✅ **Do:**
- Generate ontology once per database
- Cache is automatically enabled
- Reuse across multiple queries

❌ **Don't:**
- Regenerate for every query
- Disable caching in production

### **2. Use Descriptive Table/Column Names**

✅ **Good Schema:**
```sql
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(50),
    email_address VARCHAR(100)
);
```

❌ **Poor Schema:**
```sql
CREATE TABLE tbl1 (
    id INT PRIMARY KEY,
    c1 VARCHAR(50),
    c2 VARCHAR(100)
);
```

**Why:** LLM generates better ontologies from descriptive names.

### **3. Review Generated Ontologies**

After generation, review the OWL/YAML files to ensure:
- Concepts match your business model
- Relationships are correctly identified
- Confidence scores are reasonable (>0.7)

### **4. Adjust Confidence Threshold**

If ontology is too sparse:
```yaml
confidence_threshold: 0.5  # Lower threshold
```

If too many false positives:
```yaml
confidence_threshold: 0.85  # Higher threshold
```

---

## 🐛 Troubleshooting

### **Issue 1: Empty Ontology (0 concepts, 0 properties)**

**Symptoms:**
```
Generated file shows:
Tables: 0, Concepts: 0, Properties: 0
```

**Cause:**
- No database connection when generated
- Database has no tables

**Solution:**
1. Ensure database is connected
2. Verify database has tables: `SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';`
3. Try regenerating with `force_regenerate: true`

---

### **Issue 2: Low Quality Ontology**

**Symptoms:**
- Generic concept names ("Table1", "Entity")
- Low confidence scores (<0.5)
- Missing relationships

**Causes:**
- Poor schema naming (tbl1, c1, c2)
- No foreign key constraints
- LLM provider issues

**Solutions:**
1. **Improve schema naming:**
   ```sql
   ALTER TABLE tbl1 RENAME TO customers;
   ALTER TABLE tbl1 RENAME COLUMN c1 TO first_name;
   ```

2. **Add foreign keys:**
   ```sql
   ALTER TABLE orders 
   ADD CONSTRAINT fk_customer 
   FOREIGN KEY (customer_id) REFERENCES customers(id);
   ```

3. **Use better LLM provider:**
   ```yaml
   llm:
     provider: openai  # Instead of ollama
   openai:
     model: gpt-4o-mini-2024-07-18
   ```

---

### **Issue 3: LLM Timeout During Generation**

**Symptoms:**
```
Failed to generate ontology: Timeout waiting for LLM response
```

**Solutions:**
1. **Reduce schema size:**
   ```yaml
   ontology:
     dynamic_generation:
       max_tables: 20  # Limit tables analyzed
   ```

2. **Increase timeout:**
   ```yaml
   ollama:
     timeout: 120  # 2 minutes
   ```

3. **Use faster LLM:**
   ```yaml
   ollama:
     model: mistral:latest  # Faster than llama
   ```

---

## 📈 Performance Tips

### **1. Cache Aggressively**

```yaml
ontology:
  dynamic_generation:
    cache_ontologies: true

cache:
  schema_cache_ttl: 7200  # 2 hours
```

### **2. Generate Once at Startup**

For production, generate ontology on app startup:

```python
# In your startup script
from backend.app.services.dynamic_ontology import get_dynamic_ontology_service

@app.on_event("startup")
async def generate_ontology_on_startup():
    if config['ontology']['enabled']:
        # Generate and cache
        await dynamic_ontology.generate_ontology(...)
```

### **3. Use Smaller LLM for Speed**

```yaml
ollama:
  model: mistral:latest  # Fast
  # vs
  model: llama3.1:70b   # Slow but accurate
```

---

## 🎓 Example Use Cases

### **Use Case 1: E-commerce Database**

**Before Ontology:**
```
User: "Show customers from California"
LLM: SELECT * FROM tbl_cust WHERE st = 'CA'  ❌ (Wrong column name)
```

**After Ontology:**
```
User: "Show customers from California"
Ontology maps: Customer.State → tbl_cust.st_cd
LLM: SELECT * FROM tbl_cust WHERE st_cd = 'CA'  ✅
```

### **Use Case 2: Healthcare Database**

**Before Ontology:**
```
User: "Find diabetic patients"
LLM: SELECT * FROM patients WHERE condition = 'diabetes'  ❌ (No such column)
```

**After Ontology:**
```
User: "Find diabetic patients"
Ontology: Patient → pt_rec, Diagnosis → dx_code (ICD-10: E11.*)
LLM: SELECT p.* FROM pt_rec p 
     JOIN dx_code d ON p.pt_id = d.pt_id 
     WHERE d.icd_10_cd LIKE 'E11%'  ✅
```

---

## 📚 Further Reading

- **W3C OWL Standard:** https://www.w3.org/TR/owl2-overview/
- **Dynamic Ontology Guide:** `DYNAMIC_ONTOLOGY_GUIDE.md`
- **Implementation Details:** `ONTOLOGY_IMPLEMENTATION_COMPLETE.md`
- **Architecture:** `ARCHITECTURE_DIAGRAM.md`

---

## ✅ Quick Checklist

Before generating ontology:

- [ ] Database connected
- [ ] Schema loaded (check table count)
- [ ] LLM service running (`ollama list` or check OpenAI key)
- [ ] `ontology.enabled: true` in config
- [ ] `ontology.dynamic_generation.enabled: true`

Generate ontology:

- [ ] Navigate to Settings → Ontology
- [ ] Click "Generate Ontology"
- [ ] Wait 15-30 seconds
- [ ] Check for success message
- [ ] Download OWL/YAML files (optional)

Verify ontology:

- [ ] Check `/ontology/` directory for files
- [ ] Open OWL file and verify: Tables > 0, Concepts > 0
- [ ] Test a query to see if ontology improves results

---

## 🆘 Still Having Issues?

1. **Check backend logs:**
   ```bash
   tail -f logs/backend.log
   ```

2. **Check database connection:**
   ```bash
   psql -h localhost -p 5432 -U postgres -d mydb -c "SELECT COUNT(*) FROM information_schema.tables;"
   ```

3. **Test LLM service:**
   ```bash
   curl http://localhost:11434/api/generate -d '{"model":"mistral","prompt":"test"}'
   ```

4. **Clear cache and retry:**
   ```bash
   rm -rf ontology/*.owl ontology/*.yml
   # Restart backend
   python run_backend.py
   ```

---

## 🚀 Summary

The Ontology feature is powerful but **requires an active database connection** to work. Always:

1. ✅ **Connect first** (Connection page)
2. ✅ **Wait for schema** (see table count)
3. ✅ **Generate ontology** (Settings → Ontology)
4. ✅ **Use in queries** (automatic if enabled)

Happy querying! 🎉
