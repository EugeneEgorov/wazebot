import os
import re
import logging
import requests
from urllib.parse import urlparse, parse_qs, unquote
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

# Read the bot token from the environment
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Please set the TELEGRAM_TOKEN environment variable.")

# Global variable to track browser health
BROWSER_HEALTHY = True

# ─── Regex patterns to find numeric coordinates in a Google Maps URL ───────────────
# 1) /@<lat>,<lon>,<zoom>/
# 2) ?api=1&query=<lat>,<lon>
# 3) !3d<lat>!4d<lon>
# 4) fallback: any "<lat>,<lon>" anywhere
COORD_PATTERN_AT   = re.compile(r"/@(-?\d+\.\d+),(-?\d+\.\d+),")
COORD_PATTERN_Q    = re.compile(r"[?&]query=(-?\d+\.\d+),(-?\d+\.\d+)")
COORD_PATTERN_BANG = re.compile(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)")
COORD_PATTERN_ANY  = re.compile(r"@?(-?\d+\.\d+),\s*(-?\d+\.\d+)")

# Pattern to extract place ID from Google Maps URLs
PLACE_ID_PATTERN = re.compile(r"1s0x[a-f0-9]+:0x[a-f0-9]+")

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def extract_coordinates_from_google_url(url: str) -> tuple[float, float] | None:
    """
    Attempt to extract a (lat, lon) pair from a Google Maps URL using multiple patterns:
      1. /@<lat>,<lon>,<zoom>/
      2. ?api=1&query=<lat>,<lon>
      3. !3d<lat>!4d<lon>
      4. Fallback: any "<lat>,<lon>" anywhere
    """
    # 1) /@LAT,LON,…
    match = COORD_PATTERN_AT.search(url)
    if match:
        return float(match.group(1)), float(match.group(2))

    # 2) ?api=1&query=LAT,LON
    match = COORD_PATTERN_Q.search(url)
    if match:
        return float(match.group(1)), float(match.group(2))

    # 3) !3dLAT!4dLON
    match = COORD_PATTERN_BANG.search(url)
    if match:
        return float(match.group(1)), float(match.group(2))

    # 4) Fallback: any "LAT,LON" in the URL
    match = COORD_PATTERN_ANY.search(url)
    if match:
        return float(match.group(1)), float(match.group(2))

    return None


def extract_place_id(url: str) -> str | None:
    """
    Extract place ID from a Google Maps URL.
    Place IDs look like: 1s0xd19337acbb1ab1b:0xeb80fb06738c323
    """
    match = PLACE_ID_PATTERN.search(url)
    if match:
        return match.group(0)
    return None


def strip_consent_url(url: str) -> str:
    """
    If the URL is a Google consent redirect (e.g. "https://consent.google.com/m?continue=<real_url>&..."),
    extract and return the <real_url> value. Otherwise, return the URL unchanged.
    """
    parsed = urlparse(url)
    if parsed.netloc.endswith("consent.google.com"):
        qs = parse_qs(parsed.query)
        if "continue" in qs:
            real_url = qs["continue"][0]
            return unquote(real_url)
    return url


