# Oracle Current User Only Schema Fix - V2

## Problem Statement
When connecting to Oracle database as user `pgaiview`, the application was showing multiple schemas including:
- **PGAIVIEW** (current user's schema) ✓
- **AUDSYS** (Oracle audit system schema) ✗
- **DEMOUSER** (another user) ✗  
- **DVSYS** (Database Vault schema) ✗
- **DBSFWUSER** (system schema) ✗
- Other system and user schemas ✗

**User Requirement:** Show ONLY the connected user's schema (PGAIVIEW), not ANY other schemas.

## Root Cause
The previous `get_all_schemas()` method was querying `all_tables` which returns tables from ALL schemas the user can access, not just the user's own schema. Even with system schema filtering, it still showed other user schemas.

## Solution - Show Only Current User's Schema

### Implementation
Modified `oracle_adapter.py` `get_all_schemas()` method to:

1. **Get Current User:**
   ```sql
   SELECT USER FROM dual
   ```

2. **Query Only Current User's Objects:**
   ```sql
   -- Tables owned by current user
   SELECT COUNT(*) FROM user_tables
   
   -- Views owned by current user  
   SELECT COUNT(*) FROM user_views
   ```

3. **Return Only Current User:**
   ```python
   schemas.append({
       'schema_name': current_user,
       'table_count': table_count,
       'view_count': view_count,
       'owner': current_user
   })
   ```

### Key Changes

#### Before (showing all accessible schemas):
```python
cursor.execute("""
    SELECT DISTINCT owner as schema_name
    FROM all_tables
    WHERE owner NOT IN (system schemas...)
    ORDER BY owner
""")
# Returns: PGAIVIEW, AUDSYS, DEMOUSER, DVSYS, etc.
```

#### After (showing only current user):
```python
cursor.execute("SELECT USER FROM dual")
current_user = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_tables")
table_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_views")
view_count = cursor.fetchone()[0]

return [{'schema_name': current_user, ...}]
# Returns: PGAIVIEW only
```

## Database Views Comparison

| View | Scope | Usage |
|------|-------|-------|
| `dba_tables` | All tables in database | Requires DBA privilege (OLD) |
| `all_tables` | Tables user can access | Shows multiple schemas (OLD) |
| `user_tables` | Current user's tables | Shows only own schema (NEW ✓) |
| `user_views` | Current user's views | Shows only own views (NEW ✓) |

## Benefits

✅ **Security**: User only sees their own schema  
✅ **Simplicity**: No confusion with multiple schemas  
✅ **Performance**: Faster queries (no joins across schemas)  
✅ **Accuracy**: Shows only what the user owns  
✅ **Privacy**: Other users' schemas are hidden  

## Files Changed

1. **backend/app/database_adapters/oracle_adapter.py**
   - Modified `get_all_schemas()` method (lines 86-145)
   - Returns only current user's schema
   - Added fallback error handling
   - Kept old method as `_get_schema_info_OLD_METHOD()` for reference

## Testing

### 1. Rebuild Docker Image
```powershell
docker compose -f .\docker-compose.all.yml build databaseai
```

### 2. Start Containers
```powershell
docker compose -f .\docker-compose.all.yml up -d
```

### 3. Connect as PGAIVIEW
- **Host:** `oracle-db` (in Docker) or `localhost` (external)
- **Port:** `1521`
- **Service Name:** `XEPDB1`
- **Username:** `pgaiview`
- **Password:** `pgaiview123`

### 4. Expected Result
**Schema List Should Show:**
- ✅ PGAIVIEW (5 tables, 0 views)

**Schema List Should NOT Show:**
- ✗ AUDSYS
- ✗ DEMOUSER
- ✗ DVSYS
- ✗ DBSFWUSER
- ✗ SYS
- ✗ SYSTEM
- ✗ Any other schemas

### 5. Verify Tables
When you select PGAIVIEW schema, you should see only the tables owned by pgaiview:
- NETWORK_DEVICES
- DEVICE_STATUS
- MAINTENANCE_LOGS
- NETWORK_ALERTS
- HARDWARE_INFO
- (any other tables created by this user)

## Behavior for Different Users

| User | What They See |
|------|---------------|
| pgaiview | PGAIVIEW schema only |
| demouser | DEMOUSER schema only |
| system (DBA) | SYSTEM schema only* |
| audsys | AUDSYS schema only |

*Even DBA users will see only their own schema, not all schemas. This is by design for simplicity.

## Optional: Multi-Schema Support

If you need to support viewing multiple schemas in the future, you can:

1. Add a configuration option: `show_all_accessible_schemas: true/false`
2. Add a UI toggle: "Show only my schema" vs "Show all accessible schemas"
3. Use the old method `_get_schema_info_OLD_METHOD()` when toggled

Current implementation prioritizes **security and simplicity** over flexibility.

## Troubleshooting

### Issue: Still seeing other schemas
**Solution:** Clear Docker cache and rebuild
```powershell
docker compose -f .\docker-compose.all.yml down
docker compose -f .\docker-compose.all.yml build --no-cache databaseai
docker compose -f .\docker-compose.all.yml up -d
```

### Issue: Schema shows 0 tables but you have tables
**Solution:** Check if tables are in the correct schema
```sql
-- Connect as pgaiview and verify
SELECT table_name FROM user_tables;
```

### Issue: Permission denied errors
**Solution:** Ensure user has CREATE SESSION privilege
```sql
GRANT CREATE SESSION TO pgaiview;
GRANT CREATE TABLE TO pgaiview;
```

## Summary

This fix ensures that when any user connects to Oracle, they ONLY see their own schema, making the interface cleaner, more secure, and less confusing. No system schemas or other user schemas will be visible.

**Status:** ✅ Implemented and ready for testing  
**Date:** November 27, 2025  
**Modified Files:** 1 (oracle_adapter.py)
