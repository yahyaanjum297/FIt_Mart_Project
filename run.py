#!/usr/bin/env python3
"""
FitMart Backend Launcher
Run: python run.py
"""
import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] .env loaded")
except ImportError:
    print("[INFO] python-dotenv not installed, using system env vars")

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"\n{'='*52}")
    print(f"  FitMart Backend starting...")
    print(f"  API: http://localhost:{port}")
    print(f"  Docs: http://localhost:{port}/docs")
    print(f"  Health: http://localhost:{port}/health")
    print(f"{'='*52}\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