def try_get_coordinates_from_place_url(url: str, headers: dict) -> tuple[float, float] | None:
    """
    Try to get coordinates from a Google Maps place URL by making additional requests
    and following redirects.
    """
    try:
        # First, try to make a request to the place URL
        logger.info(f"Making additional request to place URL: {url}")
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        final_url = resp.url
        logger.info(f"Place URL final redirect: {final_url}")
        
        # Strip consent from the final URL as well
        final_url = strip_consent_url(final_url)
        logger.info(f"After stripping consent from final URL: {final_url}")
        
        # Try to extract coordinates from the final URL
        coords = extract_coordinates_from_google_url(final_url)
        if coords:
            return coords
            
        # If that didn't work, try extracting place ID and use alternative approaches
        place_id = extract_place_id(url)
        if place_id:
            logger.info(f"Found place ID: {place_id}")
            
            # Try multiple alternative URL patterns
            alternative_urls = [
                f"https://maps.google.com/maps?cid={place_id.split(':')[1]}",
                f"https://www.google.com/maps/@?api=1&map_action=pano&pano={place_id}",
                f"https://www.google.com/maps/search/?api=1&query=place_id:{place_id}",
                f"https://maps.google.com/?q=place_id:{place_id}",
                f"https://www.google.com/maps/place/{place_id}",
            ]
            
            for alt_url in alternative_urls:
                try:
                    logger.info(f"Trying alternative URL: {alt_url}")
                    
                    # Try with different headers that might bypass consent
                    alt_headers = headers.copy()
                    alt_headers.update({
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'DNT': '1',
                        'Upgrade-Insecure-Requests': '1',
                    })
                    
                    resp = requests.get(alt_url, headers=alt_headers, timeout=10, allow_redirects=True)
                    final_url = resp.url
                    logger.info(f"Alternative URL final redirect: {final_url}")
                    
                    # Strip consent if present
                    final_url = strip_consent_url(final_url)
                    logger.info(f"After stripping consent: {final_url}")
                    
                    coords = extract_coordinates_from_google_url(final_url)
                    if coords:
                        logger.info(f"Success with alternative URL: {alt_url}")
                        return coords
                        
                except Exception as e:
                    logger.info(f"Alternative URL {alt_url} failed: {e}")
                    continue
        
        # Last resort: try to use Google's embed API which might work differently  
        if place_id:
            embed_url = f"https://www.google.com/maps/embed/v1/place?key=&q=place_id:{place_id}"
            try:
                logger.info(f"Trying embed URL: {embed_url}")
                resp = requests.get(embed_url, headers=headers, timeout=10, allow_redirects=True)
                final_url = resp.url
                logger.info(f"Embed URL final redirect: {final_url}")
                
                final_url = strip_consent_url(final_url)
                coords = extract_coordinates_from_google_url(final_url)
                if coords:
                    return coords
            except Exception as e:
                logger.info(f"Embed URL failed: {e}")
                
    except Exception as e:
        logger.error(f"Error in try_get_coordinates_from_place_url: {e}")
    
    return None


def extract_coordinates_from_place_url_params(url: str) -> tuple[float, float] | None:
    """
    Try to extract coordinates from URL parameters or fragments that might contain them.
    Some Google Maps URLs embed coordinates in different parts of the URL.
    """
    try:
        # Look for coordinates in various URL parameter patterns
        patterns_to_try = [
            # Look for !3d and !4d patterns in URL fragments
            r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)",
            # Look for coordinates in @ patterns 
            r"@(-?\d+\.\d+),(-?\d+\.\d+)",
            # Look for coordinates after equal signs
            r"=(-?\d+\.\d+),(-?\d+\.\d+)",
            # Look for coordinates in query parameters
            r"[?&](?:q|query|ll|center)=(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)",
        ]
        
        for pattern in patterns_to_try:
            matches = re.findall(pattern, url)
            if matches:
                # Take the first match
                lat, lon = matches[0]
                return float(lat), float(lon)
                
        # Also check URL fragments after # or data=
        if 'data=' in url:
            data_part = url.split('data=')[1].split('&')[0]
            # URL decode the data part
            from urllib.parse import unquote
            decoded_data = unquote(data_part)
            logger.info(f"Checking decoded data part: {decoded_data}")
            
            for pattern in patterns_to_try:
                matches = re.findall(pattern, decoded_data)
                if matches:
                    lat, lon = matches[0]
                    return float(lat), float(lon)
        
    except Exception as e:
        logger.error(f"Error in extract_coordinates_from_place_url_params: {e}")
    
    return None


