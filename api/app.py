"""
Re-export the single FastAPI app from api.routes for backward compatibility.
Use: from api.routes import app (or from api.app import app).
"""

from api.routes import app

__all__ = ["app"]
