# Schema Dropdown Feature Implementation

## Overview
Implemented a schema dropdown feature in the UI that allows users to select different database schemas and view their tables and views dynamically. The backend stores snapshots of each schema separately for efficient caching.

## Changes Made

### Backend Changes

#### 1. **Database Service Updates** (`backend/app/services/database.py`)

**New Instance Variables:**
```python
self.schema_snapshots = {}  # Store snapshots per schema: {schema_name: snapshot_data}
```

**New Methods:**

a) `get_all_schemas()` - Returns list of all user schemas (excluding system schemas)
   - Returns: `[{schema_name, table_count, view_count}, ...]`
   - Excludes: pg_catalog, information_schema, pg_toast

b) `get_schema_snapshot(schema_name: str)` - Returns snapshot for a specific schema
   - Fetches tables and views for the specified schema
   - Gets column details including primary keys
   - Caches results for 1 hour per schema
   - Returns: Full schema snapshot with tables, views, columns, and sample data

**Features:**
- ✅ Per-schema caching (1 hour TTL)
- ✅ Primary key detection
- ✅ Sample data (3 rows per table)
- ✅ View definitions included
- ✅ Efficient separate storage for each schema

#### 2. **API Routes** (`backend/app/routes/api.py`)

**New Endpoints:**

```python
GET /api/v1/database/schemas
```
- Returns list of all schemas with table/view counts
- Response: `{success: true, schemas: [...], total: n}`

```python
GET /api/v1/database/schemas/{schema_name}/snapshot
```
- Returns detailed snapshot for specific schema
- Response: `{success: true, snapshot: {...}}`

### Frontend Changes

#### 3. **API Service** (`frontend/src/services/api.js`)

**New Methods:**
```javascript
getAllSchemas() - Fetch all schemas
getSchemaSnapshot(schemaName) - Fetch specific schema snapshot
```

#### 4. **SchemaTreeView Component** (`frontend/src/components/SchemaTreeView.js`)

**Major Refactoring:**

**State Management:**
```javascript
const [schemas, setSchemas] = useState([]);
const [selectedSchema, setSelectedSchema] = useState(null);
const [schemaData, setSchemaData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
```

**New Features:**
- 🎯 **Schema Dropdown**: Dropdown beside "Database Schema" header
- 🔄 **Auto-fetch**: Automatically fetches all schemas on mount
- 🎨 **Smart Selection**: Auto-selects 'public' schema or first available
- ⚡ **Dynamic Loading**: Fetches schema-specific data on selection change
- 💾 **Backend Caching**: Leverages backend's per-schema caching
- 🔄 **Loading States**: Shows spinner while loading
- ❌ **Error Handling**: Graceful error display

**UI Components:**
```javascript
// Schema Dropdown (NEW)
<select value={selectedSchema} onChange={handleSchemaChange}>
  {schemas.map(schema => (
    <option>
      {schema.schema_name} ({schema.table_count} tables, {schema.view_count} views)
    </option>
  ))}
</select>

// Database Node displays selected schema
<span>{schemaData.schema_name || selectedSchema}</span>
```

**Props Removed:**
- ❌ `schema` prop - Component now self-manages data fetching
- ✅ `onCopy` prop - Remains for copying table/column names

#### 5. **ChatPage Component** (`frontend/src/pages/ChatPage.js`)

**Changes:**
```javascript
// OLD
<SchemaTreeView 
  schema={databaseSchema} 
  onCopy={handleSchemaCopy}
/>

// NEW
<SchemaTreeView 
  onCopy={handleSchemaCopy}
/>
```