def try_alternative_coordinate_resolution(place_id: str, headers: dict) -> tuple[float, float] | None:
    """
    Try alternative methods to resolve coordinates from a place ID.
    """
    try:
        # Method 1: Try using different Google domains that might not show consent
        alternative_domains = [
            "maps.googleapis.com",
            "maps.google.co.uk", 
            "maps.google.de",
            "maps.google.ca",
        ]
        
        for domain in alternative_domains:
            try:
                # Try the Maps API format that might work
                alt_url = f"https://{domain}/maps/api/place/details/json?place_id={place_id}&fields=geometry&key="
                logger.info(f"Trying alternative domain: {alt_url}")
                
                # Use minimal headers to avoid triggering consent
                minimal_headers = {
                    "User-Agent": "curl/7.68.0",
                    "Accept": "*/*"
                }
                
                resp = requests.get(alt_url, headers=minimal_headers, timeout=5)
                if resp.status_code == 200 and "geometry" in resp.text:
                    # Try to parse any coordinate-like numbers from the response
                    import json
                    try:
                        data = resp.json()
                        if "result" in data and "geometry" in data["result"]:
                            location = data["result"]["geometry"]["location"]
                            return float(location["lat"]), float(location["lng"])
                    except:
                        pass
                        
            except Exception as e:
                logger.info(f"Alternative domain {domain} failed: {e}")
                continue
        
        # Method 2: Try using a simple GET request with the place ID in a different format
        hex_parts = place_id.replace("1s", "").split(":")
        if len(hex_parts) == 2:
            try:
                # Sometimes we can construct a direct URL using the hex values
                hex1, hex2 = hex_parts
                simple_url = f"https://www.google.com/maps?cid={hex2}"
                logger.info(f"Trying simple CID URL: {simple_url}")
                
                # Use a very basic user agent
                basic_headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(simple_url, headers=basic_headers, timeout=5, allow_redirects=False)
                
                # Check if we get a redirect with coordinates
                if resp.status_code in [301, 302] and "Location" in resp.headers:
                    redirect_url = resp.headers["Location"]
                    logger.info(f"Got redirect: {redirect_url}")
                    coords = extract_coordinates_from_google_url(redirect_url)
                    if coords:
                        return coords
                        
            except Exception as e:
                logger.info(f"Simple CID method failed: {e}")
        
        # Method 3: Try a direct search approach
        try:
            search_url = f"https://www.google.com/search?q={place_id}+coordinates"
            logger.info(f"Trying search approach: {search_url}")
            
            search_headers = {
                "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
            }
            
            resp = requests.get(search_url, headers=search_headers, timeout=5)
            if resp.status_code == 200:
                # Look for coordinate patterns in the search results
                coords = extract_coordinates_from_google_url(resp.text)
                if coords:
                    return coords
                    
        except Exception as e:
            logger.info(f"Search method failed: {e}")
            
    except Exception as e:
        logger.error(f"Error in try_alternative_coordinate_resolution: {e}")
    
    return None


def try_direct_place_id_resolution(place_id: str) -> tuple[float, float] | None:
    """
    Try to resolve coordinates directly from a place ID by making targeted requests.
    Place IDs like 1s0xd1ecca7e6530079:0x7eb7624ea64a4a4a contain hex coordinates.
    """
    try:
        logger.info(f"Trying direct place ID resolution for: {place_id}")
        
        # Extract hex parts
        hex_parts = place_id.replace("1s", "").split(":")
        if len(hex_parts) != 2:
            return None
            
        hex1, hex2 = hex_parts
        logger.info(f"Extracted hex parts: {hex1}, {hex2}")
        
        # Try several direct approaches
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Method 1: Try direct CID redirect (most reliable)
        try:
            cid_url = f"https://www.google.com/maps?cid={hex2}"
            logger.info(f"Trying CID redirect: {cid_url}")
            
            resp = requests.get(cid_url, headers=headers, timeout=5, allow_redirects=False)
            if resp.status_code in [301, 302] and "Location" in resp.headers:
                redirect_url = resp.headers["Location"]
                logger.info(f"CID redirect location: {redirect_url}")
                
                if "consent.google.com" not in redirect_url:
                    coords = extract_coordinates_from_google_url(redirect_url)
                    if coords:
                        logger.info(f"Success with CID redirect: {coords}")
                        return coords
        except Exception as e:
            logger.info(f"CID redirect failed: {e}")
        
        # Method 2: Try alternative domain approaches
        alternative_domains = ["maps.google.co.uk", "maps.google.de", "maps.google.ca"]
        for domain in alternative_domains:
            try:
                alt_url = f"https://{domain}/maps?cid={hex2}"
                logger.info(f"Trying alternative domain: {alt_url}")
                
                resp = requests.get(alt_url, headers=headers, timeout=3, allow_redirects=False)
                if resp.status_code in [301, 302] and "Location" in resp.headers:
                    redirect_url = resp.headers["Location"]
                    if "consent.google.com" not in redirect_url:
                        coords = extract_coordinates_from_google_url(redirect_url)
                        if coords:
                            logger.info(f"Success with alternative domain {domain}: {coords}")
                            return coords
            except Exception as e:
                logger.info(f"Alternative domain {domain} failed: {e}")
                continue
        
        # Method 3: Try search approach
        try:
            search_url = f"https://www.google.com/search?q=site:maps.google.com+{hex2}"
            logger.info(f"Trying search approach: {search_url}")
            
            resp = requests.get(search_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                coords = extract_coordinates_from_google_url(resp.text)
                if coords:
                    logger.info(f"Success with search approach: {coords}")
                    return coords
        except Exception as e:
            logger.info(f"Search approach failed: {e}")
            
    except Exception as e:
        logger.error(f"Direct place ID resolution failed: {e}")
    
    return None


async def check_browser_health() -> bool:
    """
    Check if the headless browser is working properly.
    Returns True if browser works, False otherwise.
    """
    try:
        from playwright.async_api import async_playwright
        import asyncio
        
        logger.info("Testing headless browser health...")
        
        async def test_browser():
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--disable-javascript',
                            '--disable-gpu',
                            '--disable-software-rasterizer',
                            '--disable-background-timer-throttling',
                            '--disable-renderer-backgrounding',
                            '--disable-backgrounding-occluded-windows',
                            '--single-process',  # Help with server environments
                        ]
                    )
                    
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                        viewport={'width': 800, 'height': 600}
                    )
                    
                    page = await context.new_page()
                    
                    # Test with a simple page
                    await page.goto("https://www.google.com", timeout=5000)
                    title = await page.title()
                    
                    await browser.close()
                    
                    return "Google" in title
                    
            except Exception as e:
                logger.error(f"Browser test failed: {e}")
                return False
        
        # Run with 10 second timeout
        result = await asyncio.wait_for(test_browser(), timeout=10.0)
        logger.info(f"Browser health check: {'PASSED' if result else 'FAILED'}")
        return result
        
    except ImportError:
        logger.info("Playwright not installed - browser health check skipped")
        return False
    except asyncio.TimeoutError:
        logger.error("Browser health check timed out")
        return False
    except Exception as e:
        logger.error(f"Browser health check error: {e}")
        return False


