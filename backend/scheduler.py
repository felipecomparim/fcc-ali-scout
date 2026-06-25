import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.config_loader import load_properties
from backend.database import get_db_repository
from backend.scraper import scrape_aliexpress

logger = logging.getLogger("scheduler")

# Global scheduler state for status endpoint
scheduler_state = {
    "last_run": "Never",
    "next_run": "Starting...",
    "status": "Initializing",
    "is_scraping": False,
    "last_run_scraped_count": 0,
    "last_run_new_posts_count": 0,
    "error": None
}

# Future run controller
_next_run_time: datetime = None
_force_scrape_event = asyncio.Event()

async def run_scrape_cycle():
    """Runs a single scraping cycle for all configured keywords."""
    scheduler_state["is_scraping"] = True
    scheduler_state["status"] = "Scraping in progress"
    scheduler_state["error"] = None
    
    config = load_properties()
    keywords_str = config.get("search.keywords", "fidget slider")
    limit = config.get("max.products.per.day", 10)
    use_fallback = config.get("use.mock.fallback", True)
    
    # Split keywords by comma
    keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
    if not keywords:
        keywords = ["fidget slider"]
        
    logger.info(f"Starting scheduled scrape for keywords: {keywords}")
    
    total_scraped = 0
    total_new = 0
    
    try:
        repo = get_db_repository()
        
        for kw in keywords:
            # Scrape products for this keyword
            products = await scrape_aliexpress(kw, limit=limit, use_fallback=use_fallback)
            total_scraped += len(products)
            
            # Save to repository
            new_saved = repo.save_posts(products)
            total_new += new_saved
            logger.info(f"Keyword '{kw}': scraped {len(products)} products, saved {new_saved} new posts.")
            
        scheduler_state["last_run"] = datetime.now().isoformat()
        scheduler_state["last_run_scraped_count"] = total_scraped
        scheduler_state["last_run_new_posts_count"] = total_new
        scheduler_state["status"] = "Idle"
        
    except Exception as e:
        logger.error(f"Scheduler scraper cycle failed: {e}", exc_info=True)
        scheduler_state["error"] = str(e)
        scheduler_state["status"] = f"Error: {e}"
    finally:
        scheduler_state["is_scraping"] = False

async def trigger_manual_scrape() -> Dict[str, Any]:
    """Force-triggers the scraper immediately."""
    if scheduler_state["is_scraping"]:
        return {"status": "error", "message": "Scraper is already running."}
        
    logger.info("Manual scrape triggered.")
    _force_scrape_event.set()
    return {"status": "success", "message": "Scrape cycle triggered."}

async def scheduler_loop():
    """Background loop that monitors properties and runs periodic tasks."""
    global _next_run_time
    
    logger.info("Background scheduler starting...")
    scheduler_state["status"] = "Idle"
    
    # Initial delay before first scrape so startup is fast
    await asyncio.sleep(2)
    
    while True:
        # Load configuration
        config = load_properties()
        interval_minutes = int(config.get("scrape.interval.minutes", 60))
        
        # Calculate next run if not set
        if _next_run_time is None:
            _next_run_time = datetime.now()
            
        scheduler_state["next_run"] = _next_run_time.isoformat()
        
        # Check if we should scrape now (scheduled or forced)
        now = datetime.now()
        should_run = now >= _next_run_time or _force_scrape_event.is_set()
        
        if should_run:
            # Clear manual trigger if set
            is_forced = _force_scrape_event.is_set()
            _force_scrape_event.clear()
            
            logger.info(f"Triggering scrape cycle. Scheduled: {not is_forced}, Forced: {is_forced}")
            await run_scrape_cycle()
            
            # Recalculate next run time based on updated config
            _next_run_time = datetime.now() + timedelta(minutes=interval_minutes)
            scheduler_state["next_run"] = _next_run_time.isoformat()
            
        # Sleep in small chunks (e.g. 10 seconds) to stay responsive to force events and config reloads
        try:
            await asyncio.wait_for(_force_scrape_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            pass

def start_scheduler_task():
    """Launches the scheduler loop as a background task."""
    loop = asyncio.get_event_loop()
    return loop.create_task(scheduler_loop())
