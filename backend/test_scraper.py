import asyncio
import logging
from backend.scraper import scrape_aliexpress
from backend.database import get_db_repository
from backend.config_loader import load_properties

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_scraper")

async def test():
    logger.info("Starting test scraper script...")
    
    # Load settings
    config = load_properties()
    keyword = config.get("search.keywords", "fidget slider")
    limit = config.get("max.products.per.day", 10)
    use_fallback = config.get("use.mock.fallback", True)
    db_type = config.get("database.type", "json")
    
    logger.info(f"Configuration - Keyword: '{keyword}', Limit: {limit}, Fallback: {use_fallback}, DB: {db_type}")
    
    # Run scrape
    products = await scrape_aliexpress(keyword, limit=limit, use_fallback=use_fallback)
    logger.info(f"Successfully scraped {len(products)} products.")
    
    # Instantiate repo and save
    repo = get_db_repository()
    new_saved = repo.save_posts(products)
    logger.info(f"Saved {new_saved} new posts to the '{db_type}' repository.")
    
    # Get latest
    latest = repo.get_latest_posts(limit=3)
    logger.info("Sample of latest posts saved:")
    for idx, post in enumerate(latest):
        logger.info(f"Post #{idx+1}: {post.get('title')} - Price: {post.get('price')} {post.get('currency')} - Rating: {post.get('rating')}")
        logger.info(f"  URL: {post.get('product_url')}")
        logger.info(f"  Image: {post.get('image_url')}")
        
    logger.info("Test completed successfully.")

if __name__ == "__main__":
    asyncio.run(test())
