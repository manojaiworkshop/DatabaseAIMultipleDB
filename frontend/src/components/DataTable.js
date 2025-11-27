import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, FileText, FileSpreadsheet, File, ChevronDown, Check } from 'lucide-react';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import * as XLSX from 'xlsx';

const DataTable = ({ columns, data, rowCount, executionTime }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Export column selection states
  const [showColumnSelector, setShowColumnSelector] = useState(false);
  const [selectedColumns, setSelectedColumns] = useState([...columns]);
  const [exportType, setExportType] = useState(null); // 'csv', 'excel', or 'pdf'
  const columnSelectorRef = useRef(null);

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!searchTerm.trim()) return data;
    
    const searchLower = searchTerm.toLowerCase();
    return data.filter(row => 
      columns.some(col => {
        const value = row[col];
        if (value === null || value === undefined) return false;
        return String(value).toLowerCase().includes(searchLower);
      })
    );
  }, [data, columns, searchTerm]);

  // Calculate pagination
  const totalPages = Math.ceil(filteredData.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentData = filteredData.slice(startIndex, endIndex);

  // Reset to page 1 when search changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  // Initialize selected columns when columns change
  useEffect(() => {
    setSelectedColumns([...columns]);
  }, [columns]);

  // Close column selector when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (columnSelectorRef.current && !columnSelectorRef.current.contains(event.target)) {
        setShowColumnSelector(false);
      }
    };

    if (showColumnSelector) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showColumnSelector]);

  const goToPage = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  // Column selection handlers
  const toggleColumn = (column) => {
    setSelectedColumns(prev => {
      if (prev.includes(column)) {
        // Don't allow deselecting all columns
        if (prev.length === 1) return prev;
        return prev.filter(col => col !== column);
      } else {
        return [...prev, column];
      }
    });
  };

  const selectAllColumns = () => {
    setSelectedColumns([...columns]);
  };

  const deselectAllColumns = () => {
    // Keep at least one column selected
    setSelectedColumns([columns[0]]);
  };

  // Open column selector for export
  const handleExportClick = (type) => {
    setExportType(type);
    setShowColumnSelector(true);
  };

  // Perform export with selected columns
  const performExport = () => {
    if (selectedColumns.length === 0) {
      alert('Please select at least one column to export');
      return;
    }

    setShowColumnSelector(false);

    switch (exportType) {
      case 'csv':
        exportToCSV(selectedColumns);
        break;
      case 'excel':
        exportToExcel(selectedColumns);
        break;
      case 'pdf':
        exportToPDF(selectedColumns);
        break;
      default:
        break;
    }
  };

  // Export functions with selected columns
  const exportToCSV = (exportColumns = columns) => {
    const headers = exportColumns.join(',');
    const rows = filteredData.map(row => 
      exportColumns.map(col => {
        const value = row[col];
        if (value === null || value === undefined) return '';
        // Escape commas and quotes
        const stringValue = String(value);
        if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      }).join(',')
    ).join('\n');
    
    const csv = `${headers}\n${rows}`;
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `database_export_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
  };

  const exportToExcel = (exportColumns = columns) => {
    // Create data with only selected columns
    const exportData = filteredData.map(row => {
      const newRow = {};
      exportColumns.forEach(col => {
        newRow[col] = row[col];
      });
      return newRow;
    });
    
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');
    XLSX.writeFile(workbook, `database_export_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  const exportToPDF = (exportColumns = columns) => {
    const doc = new jsPDF();
    
    // Add title
    doc.setFontSize(16);
    doc.text('Database Query Results', 14, 15);
    
    // Add metadata
    doc.setFontSize(10);
    doc.text(`Export Date: ${new Date().toLocaleString()}`, 14, 25);
    doc.text(`Total Rows: ${filteredData.length}`, 14, 31);
    doc.text(`Execution Time: ${executionTime.toFixed(3)}s`, 14, 37);
    doc.text(`Columns: ${exportColumns.join(', ')}`, 14, 43);
    
    // Add table
    doc.autoTable({
      head: [exportColumns],
      body: filteredData.map(row => exportColumns.map(col => row[col] ?? '')),
      startY: 48,
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: [59, 130, 246], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [245, 247, 250] },
      margin: { top: 48 },
    });
    
    doc.save(`database_export_${new Date().toISOString().slice(0, 10)}.pdf`);
  };

  const PageButton = ({ onClick, disabled, children, className = '' }) => (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`p-1.5 rounded hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors ${className}`}
    >
      {children}
    </button>
  );

  return (
    <div className="mt-4">
      {/* Header with info, export buttons, and search */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <span className="font-medium">
            {filteredData.length} {filteredData.length === 1 ? 'row' : 'rows'}
            {searchTerm && ` (filtered from ${data.length})`}
          </span>
          <span className="text-gray-400">•</span>
          <span>{executionTime.toFixed(3)}s</span>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full lg:w-auto">
          {/* Export Buttons with Column Selector */}
          <div className="relative flex items-center gap-1.5">
            <button
              onClick={() => handleExportClick('csv')}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="Export to CSV"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">CSV</span>
            </button>
            <button
              onClick={() => handleExportClick('excel')}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="Export to Excel"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Excel</span>
            </button>
            <button
              onClick={() => handleExportClick('pdf')}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              title="Export to PDF"
            >
              <File className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">PDF</span>
            </button>

            {/* Column Selector Dropdown */}
            {showColumnSelector && (
              <div 
                ref={columnSelectorRef}
                className="absolute top-full left-0 mt-2 w-80 bg-white border border-gray-300 rounded-lg shadow-lg z-50"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Header */}
                <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                  <h3 className="text-sm font-semibold text-gray-800 mb-1">
                    Select Columns to Export
                  </h3>
                  <p className="text-xs text-gray-600">
                    Exporting as {exportType?.toUpperCase()}
                  </p>
                </div>

                {/* Column List */}
                <div className="max-h-64 overflow-y-auto p-2">
                  {columns.map((column, index) => (
                    <label
                      key={index}
                      className="flex items-center gap-2 px-3 py-2 rounded hover:bg-gray-50 cursor-pointer group transition-colors"
                    >
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedColumns.includes(column)}
                          onChange={() => toggleColumn(column)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                        />
                        {selectedColumns.includes(column) && (
                          <Check className="absolute left-0.5 top-0.5 w-3 h-3 text-white pointer-events-none" />
                        )}
                      </div>
                      <span className="text-sm text-gray-700 font-medium group-hover:text-gray-900">
                        {column}
                      </span>
                    </label>
                  ))}
                </div>

                {/* Footer Actions */}
                <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 rounded-b-lg flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={selectAllColumns}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Select All
                    </button>
                    <span className="text-gray-300">|</span>
                    <button
                      onClick={deselectAllColumns}
                      className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowColumnSelector(false)}
                      className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={performExport}
                      disabled={selectedColumns.length === 0}
                      className="px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                      Export ({selectedColumns.length})
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search in results..."
              className="w-full pl-9 pr-3 py-1.5 text-xs border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col, i) => (
                <th
                  key={i}
                  className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentData.length > 0 ? (
              currentData.map((row, i) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  {columns.map((col, j) => (
                    <td key={j} className="px-4 py-2 text-xs text-gray-900 whitespace-nowrap">
                      {row[col] !== null && row[col] !== undefined ? (
                        <span>{String(row[col])}</span>
                      ) : (
                        <span className="text-gray-400 italic">NULL</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-500">
                  {searchTerm ? 'No results match your search' : 'No data available'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {filteredData.length > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-3">
          {/* Rows per page selector */}
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <span>Rows per page:</span>
            <select
              value={rowsPerPage}
              onChange={(e) => {
                setRowsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="border border-gray-300 rounded px-2 py-1 text-xs focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          {/* Page info and navigation */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600">
              {startIndex + 1}-{Math.min(endIndex, filteredData.length)} of {filteredData.length}
            </span>

            <div className="flex items-center gap-1 border border-gray-300 rounded-lg p-0.5">
              <PageButton
                onClick={() => goToPage(1)}
                disabled={currentPage === 1}
              >
                <ChevronsLeft className="w-4 h-4 text-gray-600" />
              </PageButton>
              
              <PageButton
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="w-4 h-4 text-gray-600" />
              </PageButton>

              {/* Page numbers */}
              <div className="flex items-center gap-1 px-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }

                  return (
                    <button
                      key={i}
                      onClick={() => goToPage(pageNum)}
                      className={`min-w-[24px] h-6 px-2 text-xs rounded transition-colors ${
                        currentPage === pageNum
                          ? 'bg-primary-500 text-white font-medium'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <PageButton
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                <ChevronRight className="w-4 h-4 text-gray-600" />
              </PageButton>

              <PageButton
                onClick={() => goToPage(totalPages)}
                disabled={currentPage === totalPages}
              >
                <ChevronsRight className="w-4 h-4 text-gray-600" />
              </PageButton>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;
