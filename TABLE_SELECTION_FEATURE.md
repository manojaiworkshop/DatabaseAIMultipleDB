# Table Selection Feature - Complete Implementation

## Overview
Users can now select specific tables to work with after connecting to a database. This feature includes:
- Modal dialog with dual-pane table selection interface
- Multi-select with Ctrl/Cmd key support
- Arrow buttons to move tables between available and selected lists
- Filtered schema tree showing only selected tables
- Backend filtering of database snapshot

## Features Implemented

### 1. Backend Changes

#### DatabaseService (`backend/app/services/database.py`)
Added table filtering capability:

```python
def __init__(self):
    # ... existing code ...
    self.selected_tables = None  # Store user-selected tables

def set_selected_tables(self, table_names: List[str]):
    """Set the list of tables user wants to work with"""
    self.selected_tables = table_names
    self.schema_cache = None  # Clear cache

def get_selected_tables(self) -> Optional[List[str]]:
    """Get the list of selected tables"""
    return self.selected_tables

def clear_selected_tables(self):
    """Clear table selection (show all tables)"""
    self.selected_tables = None

def get_database_snapshot(self) -> Dict[str, Any]:
    # ... existing code ...
    
    # Filter by selected tables if user has made a selection
    if self.selected_tables is not None:
        filtered_tables = []
        for table in snapshot.get('tables', []):
            if (table.get('table_name') in self.selected_tables or 
                table.get('full_name') in self.selected_tables):
                filtered_tables.append(table)
        
        snapshot['tables'] = filtered_tables
        snapshot['total_tables'] = len(filtered_tables)
```

#### API Endpoints (`backend/app/routes/api.py`)

**POST /database/select-tables**
```python
@router.post("/database/select-tables")
async def select_tables(request: Dict[str, Any]):
    """
    Set which tables the user wants to work with
    Request body: { "tables": ["table1", "table2", ...] }
    """
    tables = request.get("tables", [])
    
    if len(tables) == 0:
        db_service.clear_selected_tables()
    else:
        db_service.set_selected_tables(tables)
    
    return {
        "success": True,
        "message": f"Selected {len(tables)} tables",
        "selected_count": len(tables)
    }
```

**GET /database/selected-tables**
```python
@router.get("/database/selected-tables")
async def get_selected_tables():
    """Get list of currently selected tables"""
    selected = db_service.get_selected_tables()
    
    return {
        "success": True,
        "selected_tables": selected if selected is not None else [],
        "is_filtered": selected is not None
    }
```

### 2. Frontend Changes

#### TableSelectionModal Component (`frontend/src/components/TableSelectionModal.js`)

New React component with features:
- **Dual-pane interface**: Available tables (left) and Selected tables (right)
- **Multi-select**: Click to select, Ctrl+Click for multiple selections
- **Arrow buttons**:
  - Single arrow (>) - Move highlighted tables to selected
  - Double arrow (>>) - Move all tables to selected
  - Single arrow (<) - Move highlighted tables back to available
  - Double arrow (<<) - Move all tables back to available
- **Visual feedback**: Selected items highlighted in blue
- **Count display**: Shows number of tables in each list
- **Submit validation**: Requires at least one table to be selected

#### ConnectionPage Updates (`frontend/src/pages/ConnectionPage.js`)

Modified connection flow:
```javascript
// After successful connection
if (response.success) {
  setSuccess(`Connected successfully!`);
  setConnectionResponse(response);
  setShowTableModal(true);  // Show modal instead of navigating directly
}

// Handle table selection
const handleTableSelection = async (selectedTables) => {
  await api.selectTables(selectedTables);
  
  // Filter schema by selected tables
  const filteredSchema = {
    ...schema,
    tables: schema.tables.filter(table => 
      selectedTables.includes(table.table_name) || 
      selectedTables.includes(table.full_name)
    ),
    total_tables: selectedTables.length
  };
  
  navigate('/chat', { 
    state: { 
      schema: filteredSchema,
      selectedTables: selectedTables
    } 
  });
};
```

#### API Service Updates (`frontend/src/services/api.js`)

Added new API methods:
```javascript
selectTables: async (tables) => {
  const response = await apiClient.post('/database/select-tables', { tables });
  return response.data;
},

getSelectedTables: async () => {
  const response = await apiClient.get('/database/selected-tables');
  return response.data;
},
```

## User Flow

### Step-by-Step Process

1. **Connect to Database**
   - User fills in connection details
   - Clicks "Connect to Database"
   - Backend establishes connection and fetches full schema

2. **Table Selection Modal Appears**
   - Modal shows all available tables in left pane
   - Right pane is empty (no tables selected yet)
   - User sees total count of available tables

3. **Select Tables**
   - Click individual tables to highlight them
   - Hold Ctrl/Cmd and click to select multiple tables
   - Click single arrow (>) to move highlighted tables to selected list
   - Or click double arrow (>>) to select all tables at once

4. **Deselect Tables (Optional)**
   - Click tables in the selected (right) pane
   - Click single arrow (<) to move them back to available
   - Or click double arrow (<<) to move all back

5. **Submit Selection**
   - Click "Continue with Selected Tables" button
   - Modal validates at least one table is selected
   - Backend stores the selection
   - User navigates to chat interface

