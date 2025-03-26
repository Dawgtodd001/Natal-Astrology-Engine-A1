"""
Server startup script for Natal Astrology Engine
"""
import uvicorn

if __name__ == "__main__":
    # Run on port 8000 for backend
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