async def try_headless_browser_resolution(url: str, browser_healthy: bool = True) -> tuple[float, float] | None:
    """
    Use a headless browser to load the Google Maps URL and extract coordinates
    from the final rendered page. This requires playwright to be installed.
    """
    if not browser_healthy:
        logger.info("Skipping headless browser - health check failed")
        return None
        
    try:
        # Try to import playwright - it may not be installed
        from playwright.async_api import async_playwright
        import asyncio
        
        logger.info("Attempting headless browser resolution...")
        
        # Set a maximum timeout for the entire operation
        async def browser_operation():
            browser = None
            try:
                async with async_playwright() as p:
                    # Try with JavaScript disabled first (faster)
                    for js_enabled in [False, True]:
                        try:
                            logger.info(f"Trying browser with JavaScript {'enabled' if js_enabled else 'disabled'}...")
                            
                            # Optimized browser args for server environments
                            browser_args = [
                                '--no-sandbox',
                                '--disable-dev-shm-usage',
                                '--disable-web-security',
                                '--disable-features=VizDisplayCompositor',
                                '--disable-extensions',
                                '--disable-plugins',
                                '--disable-images',  # Faster loading
                                '--disable-gpu',
                                '--disable-software-rasterizer',
                                '--disable-background-timer-throttling',
                                '--disable-renderer-backgrounding',
                                '--disable-backgrounding-occluded-windows',
                                '--disable-ipc-flooding-protection',
                                '--single-process',  # Important for server environments
                                '--no-zygote',  # Disable zygote process
                                '--disable-sync',
                                '--disable-default-apps',
                                '--no-first-run',
                                '--disable-crashpad',
                            ]
                            
                            if not js_enabled:
                                browser_args.append('--disable-javascript')
                            
                            browser = await p.chromium.launch(
                                headless=True, 
                                args=browser_args,
                                # Additional options for server environments
                                handle_sigint=False,
                                handle_sigterm=False,
                                handle_sighup=False,
                            )
                            
                            context = await browser.new_context(
                                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                viewport={'width': 800, 'height': 600},  # Smaller viewport
                                # Disable some features for performance
                                java_script_enabled=js_enabled,
                                bypass_csp=True,
                            )
                            
                            page = await context.new_page()
                            
                            try:
                                # Navigate to the URL with shorter timeout
                                logger.info(f"Loading URL: {url}")
                                await page.goto(url, wait_until="domcontentloaded", timeout=4000)  # Even shorter timeout
                                logger.info("Page loaded successfully")
                                
                                # Wait briefly for initial content
                                await page.wait_for_timeout(300)
                                
                                # Get the final URL immediately
                                final_url = page.url
                                logger.info(f"Final URL: {final_url}")
                                
                                # Try to extract coordinates from the final URL first
                                coords = extract_coordinates_from_google_url(final_url)
                                if coords:
                                    logger.info(f"Found coordinates in final URL: {coords}")
                                    return coords
                                
                                # Only try consent handling if JavaScript is enabled
                                if js_enabled:
                                    logger.info("Trying consent handling...")
                                    try:
                                        # Simple consent button detection with very short timeouts
                                        consent_selectors = [
                                            'button:has-text("Accept all")',
                                            'button:has-text("Aceitar")',
                                        ]
                                        
                                        for selector in consent_selectors:
                                            try:
                                                elements = await page.locator(selector).count()
                                                if elements > 0:
                                                    logger.info(f"Clicking consent button: {selector}")
                                                    await page.locator(selector).first.click(timeout=500)
                                                    await page.wait_for_timeout(800)
                                                    
                                                    final_url = page.url
                                                    logger.info(f"URL after consent: {final_url}")
                                                    
                                                    coords = extract_coordinates_from_google_url(final_url)
                                                    if coords:
                                                        logger.info(f"Found coordinates after consent: {coords}")
                                                        return coords
                                                    break
                                            except Exception as e:
                                                logger.info(f"Consent selector {selector} failed: {e}")
                                                continue
                                    except Exception as e:
                                        logger.info(f"Consent handling error: {e}")
                                
                                # Try page content as last resort (only if no JS, to avoid hanging)
                                if not js_enabled:
                                    try:
                                        page_content = await page.content()
                                        coords = extract_coordinates_from_google_url(page_content)
                                        if coords:
                                            logger.info(f"Found coordinates in page content: {coords}")
                                            return coords
                                    except Exception as e:
                                        logger.info(f"Page content extraction failed: {e}")
                                
                            except Exception as e:
                                logger.info(f"Page operation failed (JS {'on' if js_enabled else 'off'}): {e}")
                            finally:
                                if browser:
                                    await browser.close()
                                    browser = None
                                    
                        except Exception as e:
                            logger.info(f"Browser attempt failed (JS {'on' if js_enabled else 'off'}): {e}")
                            if browser:
                                try:
                                    await browser.close()
                                except:
                                    pass
                                browser = None
                            continue
                    
                    logger.info("No coordinates found with headless browser")
                    return None
                            
            except Exception as e:
                logger.error(f"Browser operation error: {e}")
                if browser:
                    try:
                        await browser.close()
                    except:
                        pass
                return None
        
        # Run the browser operation with a total timeout of 10 seconds (even shorter)
        try:
            logger.info("Starting browser operation with 10 second timeout...")
            coords = await asyncio.wait_for(browser_operation(), timeout=10.0)
            logger.info(f"Browser operation completed: {coords}")
            return coords
        except asyncio.TimeoutError:
            logger.error("Headless browser operation timed out after 10 seconds")
            return None
                
    except ImportError:
        logger.info("Playwright not installed. To use headless browser resolution, install with: pip install playwright")
        return None
    except Exception as e:
        logger.error(f"Headless browser resolution failed: {e}")
        return None