- Removed `databaseSchema` state dependency
- Removed schema fetching logic from ChatPage
- Component is now self-contained

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Component Mount                                          │
│    SchemaTreeView → getAllSchemas()                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Backend: GET /database/schemas                          │
│    DatabaseService.get_all_schemas()                        │
│    → Returns: [{schema_name, table_count, view_count}]     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Frontend: Display Dropdown                               │
│    Auto-select 'public' or first schema                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. User Selects Schema                                      │
│    SchemaTreeView → getSchemaSnapshot(schema_name)          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Backend: GET /database/schemas/{name}/snapshot          │
│    DatabaseService.get_schema_snapshot(schema_name)         │
│    → Check cache (1hr TTL)                                  │
│    → If miss: Fetch from PostgreSQL                         │
│    → Store in schema_snapshots[schema_name]                 │
│    → Returns: Full snapshot with tables/views/columns       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Frontend: Render Tree                                    │
│    Display tables and views for selected schema             │
│    Reset expanded states on schema change                   │
└─────────────────────────────────────────────────────────────┘
```

## Schema Snapshot Structure

```json
{
  "database_name": "mydb",
  "schema_name": "public",
  "tables": [
    {
      "schema_name": "public",
      "table_name": "users",
      "full_name": "public.users",
      "columns": [
        {
          "column_name": "id",
          "data_type": "integer",
          "is_nullable": "NO",
          "column_default": "nextval('users_id_seq'::regclass)",
          "primary_key": true
        },
        {
          "column_name": "email",
          "data_type": "character varying",
          "is_nullable": "NO",
          "column_default": null,
          "primary_key": false
        }
      ],
      "sample_data": [
        {"id": 1, "email": "user@example.com"},
        {"id": 2, "email": "admin@example.com"}
      ]
    }
  ],
  "views": [
    {
      "schema_name": "public",
      "view_name": "active_users",
      "full_name": "public.active_users",
      "columns": [...],
      "definition": "SELECT * FROM users WHERE active = true"
    }
  ],
  "total_tables": 5,
  "total_views": 2,
  "timestamp": "2025-10-30T12:00:00"
}
```

## Benefits

### Performance
- ✅ **Cached Snapshots**: Each schema cached separately (1hr TTL)
- ✅ **On-Demand Loading**: Only fetch selected schema
- ✅ **Reduced Network**: No repeated fetches for same schema

### UX Improvements
- 🎯 **Schema Visibility**: See all schemas at a glance
- 📊 **Count Display**: Table/view counts in dropdown
- 🔄 **Smooth Transitions**: Loading states and error handling
- 🎨 **Clean Interface**: Dropdown integrated into tree header

### Scalability
- 📦 **Multi-Schema Support**: Works with any number of schemas
- 💾 **Efficient Storage**: Separate caching per schema
- 🔍 **Namespace Clarity**: Full schema-qualified names (schema.table)

## Testing Checklist

- [ ] Connect to database with multiple schemas
- [ ] Verify dropdown shows all schemas with counts
- [ ] Select different schemas and verify tables/views load
- [ ] Check caching works (subsequent selections are instant)
- [ ] Verify primary key detection (PK badge)
- [ ] Test copy functionality for table/column names
- [ ] Verify column detail modal works
- [ ] Check loading states and error handling
- [ ] Test with schemas having 0 tables/views
- [ ] Verify expand/collapse functionality per schema

## Future Enhancements

1. **Schema Search**: Filter schemas by name
2. **Favorite Schemas**: Pin frequently used schemas
3. **Schema Statistics**: Show data size, row counts
4. **Refresh Button**: Manual cache invalidation
5. **Schema Comparison**: Compare tables across schemas
6. **Export Schema**: Download schema definition as SQL/JSON

## Files Modified

### Backend
- `backend/app/services/database.py` - Added schema methods and caching
- `backend/app/routes/api.py` - Added new API endpoints

### Frontend
- `frontend/src/services/api.js` - Added API methods
- `frontend/src/components/SchemaTreeView.js` - Major refactoring with dropdown
- `frontend/src/pages/ChatPage.js` - Removed schema prop passing

### Backup
- `frontend/src/components/SchemaTreeView_backup.js` - Original component backup

## Example Usage

```javascript
// Frontend automatically handles everything:
// 1. Fetches schemas on mount
// 2. Auto-selects 'public' or first schema
// 3. User changes dropdown → fetches new schema
// 4. Caching handled by backend
// 5. Tree updates automatically

<SchemaTreeView onCopy={handleCopy} />
```

## Backend Cache Management

```python
# Per-schema cache with timestamps
self.schema_snapshots = {
  'public': {
    'data': {...},
    'timestamp': datetime(2025, 10, 30, 12, 0, 0)
  },
  'analytics': {
    'data': {...},
    'timestamp': datetime(2025, 10, 30, 12, 5, 0)
  }
}

# Cache TTL: 1 hour
# Cleared on: Connection change, manual clear
```

## Deployment Notes

1. **No Database Changes**: Only code changes, no migrations needed
2. **Backward Compatible**: Existing endpoints unchanged
3. **No Breaking Changes**: Chat functionality unaffected
4. **Frontend Build Required**: Run `npm run build` in frontend/
5. **Docker Rebuild**: Rebuild combined image for deployment

## Summary

This feature provides a professional, user-friendly way to navigate multi-schema databases with efficient caching and a clean UI. Users can now easily switch between schemas and explore their structure without performance degradation.
