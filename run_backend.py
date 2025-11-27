#!/usr/bin/env python3
"""
Start script for DatabaseAI backend
Run from the project root directory
"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    
    # Check if running as PyInstaller executable
    is_frozen = getattr(sys, 'frozen', False)
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False if is_frozen else True  # Disable reload for executable
    )
