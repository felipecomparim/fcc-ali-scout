import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List

from backend.config_loader import load_properties, save_properties
from backend.database import get_db_repository
from backend.scheduler import start_scheduler_task, trigger_manual_scrape, scheduler_state

# Initialize FastAPI
app = FastAPI(title="AliExpress Blog Scraper API")

# Setup CORS for development with React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files to serve images
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path, exist_ok=True)
    
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Pydantic schemas
class ConfigUpdate(BaseModel):
    keywords: str
    interval_minutes: int
    max_products: int
    use_fallback: bool
    database_type: str

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    # Start the background periodic scraper
    app.state.scheduler_task = start_scheduler_task()

@app.on_event("shutdown")
async def shutdown_event():
    # Cancel the scheduler background task on shutdown
    if hasattr(app.state, "scheduler_task"):
        app.state.scheduler_task.cancel()

# Endpoints
@app.get("/api/posts", response_model=List[Dict[str, Any]])
def get_posts():
    """Fetches the latest blog post products from the database, capped at 10 items (or configured limit)."""
    try:
        config = load_properties()
        limit = int(config.get("max.products.per.day", 10))
        repo = get_db_repository()
        posts = repo.get_latest_posts(limit=limit)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/api/scrape")
async def force_scrape():
    """Triggers the scraper immediately."""
    result = await trigger_manual_scrape()
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/api/config")
def get_config():
    """Retrieves current configuration property values."""
    config = load_properties()
    return {
        "keywords": config.get("search.keywords", "fidget slider"),
        "interval_minutes": int(config.get("scrape.interval.minutes", 60)),
        "max_products": int(config.get("max.products.per.day", 10)),
        "use_fallback": bool(config.get("use.mock.fallback", True)),
        "database_type": config.get("database.type", "json"),
        "database_path": config.get("database.path", "data/posts.json"),
        "sqlite_path": config.get("sqlite.path", "data/posts.db")
    }

@app.put("/api/config")
def update_config(data: ConfigUpdate):
    """Updates configuration parameters in config.properties."""
    try:
        current_config = load_properties()
        
        # Prepare properties mapping
        updated_properties = {
            "search.keywords": data.keywords,
            "scrape.interval.minutes": data.interval_minutes,
            "max.products.per.day": data.max_products,
            "use.mock.fallback": data.use_fallback,
            "database.type": data.database_type,
            # Maintain paths
            "database.path": current_config.get("database.path", "data/posts.json"),
            "sqlite.path": current_config.get("sqlite.path", "data/posts.db")
        }
        
        save_properties(updated_properties)
        return {"status": "success", "message": "Properties updated successfully.", "config": get_config()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving properties: {e}")

@app.get("/api/status")
def get_status():
    """Retrieves active running status of the background scraper thread."""
    config = load_properties()
    
    # Calculate post counts
    try:
        repo = get_db_repository()
        total_posts = len(repo.get_latest_posts(limit=1000))
    except Exception:
        total_posts = 0
        
    return {
        "scheduler": scheduler_state,
        "database": {
            "type": config.get("database.type", "json"),
            "total_posts_saved": total_posts
        }
    }

@app.post("/api/posts/clear")
def clear_posts():
    """Clears all posts. Utility endpoint for development."""
    try:
        repo = get_db_repository()
        repo.clear_posts()
        return {"status": "success", "message": "All posts cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing database: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
