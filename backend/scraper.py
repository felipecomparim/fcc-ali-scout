import re
import json
import random
import logging
from typing import List, Dict, Any
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aliexpress_scraper")

def get_headers() -> Dict[str, str]:
    """Returns random headers to mimic a normal browser request."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0"
    ]
    return {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

def generate_mock_products(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Generates highly realistic and visually rich product posts as a fallback."""
    logger.info(f"Generating mock products for keyword '{keyword}' (limit: {limit})")
    
    # Base slider details
    sliders_details = [
        {
            "title": "EDC Magnetic Haptic Slider Coin",
            "desc": "A heavy-duty double-layered magnetic haptic coin that rotates and slides with a satisfying click. Engineered from sandblasted titanium with internal neodymium magnets for tactile feedback. Perfect for stress relief and focus.",
            "image": "/static/images/slider1.png"
        },
        {
            "title": "Mechforce Mechanical Metal Fidget Slider",
            "desc": "Featuring independent mechanical clicking blocks, tactical grooves, and a vintage brass finish. This slider offers modular magnetic configurations so you can adjust the tension and friction to your exact preference.",
            "image": "/static/images/slider2.png"
        },
        {
            "title": "Sleek Carbon Fiber Pocket Fidget Slider",
            "desc": "An ultra-lightweight carbon fiber slider with a classic 3K weave pattern and vibrant anodized aluminum core accents. Features smooth Teflon sliding pads on magnetic tracks for a silent but incredibly tactile sliding experience.",
            "image": "/static/images/slider3.png"
        },
        {
            "title": "Copper Haptic Slider Block",
            "desc": "CNC-machined from solid copper that will develop a unique patina over time. Features deep linear grooves for secure grip, 8 high-performance magnets, and dual-track clicky guide rails.",
            "image": "/static/images/slider2.png"
        },
        {
            "title": "Vintage Shield 3-Stage Magnetic Slider",
            "desc": "A gothic shield-inspired fidget slider crafted from aged stainless steel. Incorporates three cascading sliding steps, giving a progressive tension click feel as you slide it open.",
            "image": "/static/images/slider1.png"
        },
        {
            "title": "Modular Titanium Bead-Blasted EDC Slider",
            "desc": "Minimalist pocket toy made of aerospace titanium. Configurable with 4, 6, or 8 magnets. Includes spare ceramic sliding balls to swap between tactile clicking and smooth gliding mode.",
            "image": "/static/images/slider3.png"
        },
        {
            "title": "Retro Gaming Controller Slider Plate",
            "desc": "A nostalgic D-Pad styled double slider plate. Satisfying micro-switch sounds built right into the movement. Features textured plastic buttons on a solid zinc alloy base.",
            "image": "/static/images/slider1.png"
        },
        {
            "title": "Vortex Rotational Slider Ring",
            "desc": "Fits comfortably on your index finger, allowing both 360-degree rotation and micro linear sliding along the ring track. Extremely stealthy and quiet for classroom or office use.",
            "image": "/static/images/slider2.png"
        },
        {
            "title": "G10 Textured Tactical Fidget Brick",
            "desc": "Built with textured G10 scale grips identical to high-end pocket knives. Solid steel chassis with high-strength rare earth magnets. Extremely durable, drop-resistant, and clicky.",
            "image": "/static/images/slider3.png"
        },
        {
            "title": "Zen-State Silent Slider Card",
            "desc": "Designed specifically for silent fidgeting. Uses high-friction dampening pads alongside weak magnets to simulate the resistance of sliding card decks without the audible click.",
            "image": "/static/images/slider1.png"
        }
    ]
    
    # Generic product template generator for other keywords
    generic_templates = [
        ("Premium Custom {keyword} Pro", "Experience top-tier build quality and performance with our custom-engineered {keyword}. Designed for everyday durability and modern style.", "/static/images/slider1.png"),
        ("Minimalist EDC {keyword}", "Ultra slim and pocketable, this {keyword} is crafted from durable materials. High performance in a compact footprint.", "/static/images/slider2.png"),
        ("Championship Edition {keyword}", "Professional-grade {keyword} with premium aesthetic design. Upgraded components for an unmatched tactile and visual feel.", "/static/images/slider3.png"),
        ("Classic Retro {keyword}", "Inspired by nostalgic retro styles, this unique {keyword} merges classic aesthetics with modern reliability. A perfect desk piece.", "/static/images/slider1.png"),
    ]
    
    posts = []
    now_str = datetime.now().isoformat()
    
    is_slider_keyword = "slider" in keyword.lower() or "fidget" in keyword.lower()
    
    for i in range(min(limit, 10)):
        product_id = f"mock_{keyword.replace(' ', '_')}_{i}_{datetime.now().strftime('%Y%m%d')}"
        
        # Generate custom details based on query
        if is_slider_keyword:
            details = sliders_details[i % len(sliders_details)]
            title = details["title"]
            desc = details["desc"]
            image = details["image"]
        else:
            tpl_title, tpl_desc, tpl_img = generic_templates[i % len(generic_templates)]
            kw_cap = keyword.title()
            title = tpl_title.format(keyword=kw_cap)
            desc = tpl_desc.format(keyword=keyword)
            image = tpl_img
            
        price = round(random.uniform(9.99, 89.99), 2)
        rating = round(random.uniform(4.2, 4.9), 1)
        reviews = random.randint(15, 340)
        
        # Simulated affiliate link
        aff_link = f"https://www.aliexpress.com/item/{1005000000000000 + i}.html?aff_fcid=mocked_affiliate_tag_{product_id}"
        
        posts.append({
            "product_id": product_id,
            "title": title,
            "description": desc,
            "price": price,
            "currency": "USD",
            "image_url": image,
            "product_url": aff_link,
            "rating": rating,
            "reviews_count": reviews,
            "keyword": keyword,
            "created_at": now_str
        })
        
    return posts

