import React, { useState } from 'react';
import { Database, Info } from 'lucide-react';

/**
 * SchemaTreeView Component
 * Displays database schema in a tree structure with database -> tables/views -> columns
 */
const SchemaTreeView = ({ schema, onCopy }) => {
  const [expandedDatabase, setExpandedDatabase] = useState(true);
  const [expandedTablesCategory, setExpandedTablesCategory] = useState(true);
  const [expandedViewsCategory, setExpandedViewsCategory] = useState(true);
  const [expandedTables, setExpandedTables] = useState(new Set());
  const [expandedViews, setExpandedViews] = useState(new Set());
  const [showColumnDetail, setShowColumnDetail] = useState(null);

  if (!schema) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Database className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No database connected</p>
        </div>
      </div>
    );
  }

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

  // Handle both array and object formats for tables
  const tablesArray = Array.isArray(schema.tables) 
    ? schema.tables 
    : Object.entries(schema.tables || {}).map(([name, data]) => ({
        table_name: name,
        columns: data.columns || []
      }));

  // Handle views
  const viewsArray = Array.isArray(schema.views) 
    ? schema.views 
    : Object.entries(schema.views || {}).map(([name, data]) => ({
        view_name: name,
        columns: data.columns || []
      }));

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-gray-50 to-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
          Database Schema
        </h3>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3">
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

            {/* Database Name */}
            <span className="font-semibold text-gray-800 text-base flex-1">
              {schema.database_name || 'Database'}
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

/**
 * TableNode Component
 * Represents a table with expand/collapse functionality
 */
const TableNode = ({ tableName, columns, isExpanded, onToggle, onCopy, onShowDetail }) => {
  // Truncate table name if too long
  const displayName = tableName.length > 25 ? tableName.substring(0, 25) + '...' : tableName;

  return (
    <div className="mb-1">
      <div
        className="flex items-center space-x-2 p-2 hover:bg-green-50 rounded-lg cursor-pointer transition-all group shadow-sm hover:shadow-md"
        onClick={onToggle}
      >
        {/* Expand Icon */}
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

        {/* Table Icon */}
        <svg className="h-4 w-4 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M5 4a3 3 0 00-3 3v6a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H5zm-1 9v-1h5v2H5a1 1 0 01-1-1zm7 1h4a1 1 0 001-1v-1h-5v2zm0-4h5V8h-5v2zM9 8H4v2h5V8z" clipRule="evenodd" />
        </svg>

        {/* Table Name */}
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

        {/* Column Count Badge */}
        <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full font-medium border border-green-200">
          {columns.length}
        </span>

        {/* Copy Icon (visible on hover) */}
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

      {/* Columns List */}
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
 * Represents a database view with expand/collapse functionality
 */
const ViewNode = ({ viewName, columns, isExpanded, onToggle, onCopy, onShowDetail }) => {
  // Truncate view name if too long
  const displayName = viewName.length > 25 ? viewName.substring(0, 25) + '...' : viewName;

  return (
    <div className="mb-1">
      <div
        className="flex items-center space-x-2 p-2 hover:bg-purple-50 rounded-lg cursor-pointer transition-all group shadow-sm hover:shadow-md"
        onClick={onToggle}
      >
        {/* Expand Icon */}
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

        {/* View Icon */}
        <svg className="h-4 w-4 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
          <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
        </svg>

        {/* View Name */}
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

        {/* Column Count Badge */}
        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full font-medium border border-purple-200">
          {columns.length}
        </span>

        {/* Copy Icon (visible on hover) */}
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

      {/* Columns List */}
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
 * Represents a single column (minimal display with detail icon)
 */
const ColumnNode = ({ column, onCopy, onShowDetail }) => {
  // Handle both object format and string format
  const columnName = typeof column === 'string' ? column : (column.column_name || column.name || 'unknown');
  const isPrimaryKey = typeof column === 'object' ? (column.primary_key || false) : false;
  
  // Truncate column name if too long
  const displayName = columnName.length > 20 ? columnName.substring(0, 20) + '...' : columnName;

  return (
    <div className="flex items-center space-x-2 p-1.5 pl-3 hover:bg-purple-50 rounded-md cursor-pointer group text-sm transition-all">
      {/* Column Icon */}
      <svg className="h-3 w-3 text-purple-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" />
      </svg>
      
      {/* Column Name */}
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
      
      {/* Primary Key Badge */}
      {isPrimaryKey && (
        <span className="text-xs bg-red-500 text-white px-1.5 py-0.5 rounded font-bold shadow-sm" title="Primary Key">
          PK
        </span>
      )}
      
      {/* Detail Icon (always visible) */}
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
      
      {/* Copy Icon (visible on hover) */}
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
 * Shows all details about a column in a modal
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
        {/* Header */}
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

        {/* Content */}
        <div className="space-y-3">
          {/* Column Name */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Column Name</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-sm text-gray-800">
              {columnName}
            </div>
          </div>

          {/* Data Type */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Data Type</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-sm text-gray-800">
              {columnType}
            </div>
          </div>

          {/* Nullable */}
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

          {/* Default Value */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Default Value</label>
            <div className="mt-1 p-2 bg-gray-50 rounded border border-gray-200 font-mono text-sm text-gray-800">
              {defaultValue}
            </div>
          </div>

          {/* Primary Key */}
          {isPrimaryKey && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <span className="text-red-600 font-semibold text-sm">🔑 Primary Key</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
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