def try_geocoding_fallback(url: str) -> tuple[float, float] | None:
    """
    Try to extract business name and address from the URL and geocode it
    using a free geocoding service.
    """
    try:
        import urllib.parse
        import re
        
        # Extract business name and address from the URL path
        if '/place/' in url:
            place_part = url.split('/place/')[1].split('/')[0]
            # URL decode the place name
            place_name = urllib.parse.unquote_plus(place_part.replace('+', ' '))
            logger.info(f"Extracted place name: {place_name}")
            
            # Try to extract different components from the place name
            search_queries = [place_name]  # Always start with full name
            
            # Try to extract address components dynamically
            if ',' in place_name:
                parts = [part.strip() for part in place_name.split(',')]
                
                # Look for postal codes (format: NNNN-NNN)
                postal_code_pattern = r'\b\d{4}-\d{3}\b'
                
                # Try to find city/location names and postal codes
                for i, part in enumerate(parts):
                    # If this part contains a postal code, create address queries
                    if re.search(postal_code_pattern, part):
                        # This part likely contains city and postal code
                        if i > 0:
                            # Include the street part + city part
                            street_and_city = ', '.join(parts[i-1:i+1])
                            search_queries.append(f"{street_and_city}, Portugal")
                        
                        # Just the city part
                        search_queries.append(f"{part}, Portugal")
                
                # Try different combinations of parts
                if len(parts) >= 2:
                    # Last two parts (often street + city)
                    search_queries.append(f"{parts[-2]}, {parts[-1]}, Portugal")
                    
                    # Just the last part (often the city)
                    search_queries.append(f"{parts[-1]}, Portugal")
                
                # Try each part individually with Portugal
                for part in parts[1:]:  # Skip first part (business name)
                    if len(part.strip()) > 3:  # Only meaningful parts
                        search_queries.append(f"{part.strip()}, Portugal")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_queries = []
            for query in search_queries:
                if query not in seen:
                    seen.add(query)
                    unique_queries.append(query)
            
            headers = {
                "User-Agent": "TelegramBot/1.0 (contact@example.com)"  # Nominatim requires a user agent
            }
            
            for query in unique_queries:
                try:
                    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=3"
                    
                    logger.info(f"Trying Nominatim geocoding with query: {query}")
                    logger.info(f"URL: {nominatim_url}")
                    
                    resp = requests.get(nominatim_url, headers=headers, timeout=10)
                    logger.info(f"Nominatim response status: {resp.status_code}")
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        logger.info(f"Nominatim returned {len(data)} results")
                        
                        if data and len(data) > 0:
                            # Log all results for debugging
                            for i, result in enumerate(data):
                                logger.info(f"Result {i}: {result.get('display_name', 'No name')} - lat: {result.get('lat')}, lon: {result.get('lon')}")
                            
                            # Use the first result
                            result = data[0]
                            if 'lat' in result and 'lon' in result:
                                lat = float(result['lat'])
                                lon = float(result['lon'])
                                logger.info(f"Nominatim found coordinates: {lat}, {lon} for query: {query}")
                                return lat, lon
                        else:
                            logger.info(f"No results for query: {query}")
                    else:
                        logger.info(f"Bad response from Nominatim: {resp.status_code} - {resp.text[:200]}")
                        
                    # Add a small delay between requests to be nice to the service
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error with query '{query}': {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Geocoding fallback failed: {e}")
    
    return None


def extract_place_name(url: str) -> str | None:
    """
    Extract place name from a Google Maps URL.
    Returns the business/place name if found, None otherwise.
    """
    try:
        import urllib.parse
        
        if '/place/' in url:
            # Extract the place part from the URL
            place_part = url.split('/place/')[1].split('/')[0]
            # URL decode the place name
            place_name = urllib.parse.unquote_plus(place_part.replace('+', ' '))
            
            # If there's a comma, take only the first part (usually the business name)
            if ',' in place_name:
                business_name = place_name.split(',')[0].strip()
                # Only return if it's meaningful (not too short, not just numbers)
                if len(business_name) > 2 and not business_name.replace(' ', '').isdigit():
                    return business_name
            else:
                # No comma, return the whole name if meaningful
                if len(place_name) > 2 and not place_name.replace(' ', '').isdigit():
                    return place_name
                    
    except Exception as e:
        logger.info(f"Failed to extract place name: {e}")
    
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    if "maps.app.goo.gl/" not in text:
        return  # ignore if no Google Maps short link present

    short_url = text.split()[0]
    logger.info(f"Received short URL: {short_url}")

    try:
        # 1) GET with a browser User-Agent to force the full "@" or "!3d!4d" patterns
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(short_url, headers=headers, timeout=10, allow_redirects=True)
        expanded_url = resp.url
        logger.info(f"Expanded via GET (browser UA) → {expanded_url}")

        # 2) If Google shows a consent redirect, strip it out
        expanded_url = strip_consent_url(expanded_url)
        logger.info(f"After stripping consent, URL is → {expanded_url}")

    except Exception as e:
        logger.error(f"Error while expanding {short_url}: {e}")
        await update.message.reply_text("❗️ Couldn't expand that Google Maps link.")
        return

    # Extract place name for more informative responses
    place_name = extract_place_name(expanded_url)
    place_text = f" for {place_name}" if place_name else ""

    # 3) Try to parse numeric coordinates directly
    coords = extract_coordinates_from_google_url(expanded_url)
    if coords:
        lat, lon = coords
        logger.info(f"Parsed coordinates directly: lat={lat}, lon={lon}")
        waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
        await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
        return

    # 4) Try to extract coordinates from URL parameters/fragments
    logger.info("Direct coordinate parsing failed, trying URL parameter parsing...")
    coords = extract_coordinates_from_place_url_params(expanded_url)
    if coords:
        lat, lon = coords
        logger.info(f"Parsed coordinates from URL parameters: lat={lat}, lon={lon}")
        waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
        await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
        return

    # 5) Check if we're hitting consent pages - if so, skip HTTP methods and go to browser
    consent_detected = "consent.google.com" in resp.url or "consent.google.com" in expanded_url
    
    if consent_detected:
        logger.info("Consent pages detected - skipping HTTP methods, going directly to headless browser...")
        
        # Try direct place ID resolution first (faster than browser)
        place_id = extract_place_id(expanded_url)
        if place_id:
            logger.info("Trying direct place ID resolution...")
            coords = try_direct_place_id_resolution(place_id)
            if coords:
                lat, lon = coords
                logger.info(f"Parsed coordinates from direct place ID resolution: lat={lat}, lon={lon}")
                waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
                await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
                return
        
        # Try headless browser (most accurate)
        logger.info("Trying headless browser...")
        coords = await try_headless_browser_resolution(expanded_url, BROWSER_HEALTHY)
        if coords:
            lat, lon = coords
            logger.info(f"Parsed coordinates from headless browser: lat={lat}, lon={lon}")
            waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
            await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
            return
    else:
        # No consent detected - try a few quick HTTP methods before browser
        logger.info("No consent detected, trying quick HTTP methods...")
        
        # Try just one quick alternative URL
        place_id = extract_place_id(expanded_url)
        if place_id:
            hex_parts = place_id.replace("1s", "").split(":")
            if len(hex_parts) == 2:
                try:
                    hex1, hex2 = hex_parts
                    simple_url = f"https://www.google.com/maps?cid={hex2}"
                    logger.info(f"Trying simple CID URL: {simple_url}")
                    
                    basic_headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(simple_url, headers=basic_headers, timeout=3, allow_redirects=False)
                    
                    if resp.status_code in [301, 302] and "Location" in resp.headers:
                        redirect_url = resp.headers["Location"]
                        if "consent.google.com" not in redirect_url:
                            coords = extract_coordinates_from_google_url(redirect_url)
                            if coords:
                                lat, lon = coords
                                logger.info(f"Parsed coordinates from quick redirect: lat={lat}, lon={lon}")
                                waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
                                await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
                                return
                except Exception as e:
                    logger.info(f"Quick method failed: {e}")

            # If quick method didn't work, try comprehensive place ID resolution
            logger.info("Quick method failed, trying direct place ID resolution...")
            coords = try_direct_place_id_resolution(place_id)
            if coords:
                lat, lon = coords
                logger.info(f"Parsed coordinates from direct place ID resolution: lat={lat}, lon={lon}")
                waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
                await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
                return

        # Try headless browser (most accurate)
        logger.info("All quick methods failed, trying headless browser...")
        coords = await try_headless_browser_resolution(expanded_url, BROWSER_HEALTHY)
        if coords:
            lat, lon = coords
            logger.info(f"Parsed coordinates from headless browser: lat={lat}, lon={lon}")
            waze_link = f"https://ul.waze.com/ul?ll={lat},{lon}"
            await update.message.reply_text(f"Here's your Waze link{place_text}:\n{waze_link}")
            return

    logger.info("❌ Failed to parse coordinates from expanded URL using all methods.")
    await update.message.reply_text(
        "❗️ Couldn't parse coordinates from the Maps URL.\n"
        "Make sure the link contains numeric latitude/longitude or try a different link format."
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a Google Maps share link (maps.app.goo.gl/…), and I'll return a Waze link.\n"
        "Works with both coordinate links and place links!"
    )


def main() -> None:
    global BROWSER_HEALTHY
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Bot is starting...")
    
    # Check browser health on startup
    import asyncio
    try:
        logger.info("Performing browser health check...")
        BROWSER_HEALTHY = asyncio.run(check_browser_health())
        if BROWSER_HEALTHY:
            logger.info("✅ Browser is healthy - headless browser resolution enabled")
        else:
            logger.warning("⚠️ Browser health check failed - headless browser resolution disabled")
            logger.info("To fix this on a server, try running: playwright install-deps chromium")
    except Exception as e:
        logger.error(f"Browser health check error: {e}")
        BROWSER_HEALTHY = False
        logger.warning("⚠️ Browser health check failed - headless browser resolution disabled")
    
    logger.info("Starting bot polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
    