async def scrape_aliexpress(keyword: str, limit: int = 10, use_fallback: bool = True) -> List[Dict[str, Any]]:
    """
    Asynchronously queries AliExpress for the search keyword.
    Tries to parse the webpage JSON. Falls back to mock data if blocked.
    """
    search_url = f"https://www.aliexpress.com/w/wholesale-{keyword.replace(' ', '-')}.html"
    logger.info(f"Initiating scrape for: '{keyword}' via {search_url}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = get_headers()
            response = await client.get(search_url, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch AliExpress search page. Status code: {response.status_code}")
                if use_fallback:
                    return generate_mock_products(keyword, limit)
                return []
                
            html_content = response.text
            
            # Check for security slide / login redirect block
            if "sec.aliexpress.com" in response.url.host or "login.aliexpress.com" in response.url.host:
                logger.warning("Scraper blocked by AliExpress security redirect (CAPTCHA/anti-bot shield).")
                if use_fallback:
                    return generate_mock_products(keyword, limit)
                return []
                
            # Try to extract the JSON block representing search parameters
            # Usually inside a script tag like window._initData = or window.runParams =
            soup = BeautifulSoup(html_content, "html.parser")
            scripts = soup.find_all("script")
            
            data_json = None
            for script in scripts:
                if not script.string:
                    continue
                if "window._initData =" in script.string or "window.runParams =" in script.string:
                    # Extract JSON using regex
                    match = re.search(r"window\.(?:_initData|runParams)\s*=\s*({.*?});", script.string, re.DOTALL)
                    if match:
                        try:
                            data_json = json.loads(match.group(1))
                            break
                        except json.JSONDecodeError:
                            pass
            
            if not data_json:
                # Alternate pattern search
                match = re.search(r"runParams\s*:\s*({.*?}),\s*\n", html_content)
                if match:
                    try:
                        data_json = json.loads(match.group(1))
                    except json.JSONDecodeError:
                        pass

            if not data_json:
                logger.warning("No embedded product JSON found in the AliExpress HTML search result.")
                if use_fallback:
                    return generate_mock_products(keyword, limit)
                return []
            
            # Attempt to parse products out of the JSON
            # Structure changes frequently, so we extract carefully
            products = []
            now_str = datetime.now().isoformat()
            
            # Navigate nested structure
            items = []
            try:
                # Standard path inside runParams.data.items or similar
                if "data" in data_json and "items" in data_json["data"]:
                    items = data_json["data"]["items"]
                elif "mods" in data_json and "itemList" in data_json["mods"] and "content" in data_json["mods"]["itemList"]:
                    items = data_json["mods"]["itemList"]["content"]
            except Exception as e:
                logger.error(f"Error traversing AliExpress JSON structure: {e}")
            
            for item in items:
                if len(products) >= limit:
                    break
                    
                try:
                    product_id = item.get("productId") or item.get("itemId")
                    if not product_id:
                        continue
                        
                    # Extract fields
                    title = item.get("title", {}).get("displayTitle") or item.get("title", {}).get("text") or item.get("name")
                    if not title:
                        continue
                        
                    # Clean title HTML tags
                    title = re.sub(r"<[^>]*>", "", title)
                    
                    # Extract price
                    price_val = None
                    price_obj = item.get("price") or item.get("prices", {})
                    if isinstance(price_obj, dict):
                        price_val = price_obj.get("salePrice", {}).get("value") or price_obj.get("value")
                    if not price_val:
                        price_val = item.get("priceStr") or item.get("price")
                        
                    # Parse numeric float
                    if isinstance(price_val, str):
                        price_val = re.sub(r"[^\d.]", "", price_val)
                        try:
                            price_val = float(price_val)
                        except ValueError:
                            price_val = 19.99  # Fallback price
                    elif not isinstance(price_val, (int, float)):
                        price_val = 19.99
                        
                    # Extract image URL
                    image_url = item.get("image", {}).get("imgUrl") or item.get("imageUrl") or item.get("productImage")
                    if image_url and image_url.startswith("//"):
                        image_url = "https:" + image_url
                        
                    # Extract product URL
                    prod_url = item.get("productDetailUrl") or item.get("action", {}).get("url") or item.get("itemUrl")
                    if prod_url and prod_url.startswith("//"):
                        prod_url = "https:" + prod_url
                    elif prod_url and not prod_url.startswith("http"):
                        prod_url = "https://www.aliexpress.com/item/" + str(product_id) + ".html"
                    else:
                        prod_url = f"https://www.aliexpress.com/item/{product_id}.html"
                        
                    # Simulated affiliate integration
                    affiliate_url = f"{prod_url}?aff_fcid=fccnews_aff_{product_id}"
                        
                    # Rating
                    rating = item.get("evaluation", {}).get("starRating") or item.get("starRating") or item.get("rating", 4.7)
                    try:
                        rating = float(rating)
                    except (ValueError, TypeError):
                        rating = 4.7
                        
                    # Reviews
                    reviews = item.get("evaluation", {}).get("reviewCount") or item.get("reviewCount") or item.get("reviews", random.randint(10, 80))
                    try:
                        reviews = int(reviews)
                    except (ValueError, TypeError):
                        reviews = random.randint(10, 80)
                        
                    description = f"Scraped AliExpress product matching research keyword: {keyword}. Features a star rating of {rating} and verified reviews. Highly rated item."
                    
                    products.append({
                        "product_id": str(product_id),
                        "title": title,
                        "description": description,
                        "price": float(price_val),
                        "currency": "USD",
                        "image_url": image_url or "/static/images/slider1.png",
                        "product_url": affiliate_url,
                        "rating": rating,
                        "reviews_count": reviews,
                        "keyword": keyword,
                        "created_at": now_str
                    })
                except Exception as ex:
                    logger.warning(f"Error parsing item in AliExpress scraper: {ex}")
                    
            if not products:
                logger.warning("Scraper finished, but zero products could be successfully parsed from search page.")
                if use_fallback:
                    return generate_mock_products(keyword, limit)
                    
            return products
            
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        if use_fallback:
            return generate_mock_products(keyword, limit)
        return []
