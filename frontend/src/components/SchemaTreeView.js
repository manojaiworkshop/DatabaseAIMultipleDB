import React, { useState, useEffect } from 'react';
import { Database, Info, ChevronDown, Loader2 } from 'lucide-react';
import { api } from '../services/api';

/**
 * SchemaTreeView Component with Schema Dropdown
 * Displays database schema in a tree structure with schema selection
 */
const SchemaTreeView = ({ onCopy }) => {
  const [schemas, setSchemas] = useState([]);
  const [selectedSchema, setSelectedSchema] = useState(null);
  const [schemaData, setSchemaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [expandedDatabase, setExpandedDatabase] = useState(true);
  const [expandedTablesCategory, setExpandedTablesCategory] = useState(true);
  const [expandedViewsCategory, setExpandedViewsCategory] = useState(true);
  const [expandedTables, setExpandedTables] = useState(new Set());
  const [expandedViews, setExpandedViews] = useState(new Set());
  const [showColumnDetail, setShowColumnDetail] = useState(null);

  // Fetch all schemas on mount
  useEffect(() => {
    fetchSchemas();
  }, []);

  // Fetch schema snapshot when selection changes
  useEffect(() => {
    if (selectedSchema) {
      fetchSchemaSnapshot(selectedSchema);
    }
  }, [selectedSchema]);

  const fetchSchemas = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getAllSchemas();
      
      if (response.success && response.schemas) {
        setSchemas(response.schemas);
        
        // Auto-select first schema if available, or 'public' schema
        if (response.schemas.length > 0) {
          const publicSchema = response.schemas.find(s => s.schema_name === 'public');
          const defaultSchema = publicSchema || response.schemas[0];
          setSelectedSchema(defaultSchema.schema_name);
        }
      }
    } catch (err) {
      console.error('Failed to fetch schemas:', err);
      setError('Failed to load schemas');
    } finally {
      setLoading(false);
    }
  };

  const fetchSchemaSnapshot = async (schemaName) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getSchemaSnapshot(schemaName);
      
      if (response.success && response.snapshot) {
        setSchemaData(response.snapshot);
        // Reset expanded states when switching schemas
        setExpandedTables(new Set());
        setExpandedViews(new Set());
      }
    } catch (err) {
      console.error('Failed to fetch schema snapshot:', err);
      setError(`Failed to load schema: ${schemaName}`);
      setSchemaData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSchemaChange = (e) => {
    setSelectedSchema(e.target.value);
  };

  const toggleTable = (tableIndex) => {
    const newExpanded = new Set(expandedTables);
    if (newExpanded.has(tableIndex)) {
      newExpanded.delete(tableIndex);
    } else {
      newExpanded.add(tableIndex);
    }
    setExpandedTables(newExpanded);
  };

  const toggleView = (viewIndex) => {
    const newExpanded = new Set(expandedViews);
    if (newExpanded.has(viewIndex)) {
      newExpanded.delete(viewIndex);
    } else {
      newExpanded.add(viewIndex);
    }
    setExpandedViews(newExpanded);
  };

  if (loading && !schemaData) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Loader2 className="h-12 w-12 mx-auto mb-2 opacity-50 animate-spin" />
          <p>Loading schemas...</p>
        </div>
      </div>
    );
  }

  if (error && schemas.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Database className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p className="text-red-500">{error}</p>
        </div>
      </div>
    );
  }

  // Handle both array and object formats for tables
  const tablesArray = schemaData?.tables || [];
  const viewsArray = schemaData?.views || [];

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
          Database Schema
        </h3>
        
        {/* Schema Dropdown */}
        <div className="relative">
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Select Schema
          </label>
          <div className="relative">
            <select
              value={selectedSchema || ''}
              onChange={handleSchemaChange}
              className="w-full px-3 py-2 pr-8 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none cursor-pointer hover:border-blue-400 transition-colors"
              disabled={loading}
            >
              {schemas.map((schema) => (
                <option key={schema.schema_name} value={schema.schema_name}>
                  {schema.schema_name} ({schema.table_count} tables, {schema.view_count} views)
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3">
        {loading && schemaData ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          </div>
        ) : schemaData ? (
          <>
            {/* Database Node (Root) */}
            <div className="mb-2">
              <div
                className="flex items-center space-x-2 p-2.5 hover:bg-blue-50 rounded-lg cursor-pointer transition-all group shadow-sm hover:shadow-md"
                onClick={() => setExpandedDatabase(!expandedDatabase)}
              >
                {/* Expand Icon */}
                <button className="focus:outline-none text-gray-600 hover:text-blue-600 transition-colors">
                  {expandedDatabase ? (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>

                {/* Database Icon */}
                <Database className="h-5 w-5 text-blue-600 flex-shrink-0" />

                {/* Schema Name */}
                <span className="font-semibold text-gray-800 text-base flex-1">
                  {schemaData.schema_name || selectedSchema}
                </span>

                {/* Total Count Badge */}
                <span className="text-xs bg-blue-100 text-blue-800 px-2.5 py-1 rounded-full font-medium border border-blue-200 shadow-sm">
                  {tablesArray.length + viewsArray.length} items
                </span>
              </div>

              {/* Tables and Views Categories */}
              {expandedDatabase && (
                <div className="ml-4 mt-1 space-y-1">
                  {/* Tables Category */}
                  <div className="mb-2">
                    <div
                      className="flex items-center space-x-2 p-2 hover:bg-green-50 rounded-lg cursor-pointer transition-all group"
                      onClick={() => setExpandedTablesCategory(!expandedTablesCategory)}
                    >
                      {/* Expand Icon */}
                      <button className="focus:outline-none text-gray-600 hover:text-green-600 transition-colors">
                        {expandedTablesCategory ? (
                          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>

                      {/* Tables Icon */}
                      <svg className="h-4 w-4 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 6a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2zm0 6a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z" clipRule="evenodd" />
                      </svg>

                      {/* Category Name */}
                      <span className="font-semibold text-gray-700 text-sm flex-1">
                        Tables
                      </span>

                      {/* Table Count Badge */}
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full font-medium border border-green-200">
                        {tablesArray.length}
                      </span>
                    </div>

                    {/* Tables List */}
                    {expandedTablesCategory && (
                      <div className="ml-4 mt-1 space-y-1">
                        {tablesArray.map((table, index) => {
                          const tableName = table.table_name || `Table ${index + 1}`;
                          return (
                            <TableNode
                              key={`table-${index}`}
                              tableName={tableName}
                              columns={table.columns || []}
                              isExpanded={expandedTables.has(index)}
                              onToggle={() => toggleTable(index)}
                              onCopy={onCopy}
                              onShowDetail={setShowColumnDetail}
                            />
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Views Category */}
                  {viewsArray.length > 0 && (
                    <div className="mb-2">
                      <div
                        className="flex items-center space-x-2 p-2 hover:bg-purple-50 rounded-lg cursor-pointer transition-all group"
                        onClick={() => setExpandedViewsCategory(!expandedViewsCategory)}
                      >
                        {/* Expand Icon */}
                        <button className="focus:outline-none text-gray-600 hover:text-purple-600 transition-colors">
                          {expandedViewsCategory ? (
                            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>

                        {/* Views Icon */}
                        <svg className="h-4 w-4 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                          <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                        </svg>

                        {/* Category Name */}
                        <span className="font-semibold text-gray-700 text-sm flex-1">
                          Views
                        </span>

                        {/* View Count Badge */}
                        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full font-medium border border-purple-200">
                          {viewsArray.length}
                        </span>
                      </div>

                      {/* Views List */}
                      {expandedViewsCategory && (
                        <div className="ml-4 mt-1 space-y-1">
                          {viewsArray.map((view, index) => {
                            const viewName = view.view_name || `View ${index + 1}`;
                            return (
                              <ViewNode
                                key={`view-${index}`}
                                viewName={viewName}
                                columns={view.columns || []}
                                isExpanded={expandedViews.has(index)}
                                onToggle={() => toggleView(index)}
                                onCopy={onCopy}
                                onShowDetail={setShowColumnDetail}
                              />
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <Database className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Select a schema to view</p>
            </div>
          </div>
        )}
      </div>

      {/* Column Detail Modal */}
      {showColumnDetail && (
        <ColumnDetailModal
          column={showColumnDetail}
          onClose={() => setShowColumnDetail(null)}
        />
      )}
    </div>
  );
};

// TableNode, ViewNode, ColumnNode, and ColumnDetailModal components remain the same
// (Copying from original file for completeness)

/**
 * TableNode Component
 */
const TableNode = ({ tableName, columns, isExpanded, onToggle, onCopy, onShowDetail }) => {
  const displayName = tableName.length > 25 ? tableName.substring(0, 25) + '...' : tableName;

  return (
    <div className="mb-1">
      <div
        className="flex items-center space-x-2 p-2 hover:bg-green-50 rounded-lg cursor-pointer transition-all group shadow-sm hover:shadow-md"
        onClick={onToggle}
      >
        <button className="focus:outline-none text-gray-600 hover:text-green-600 transition-colors">
          {isExpanded ? (
            <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          )}
        </button>
        <svg className="h-4 w-4 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 4a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm-1 9v-1h5v2H5a1 1 0 01-1-1zm7 1h4a1 1 0 001-1v-1h-5v2zm0-4h5V8h-5v2zM9 8H4v2h5V8z" clipRule="evenodd" />
        </svg>
        <span
          className="font-medium text-gray-700 truncate flex-1 hover:text-green-600 text-sm"
          onClick={(e) => {
            e.stopPropagation();
            if (onCopy) onCopy(tableName, 'table');
          }}
          title={tableName}
        >
          {displayName}
        </span>
        <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full font-medium border border-green-200">
          {columns.length}
        </span>
        <button
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            if (onCopy) onCopy(tableName, 'table');
          }}
          title="Copy table name"
        >
          <svg className="h-3.5 w-3.5 text-gray-500 hover:text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
      {isExpanded && (
        <div className="ml-7 mt-1 space-y-0.5 pl-2 border-l-2 border-green-200">
          {columns.length === 0 ? (
            <div className="text-xs text-gray-500 italic py-2 pl-2">No columns</div>
          ) : (
            columns.map((column, idx) => (
              <ColumnNode
                key={idx}
                column={column}
                onCopy={onCopy}
                onShowDetail={onShowDetail}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ViewNode Component
 */
const ViewNode = ({ viewName, columns, isExpanded, onToggle, onCopy, onShowDetail }) => {
  const displayName = viewName.length > 25 ? viewName.substring(0, 25) + '...' : viewName;

  return (
    <div className="mb-1">
      <div
        className="flex items-center space-x-2 p-2 hover:bg-purple-50 rounded-lg cursor-pointer transition-all group shadow-sm hover:shadow-md"
        onClick={onToggle}
      >
        <button className="focus:outline-none text-gray-600 hover:text-purple-600 transition-colors">
          {isExpanded ? (
            <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          )}
        </button>
        <svg className="h-4 w-4 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
          <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
        </svg>
        <span
          className="font-medium text-gray-700 truncate flex-1 hover:text-purple-600 text-sm"
          onClick={(e) => {
            e.stopPropagation();
            if (onCopy) onCopy(viewName, 'view');
          }}
          title={viewName}
        >
          {displayName}
        </span>
        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full font-medium border border-purple-200">
          {columns.length}
        </span>
        <button
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            if (onCopy) onCopy(viewName, 'view');
          }}
          title="Copy view name"
        >
          <svg className="h-3.5 w-3.5 text-gray-500 hover:text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
      {isExpanded && (
        <div className="ml-7 mt-1 space-y-0.5 pl-2 border-l-2 border-purple-200">
          {columns.length === 0 ? (
            <div className="text-xs text-gray-500 italic py-2 pl-2">No columns</div>
          ) : (
            columns.map((column, idx) => (
              <ColumnNode
                key={idx}
                column={column}
                onCopy={onCopy}
                onShowDetail={onShowDetail}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ColumnNode Component
 */
const ColumnNode = ({ column, onCopy, onShowDetail }) => {
  const columnName = typeof column === 'string' ? column : (column.column_name || column.name || 'unknown');
  const isPrimaryKey = typeof column === 'object' ? (column.primary_key || false) : false;
  const displayName = columnName.length > 20 ? columnName.substring(0, 20) + '...' : columnName;

  return (
    <div className="flex items-center space-x-2 p-1.5 pl-3 hover:bg-purple-50 rounded-md cursor-pointer group text-sm transition-all">
      <svg className="h-3 w-3 text-purple-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" />
      </svg>
      <span
        className="text-gray-700 truncate flex-1 hover:text-purple-700 font-mono text-xs font-medium transition-colors"
        onClick={(e) => {
          e.stopPropagation();
          if (onCopy) onCopy(columnName, 'column');
        }}
        title={columnName}
      >
        {displayName}
      </span>
      {isPrimaryKey && (
        <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded font-bold shadow-sm" title="Primary Key">
          PK
        </span>
      )}
      <button
        className="opacity-70 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          if (onShowDetail) onShowDetail(column);
        }}
        title="View column details"
      >
        <Info className="h-3.5 w-3.5 text-purple-600 hover:text-purple-800" />
      </button>
      <button
        className="opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          if (onCopy) onCopy(columnName, 'column');
        }}
        title="Copy column name"
      >
        <svg className="h-3 w-3 text-gray-500 hover:text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </button>
    </div>
  );
};

/**
 * ColumnDetailModal Component
 */
const ColumnDetailModal = ({ column, onClose }) => {
  const columnName = column.column_name || column.name || 'Unknown';
  const columnType = column.data_type || column.type || 'unknown';
  const isNullable = column.is_nullable === 'YES' || column.nullable !== false;
  const defaultValue = column.column_default || column.default || 'None';
  const isPrimaryKey = column.primary_key || false;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-2xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center">
            <Info className="h-5 w-5 mr-2 text-purple-600" />
            Column Details
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Column Name</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-sm text-gray-800">
              {columnName}
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Data Type</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-sm text-gray-800">
              {columnType}
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Nullable</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                isNullable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isNullable ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Default Value</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-sm text-gray-800">
              {defaultValue}
            </div>
          </div>
          {isPrimaryKey && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <span className="text-red-600 font-semibold text-sm">🔑 Primary Key</span>
              </div>
            </div>
          )}
        </div>
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SchemaTreeView;