6. **Chat Interface**
   - Schema tree shows ONLY selected tables
   - Queries are generated using only those tables
   - LLM context includes only selected table schemas

## Technical Details

### Backend Filtering Logic

The `get_database_snapshot()` method in `DatabaseService`:
1. Fetches complete schema from database adapter
2. Checks if `selected_tables` is set (not None)
3. If set, filters the tables list:
   - Compares against both `table_name` and `full_name`
   - Keeps only matching tables
   - Updates `total_tables` count
4. Returns filtered snapshot

### Frontend State Management

ConnectionPage maintains:
- `showTableModal`: Boolean to control modal visibility
- `connectionResponse`: Stores full connection response including schema
- `selectedTables`: List of table names user selected

ChatPage receives:
- `schema`: Filtered schema with only selected tables
- `databaseInfo`: Full database connection info
- `selectedTables`: List of selected table names

### Cache Management

When tables are selected:
- Backend clears `schema_cache` and `cache_timestamp`
- Next snapshot request fetches fresh data
- Filtered snapshot is then cached for 1 hour

## API Request/Response Examples

### Select Tables
**Request:**
```http
POST /api/v1/database/select-tables
Content-Type: application/json

{
  "tables": ["users", "orders", "products"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Selected 3 tables",
  "selected_count": 3
}
```

### Get Selected Tables
**Request:**
```http
GET /api/v1/database/selected-tables
```

**Response:**
```json
{
  "success": true,
  "selected_tables": ["users", "orders", "products"],
  "is_filtered": true
}
```

### Clear Selection (Show All Tables)
**Request:**
```http
POST /api/v1/database/select-tables
Content-Type: application/json

{
  "tables": []
}
```

**Response:**
```json
{
  "success": true,
  "message": "Table selection cleared, showing all tables"
}
```

## UI/UX Design

### Modal Layout
```
┌─────────────────────────────────────────────────────────┐
│  Select Tables                                      [X] │
├─────────────────────────────────────────────────────────┤
│  Choose which tables you want to work with              │
│                                                         │
│  ┌─────────────────┐  ┌────┐  ┌─────────────────┐     │
│  │ Available (25)  │  │ >> │  │ Selected (3)    │     │
│  ├─────────────────┤  │ >  │  ├─────────────────┤     │
│  │ □ customers     │  │    │  │ ☑ users   ✓    │     │
│  │ □ departments   │  │ <  │  │ ☑ orders  ✓    │     │
│  │ ☑ orders        │  │ << │  │ ☑ products ✓   │     │
│  │ ☑ products      │  └────┘  │                 │     │
│  │ ☑ users         │          │                 │     │
│  │ □ ...           │          │                 │     │
│  └─────────────────┘          └─────────────────┘     │
│                                                         │
│  3 tables selected           [Cancel] [Continue ✓]     │
└─────────────────────────────────────────────────────────┘
```

### Color Scheme
- Available pane: Gray background (#F9FAFB)
- Selected pane: Primary blue background (#EFF6FF)
- Highlighted items: Primary 500 blue (#3B82F6)
- Arrow buttons: Primary blue with hover effect

## Testing

### Test Scenarios

1. **Basic Selection**
   - Connect to database with 10+ tables
   - Select 3 tables using single arrow
   - Verify only 3 tables appear in chat

2. **Multi-Select**
   - Select multiple tables using Ctrl+Click
   - Move all at once with single arrow
   - Verify all moved correctly

3. **Select All/Deselect All**
   - Use double arrow (>>) to select all tables
   - Use double arrow (<<) to deselect all
   - Verify counts update correctly

4. **Selection Persistence**
   - Select tables and navigate to chat
   - Query should work with selected tables only
   - Schema tree shows filtered tables

5. **Error Handling**
   - Try to submit with no tables selected
   - Verify error message appears
   - Verify submit button is disabled

6. **Multiple Databases**
   - Connect to PostgreSQL with schema.table format
   - Connect to SQLite with simple table names
   - Verify both work correctly

## Benefits

1. **Performance**: Users work with subset of tables, reducing context size
2. **Focus**: Easier to find relevant tables in large databases
3. **Clarity**: Schema tree is less cluttered
4. **Flexibility**: Can change selection by reconnecting

## Future Enhancements

Potential improvements:
- Search/filter functionality in modal
- Save table selections as "views" or "workspaces"
- Remember last selection per database
- Show table row counts in modal
- Add table descriptions/comments

## Files Modified

### Backend
- `backend/app/services/database.py` - Added table filtering logic
- `backend/app/routes/api.py` - Added selection endpoints

### Frontend
- `frontend/src/components/TableSelectionModal.js` - New modal component
- `frontend/src/pages/ConnectionPage.js` - Show modal after connection
- `frontend/src/services/api.js` - Added API methods

## Configuration

No additional configuration needed. Feature works out of the box.

## Troubleshooting

### Modal doesn't appear
- Check browser console for errors
- Verify `showTableModal` state is being set to `true`
- Check that schema contains tables array

### Tables not filtering
- Verify `/database/select-tables` endpoint returns success
- Check backend logs for filtering messages
- Ensure table names match exactly (case-sensitive)

### Submit button disabled
- At least one table must be in the selected (right) pane
- Check `selectedTables.length > 0` condition

---

**Status**: ✅ Complete and Ready for Testing
**Version**: 1.0.0
**Date**: November 28, 2025
