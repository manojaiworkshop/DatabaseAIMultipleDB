import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, CheckCircle } from 'lucide-react';

const TableSelectionModal = ({ isOpen, onClose, allTables, onSubmit }) => {
  const [availableTables, setAvailableTables] = useState([]);
  const [selectedTables, setSelectedTables] = useState([]);
  const [highlightedAvailable, setHighlightedAvailable] = useState([]);
  const [highlightedSelected, setHighlightedSelected] = useState([]);

  useEffect(() => {
    if (allTables && allTables.length > 0) {
      // Initialize with all tables in available list
      setAvailableTables(allTables);
      setSelectedTables([]);
    }
  }, [allTables]);

  if (!isOpen) return null;

  const handleAvailableClick = (tableName, isCtrlKey) => {
    if (isCtrlKey) {
      // Multi-select with Ctrl
      setHighlightedAvailable(prev => 
        prev.includes(tableName) 
          ? prev.filter(t => t !== tableName)
          : [...prev, tableName]
      );
    } else {
      setHighlightedAvailable([tableName]);
    }
  };

  const handleSelectedClick = (tableName, isCtrlKey) => {
    if (isCtrlKey) {
      // Multi-select with Ctrl
      setHighlightedSelected(prev => 
        prev.includes(tableName) 
          ? prev.filter(t => t !== tableName)
          : [...prev, tableName]
      );
    } else {
      setHighlightedSelected([tableName]);
    }
  };

  const moveToSelected = () => {
    const toMove = highlightedAvailable.length > 0 ? highlightedAvailable : [];
    if (toMove.length === 0) return;

    setSelectedTables(prev => [...prev, ...toMove].sort());
    setAvailableTables(prev => prev.filter(t => !toMove.includes(t)));
    setHighlightedAvailable([]);
  };

  const moveToAvailable = () => {
    const toMove = highlightedSelected.length > 0 ? highlightedSelected : [];
    if (toMove.length === 0) return;

    setAvailableTables(prev => [...prev, ...toMove].sort());
    setSelectedTables(prev => prev.filter(t => !toMove.includes(t)));
    setHighlightedSelected([]);
  };

  const moveAllToSelected = () => {
    setSelectedTables([...selectedTables, ...availableTables].sort());
    setAvailableTables([]);
    setHighlightedAvailable([]);
  };

  const moveAllToAvailable = () => {
    setAvailableTables([...availableTables, ...selectedTables].sort());
    setSelectedTables([]);
    setHighlightedSelected([]);
  };

  const handleSubmit = () => {
    if (selectedTables.length === 0) {
      alert('Please select at least one table');
      return;
    }
    onSubmit(selectedTables);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-500 to-primary-600 text-white px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Select Tables</h2>
            <p className="text-primary-100 text-sm mt-1">
              Choose which tables you want to work with
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Info Banner */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-800">
              <strong>Tip:</strong> Select tables from the left list and use the arrow buttons to move them to the right. 
              Hold <kbd className="px-2 py-1 bg-blue-100 rounded text-xs">Ctrl</kbd> to select multiple tables.
            </p>
          </div>

          {/* Selection Area */}
          <div className="grid grid-cols-[1fr_auto_1fr] gap-4 mb-6">
            {/* Available Tables */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Available Tables ({availableTables.length})
              </label>
              <div className="border-2 border-gray-300 rounded-lg h-96 overflow-y-auto bg-gray-50">
                {availableTables.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    All tables selected
                  </div>
                ) : (
                  <div className="p-2 space-y-1">
                    {availableTables.map((table) => (
                      <div
                        key={table}
                        onClick={(e) => handleAvailableClick(table, e.ctrlKey || e.metaKey)}
                        className={`px-3 py-2 rounded cursor-pointer transition-colors ${
                          highlightedAvailable.includes(table)
                            ? 'bg-primary-500 text-white'
                            : 'hover:bg-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{table}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Arrow Buttons */}
            <div className="flex flex-col items-center justify-center gap-2">
              <button
                onClick={moveAllToSelected}
                disabled={availableTables.length === 0}
                className="p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                title="Move all to selected"
              >
                <div className="flex items-center">
                  <ChevronRight className="w-5 h-5" />
                  <ChevronRight className="w-5 h-5 -ml-3" />
                </div>
              </button>
              <button
                onClick={moveToSelected}
                disabled={highlightedAvailable.length === 0}
                className="p-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                title="Move selected to right"
              >
                <ChevronRight className="w-6 h-6" />
              </button>
              <button
                onClick={moveToAvailable}
                disabled={highlightedSelected.length === 0}
                className="p-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                title="Move selected to left"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <button
                onClick={moveAllToAvailable}
                disabled={selectedTables.length === 0}
                className="p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                title="Move all to available"
              >
                <div className="flex items-center">
                  <ChevronLeft className="w-5 h-5" />
                  <ChevronLeft className="w-5 h-5 -ml-3" />
                </div>
              </button>
            </div>

            {/* Selected Tables */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selected Tables ({selectedTables.length})
              </label>
              <div className="border-2 border-primary-300 rounded-lg h-96 overflow-y-auto bg-primary-50">
                {selectedTables.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    No tables selected
                  </div>
                ) : (
                  <div className="p-2 space-y-1">
                    {selectedTables.map((table) => (
                      <div
                        key={table}
                        onClick={(e) => handleSelectedClick(table, e.ctrlKey || e.metaKey)}
                        className={`px-3 py-2 rounded cursor-pointer transition-colors ${
                          highlightedSelected.includes(table)
                            ? 'bg-primary-500 text-white'
                            : 'hover:bg-primary-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{table}</span>
                          <CheckCircle className="w-4 h-4 text-green-600" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t">
            <div className="text-sm text-gray-600">
              {selectedTables.length > 0 ? (
                <span className="font-medium text-primary-600">
                  {selectedTables.length} table{selectedTables.length !== 1 ? 's' : ''} selected
                </span>
              ) : (
                <span className="text-red-600">Please select at least one table</span>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-6 py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={selectedTables.length === 0}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
              >
                <CheckCircle className="w-5 h-5" />
                Continue with Selected Tables
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TableSelectionModal;
