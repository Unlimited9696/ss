import trafilatura
import requests
import json
import re
import random
import time
import uuid
import logging
import urllib.parse
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Expanded list of User agents with mobile devices to avoid blocking
USER_AGENTS = [
    # Windows browsers
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.30',
    # macOS browsers
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    # Mobile browsers
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.58 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.58 Mobile Safari/537.36'
]

# List of common proxies (would need to be replaced with real rotating proxies in production)
# Note: For demo purposes only - these are placeholders
PROXY_LIST = [
    None,  # Direct connection without proxy (fallback)
]

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)

def create_robust_session():
    """
    Create a requests session with retry logic and random user agent
    
    Returns:
        requests.Session: Session with configured retry logic
    """
    session = requests.Session()
    
    # Set up retry strategy
    retry_strategy = Retry(
        total=3,  # Maximum number of retries
        backoff_factor=1,  # Time factor between retries
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        allowed_methods=["GET", "HEAD"]  # Apply retry to these methods
    )
    
    # Mount the adapter to the session
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set a random user agent
    session.headers.update({"User-Agent": get_random_user_agent()})
    
    return session

def get_with_fallback(url, timeout=15, use_proxy=False, max_attempts=3):
    """
    Make a GET request with fallback options and retries
    
    Args:
        url (str): URL to fetch
        timeout (int): Request timeout in seconds
        use_proxy (bool): Whether to use proxy
        max_attempts (int): Maximum number of attempts
        
    Returns:
        requests.Response or None: Response object or None if all attempts fail
    """
    attempts = 0
    session = create_robust_session()
    
    # Add random delay between attempts to avoid rate limiting
    if attempts > 0:
        time.sleep(random.uniform(1, 3))
    
    while attempts < max_attempts:
        try:
            # Rotate user agent between attempts
            session.headers.update({"User-Agent": get_random_user_agent()})
            
            # Add other headers to make request look more like a browser
            session.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
                'TE': 'Trailers',
                'DNT': '1'  # Do Not Track
            })
            
            # Add random cookies if needed
            cookies = {
                'session-id': str(uuid.uuid4()),
                'session-token': str(uuid.uuid4()),
                'ubid-main': str(uuid.uuid4()),
                'visitor-id': str(uuid.uuid4())
            }
            
            # Use proxy if specified
            proxies = None
            if use_proxy and PROXY_LIST:
                proxy = random.choice(PROXY_LIST)
                if proxy:
                    proxies = {
                        'http': proxy,
                        'https': proxy
                    }
            
            # Make the request with added randomization
            response = session.get(
                url,
                timeout=timeout,
                cookies=cookies,
                proxies=proxies,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response
                
            # Special handling for specific error codes
            if response.status_code == 503:
                logger.warning(f"Service unavailable (503) for {url}, retrying...")
                # Add longer delay for 503 errors (service unavailable)
                time.sleep(random.uniform(3, 5))
            elif response.status_code == 403:
                logger.warning(f"Forbidden (403) for {url}, retrying with different agent...")
                # Change approach for 403 (forbidden)
                session.headers.update({"User-Agent": get_random_user_agent()})
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {url}: {str(e)}")
        
        attempts += 1
    
    logger.error(f"All attempts failed for {url}")
    return None

def extract_clean_content(url):
    """
    Use trafilatura to extract clean content from a webpage
    
    Args:
        url (str): URL to extract content from
        
    Returns:
        str: Clean text content
    """
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Download the webpage
        downloaded = trafilatura.fetch_url(url)
        
        if not downloaded:
            # Fallback to requests if trafilatura fails
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                downloaded = response.text
            else:
                return None
        
        # Extract the main content
        text = trafilatura.extract(downloaded)
        return text
    
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return None

def get_amazon_in_products(query, limit=20):
    """
    Get products from Amazon India using enhanced scraping techniques
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        
    Returns:
        list: List of product dictionaries
    """
    try:
        # Encode the search query
        encoded_query = quote_plus(query)
        
        # Try different URLs to avoid detection
        urls = [
            f"https://www.amazon.in/s?k={encoded_query}",
            f"https://www.amazon.in/s?rh=k%3A{encoded_query}",
            f"https://www.amazon.in/s/ref=nb_sb_noss?field-keywords={encoded_query}"
        ]
        
        # Try each URL until one works
        response = None
        for url in urls:
            # Use our robust request handler with retries and random user agent
            response = get_with_fallback(url, timeout=20, max_attempts=3)
            if response:
                logger.info(f"Successfully fetched Amazon India results from {url}")
                break
        
        if not response:
            logger.error("Failed to fetch Amazon India results from all URLs")
            return []
            
        # Add a delay to avoid rate limiting for the next request
        time.sleep(random.uniform(0.5, 2.0))
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product containers
        products = []
        product_cards = soup.select('div[data-component-type="s-search-result"]')
        
        for card in product_cards[:limit]:
            try:
                # Extract product details
                product_id = card.get('data-asin', str(uuid.uuid4()))
                
                # Name
                name_element = card.select_one('h2 a span')
                name = name_element.text.strip() if name_element else 'Unknown Product'
                
                # URL - make sure it uses the Amazon India domain
                url_element = card.select_one('h2 a')
                if url_element and 'href' in url_element.attrs:
                    product_url = 'https://www.amazon.in' + url_element['href']
                else:
                    product_url = f"https://www.amazon.in/dp/{product_id}"
                
                # Price - handle Indian Rupee format
                price_element = card.select_one('span.a-price > span.a-offscreen')
                price_text = price_element.text.strip() if price_element else '₹0'
                
                # Clean up the price text and convert to float
                price_clean = re.sub(r'[^\d.]', '', price_text)
                price = float(price_clean) if price_clean else 0
                
                # Original price (if discounted)
                original_price_element = card.select_one('span.a-price.a-text-price > span.a-offscreen')
                original_price_text = original_price_element.text.strip() if original_price_element else price_text
                original_price_clean = re.sub(r'[^\d.]', '', original_price_text)
                original_price = float(original_price_clean) if original_price_clean else price
                
                # Calculate discount
                discount = round(((original_price - price) / original_price) * 100) if original_price > price else 0
                
                # Ratings and reviews
                rating_element = card.select_one('span[aria-label*="stars"]')
                rating_text = rating_element['aria-label'] if rating_element and 'aria-label' in rating_element.attrs else '0 stars'
                rating_match = re.search(r'([\d.]+)', rating_text)
                rating = float(rating_match.group(1)) if rating_match else 0
                
                reviews_element = card.select_one('span[aria-label*="stars"] + span')
                reviews_text = reviews_element.text.strip() if reviews_element else '0'
                reviews_clean = re.sub(r'[^\d]', '', reviews_text)
                reviews = int(reviews_clean) if reviews_clean else 0
                
                # Image URL - ensure we get a high-quality image
                image_element = card.select_one('img.s-image')
                image_url = ''
                if image_element and 'src' in image_element.attrs:
                    image_url = image_element['src']
                    # Try to get a larger image by modifying the URL
                    image_url = re.sub(r'_AC_UL\d+_', '_AC_UL500_', image_url)
                
                # Create product dict
                product = {
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': product_url,
                    'image_url': image_url,
                    'source': 'amazon',
                    'currency': '₹'  # Set to Indian Rupees
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Amazon India product: {str(e)}")
                continue
        
        return products
    
    except Exception as e:
        logger.error(f"Error scraping Amazon India: {str(e)}")
        return []

def get_flipkart_products(query, limit=20):
    """
    Get products from Flipkart using enhanced scraping techniques
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        
    Returns:
        list: List of product dictionaries
    """
    try:
        # Encode the search query
        encoded_query = quote_plus(query)
        
        # Try different URL formats to avoid detection
        urls = [
            f"https://www.flipkart.com/search?q={encoded_query}",
            f"https://www.flipkart.com/search?marketplace=FLIPKART&q={encoded_query}",
            f"https://www.flipkart.com/search?p%5B%5D=facets.brand%255B%255D%3D{encoded_query}"
        ]
        
        # Try each URL until one works
        response = None
        for url in urls:
            # Use our robust request handler with retries and random user agent
            response = get_with_fallback(url, timeout=20, max_attempts=3)
            if response:
                logger.info(f"Successfully fetched Flipkart results from {url}")
                break
        
        if not response:
            logger.error("Failed to fetch Flipkart results from all URLs")
            return []
            
        # Add a delay to avoid rate limiting for the next request
        time.sleep(random.uniform(0.5, 2.0))
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product containers
        products = []
        product_cards = soup.select('div._1AtVbE')
        
        for card in product_cards[:limit]:
            try:
                # Extract product details
                product_id = str(uuid.uuid4())  # Generate a unique ID for each product
                
                # Name - try different selectors for different page layouts
                name_element = card.select_one('div._4rR01T') or card.select_one('a.s1Q9rs') or card.select_one('a.IRpwTa')
                if not name_element:
                    continue  # Skip if no name found
                
                name = name_element.text.strip()
                
                # URL
                url_element = card.select_one('a._1fQZEK') or card.select_one('a.s1Q9rs') or card.select_one('a._2rpwqI')
                if url_element and 'href' in url_element.attrs:
                    product_url = 'https://www.flipkart.com' + url_element['href']
                else:
                    continue  # Skip if no URL found
                
                # Price - handle Indian Rupee format
                price_element = card.select_one('div._30jeq3')
                price_text = price_element.text.strip() if price_element else '₹0'
                price_clean = re.sub(r'[^\d.]', '', price_text)
                price = float(price_clean) if price_clean else 0
                
                # Original price (if discounted)
                original_price_element = card.select_one('div._3I9_wc')
                original_price_text = original_price_element.text.strip() if original_price_element else price_text
                original_price_clean = re.sub(r'[^\d.]', '', original_price_text)
                original_price = float(original_price_clean) if original_price_clean else price
                
                # Calculate discount
                discount_element = card.select_one('div._3Ay6Sb')
                if discount_element:
                    discount_text = discount_element.text.strip()
                    discount_clean = re.sub(r'[^\d]', '', discount_text)
                    discount = int(discount_clean) if discount_clean else 0
                else:
                    discount = round(((original_price - price) / original_price) * 100) if original_price > price else 0
                
                # Ratings and reviews
                rating_element = card.select_one('div._3LWZlK')
                rating = float(rating_element.text.strip()) if rating_element else 0
                
                reviews_element = card.select_one('span._2_R_DZ')
                reviews_text = reviews_element.text.strip() if reviews_element else '0'
                reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                reviews_clean = re.sub(r'[^\d]', '', reviews_match.group(1)) if reviews_match else '0'
                reviews = int(reviews_clean) if reviews_clean else 0
                
                # Image URL - ensure we get a high-quality image
                image_element = card.select_one('img._396cs4') or card.select_one('img._2r_T1I')
                image_url = ''
                if image_element and 'src' in image_element.attrs:
                    image_url = image_element['src']
                    # Try to get a larger image by modifying the URL
                    image_url = re.sub(r'_\d+\.', '_500.', image_url)
                
                # Create product dict
                product = {
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': product_url,
                    'image_url': image_url,
                    'source': 'flipkart',
                    'currency': '₹'  # Set to Indian Rupees
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Flipkart product: {str(e)}")
                continue
        
        return products
    
    except Exception as e:
        logger.error(f"Error scraping Flipkart: {str(e)}")
        return []

# Function to verify product URLs before returning them to the user
def verify_product_url(url, source):
    """
    Check if a product URL is valid by making a HEAD request
    
    Args:
        url (str): Product URL to verify
        source (str): Source website (amazon or flipkart)
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        # Create session with retry logic
        session = create_robust_session()
        
        try:
            # Try a HEAD request first (faster)
            response = session.head(
                url, 
                timeout=5, 
                allow_redirects=True
            )
            
            if response.status_code < 400:
                return True
                
        except requests.RequestException:
            # If HEAD fails, try GET with minimal data transfer
            try:
                response = session.get(
                    url,
                    timeout=5,
                    allow_redirects=True,
                    stream=True  # Don't download the entire content
                )
                
                # Just read a small portion to verify it's valid
                if response.status_code < 400:
                    # Read just the first 1KB to confirm it's valid content
                    for chunk in response.iter_content(chunk_size=1024):
                        break
                    response.close()
                    return True
                    
            except requests.RequestException:
                pass
        
        return False
        
    except Exception as e:
        logger.warning(f"Error verifying URL {url}: {str(e)}")
        return False