"""
MovieBox Web - Server Entrypoint
Run this script to start the web streaming application:
    python run.py
"""

import sys
import os
import uvicorn

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    print("=" * 65)
    print(" 🎬 Room 206 - Cinema & Anime Streaming Platform")
    print(f" 🌐 Access Web UI: http://localhost:{port}")
    print(" ⚡ Powered by Room 206 High-Speed Native Stream Engine")
    print("=" * 65)
    
    uvicorn.run("app.server:app", host=host, port=port, reload=False, log_level="info")
