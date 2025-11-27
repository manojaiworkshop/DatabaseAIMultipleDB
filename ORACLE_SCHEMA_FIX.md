# Oracle Schema Filtering Fix

## Issue
When connecting to Oracle with user `pgaiview`, the application was showing **ALL schemas/users** in the database instead of only showing schemas that the connected user has access to.

## Root Cause
The `get_all_schemas()` method in `oracle_adapter.py` was querying `dba_users` which:
1. Requires DBA privileges (which most users don't have)
2. Returns ALL user accounts in the database, regardless of access
3. Showed system schemas that users shouldn't interact with

## Solution
Modified `get_all_schemas()` to:

### 1. Query Accessible Schemas Only
```sql
SELECT DISTINCT owner as schema_name
FROM all_tables
WHERE owner NOT IN (system schemas...)
ORDER BY owner
```

**Key Changes:**
- Changed from `dba_users` to `all_tables` 
- `all_tables` only shows tables the current user can access
- Filters out system schemas (SYS, SYSTEM, APEX_*, etc.)
- Only includes schemas that have tables or views (table_count > 0 or view_count > 0)

### 2. Added Current User Indicator
```python
'is_current_user': (schema_name == current_user)
```
This helps identify which schema belongs to the connected user.

### 3. Better Logging
```python
logger.info(f"Found {len(schemas)} accessible schemas for user {current_user}")
```

## Benefits
✅ **Security**: Users only see schemas they have access to  
✅ **Usability**: Cleaner schema list without system schemas  
✅ **Performance**: No need for DBA privileges  
✅ **Accuracy**: Only shows schemas with actual data  

## Testing
To test the fix:

1. **Rebuild the Docker image:**
   ```powershell
   docker compose -f .\docker-compose.all.yml build databaseai
   ```

2. **Start the containers:**
   ```powershell
   docker compose -f .\docker-compose.all.yml up -d
   ```

3. **Connect to Oracle as pgaiview:**
   - Host: `oracle-db` (or `localhost` if not in Docker)
   - Port: `1521`
   - Service Name: `XEPDB1`
   - Username: `pgaiview`
   - Password: `pgaiview123`

4. **Expected Result:**
   - Should only show schemas that `pgaiview` has access to
   - Should see `PGAIVIEW` schema (owned by the user)
   - Should NOT see system schemas like SYS, SYSTEM, APEX_*, etc.
   - Should NOT see other user schemas unless explicitly granted access

## Database Views Used
- `all_tables` - Tables accessible to the current user
- `all_views` - Views accessible to the current user
- Both views automatically respect Oracle's privilege system

## Comparison: Before vs After

### Before (Using dba_users)
```
Schemas shown:
- SYS (system)
- SYSTEM (system)
- DBSNMP (monitoring)
- APEX_PUBLIC_USER (system)
- MDSYS (spatial data)
- ... 50+ system schemas
- PGAIVIEW (user schema) ✓
- Other users' schemas (no access) ✗
```

### After (Using all_tables)
```
Schemas shown:
- PGAIVIEW (user schema) ✓
- Any other schema explicitly granted access ✓
```

## Related Files
- `backend/app/database_adapters/oracle_adapter.py` - Main fix
- `docker-compose.all.yml` - Oracle test environment
- `init-oracle/01-create-users.sql` - Test user creation

## Notes
- The fix is backward compatible - admins with DBA privileges will see more schemas
- Regular users will only see their accessible schemas
- The `all_tables` view is available to all Oracle users
- No changes needed to frontend - schema list is automatically filtered
