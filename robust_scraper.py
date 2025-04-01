"""
Enhanced web scraper for price tracking applications.
Uses Trafilatura for better content extraction and has robust fallback mechanisms.
"""
import json
import random
import re
import time
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime

import requests
import trafilatura
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of user agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
]

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)

def extract_price(price_text):
    """Extract numeric price value from text containing ₹ symbol and commas"""
    if not price_text:
        return 0
        
    # Extract digits, commas, and decimal points
    price_str = ''.join(re.findall(r'[\d,\.]+', price_text.replace(',', '')))
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return 0

def create_robust_session(max_retries=3, timeout=10):
    """
    Create a requests session with retry logic, random user agent and other anti-blocking features
    
    Args:
        max_retries (int): Maximum number of retries
        timeout (int): Request timeout in seconds
        
    Returns:
        requests.Session: Session with configured retry logic
    """
    session = requests.Session()
    
    # Set a random user agent
    session.headers.update({
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "TE": "Trailers",
    })
    
    # Add a small delay to mimic human behavior
    time.sleep(random.uniform(1, 3))
    
    return session

def get_with_fallback(url, timeout=15, max_attempts=3):
    """
    Make a GET request with fallback options and retries
    
    Args:
        url (str): URL to fetch
        timeout (int): Request timeout in seconds
        max_attempts (int): Maximum number of attempts
        
    Returns:
        requests.Response or None: Response object or None if all attempts fail
    """
    attempts = 0
    last_exception = None
    
    while attempts < max_attempts:
        try:
            # Create a fresh session for each attempt
            session = create_robust_session()
            
            # Add random delay between attempts (longer for later attempts)
            if attempts > 0:
                delay = random.uniform(2 ** attempts, 2 ** (attempts + 1))
                time.sleep(delay)
            
            response = session.get(url, timeout=timeout)
            
            # Check if response is successful
            if response.status_code == 200:
                return response
                
            # If we got blocked or hit captcha, wait longer
            if response.status_code in [403, 429]:
                logger.warning(f"Received status code {response.status_code}, possibly rate limited or blocked")
                time.sleep(random.uniform(5, 10))
            
            attempts += 1
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempts+1} failed: {str(e)}")
            attempts += 1
    
    if last_exception:
        logger.error(f"All {max_attempts} attempts failed. Last error: {str(last_exception)}")
    
    return None

def extract_amazon_product_id(url):
    """Extract the Amazon product ID from a URL"""
    # Look for /dp/XXXXXXXXXX pattern
    dp_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if dp_match:
        return dp_match.group(1)
    
    # Look for /gp/product/XXXXXXXXXX pattern
    gp_match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    if gp_match:
        return gp_match.group(1)
        
    # Try to find any 10-character alphanumeric string that could be a product ID
    generic_match = re.search(r'([A-Z0-9]{10})', url)
    if generic_match:
        return generic_match.group(1)
    
    return None

def extract_flipkart_product_id(url):
    """Extract the Flipkart product ID from a URL"""
    # Look for /p/XXXXX pattern (Flipkart product IDs are usually after /p/)
    p_match = re.search(r'/p/([a-zA-Z0-9]+)', url)
    if p_match:
        return p_match.group(1)
    
    # Look for pid= in the query string
    pid_match = re.search(r'pid=([a-zA-Z0-9]+)', url)
    if pid_match:
        return pid_match.group(1)
    
    # Fallback to the last part of the URL path
    path = urlparse(url).path
    parts = path.split('/')
    if parts and parts[-1]:
        return parts[-1]
    
    return None

def scrape_amazon_india(query, limit=20, max_retries=3):
    """
    Scrape Amazon India for products matching the query
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        max_retries (int): Maximum number of retries
        
    Returns:
        list: List of product dictionaries
    """
    products = []
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    
    logger.info(f"Scraping Amazon India for: {query}")
    
    # Get the search results page
    response = get_with_fallback(url, max_attempts=max_retries)
    if not response:
        logger.error("Failed to get Amazon search results page")
        return products
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Find all product cards
    product_cards = soup.find_all('div', {'data-component-type': 's-search-result'})
    if not product_cards:
        # Try alternative selectors if the primary one fails
        product_cards = soup.find_all('div', {'class': 'sg-col-4-of-12 s-result-item'})
    if not product_cards:
        product_cards = soup.find_all('div', {'class': 's-result-item'})
    
    logger.info(f"Found {len(product_cards)} product cards on Amazon")
    
    # Extract information from each product card
    for card in product_cards[:limit]:
        try:
            # Get product URL and title
            title_element = card.find('h2')
            if not title_element:
                continue
                
            link_element = title_element.find('a')
            if not link_element:
                continue
                
            product_url = urljoin('https://www.amazon.in', link_element.get('href', ''))
            title = link_element.get_text().strip()
            
            # Get product ID
            product_id = extract_amazon_product_id(product_url)
            if not product_id:
                logger.warning(f"Could not extract product ID from URL: {product_url}")
                continue
            
            # Get price
            price_element = card.find('span', {'class': 'a-price-whole'})
            price_text = price_element.get_text().strip() if price_element else '0'
            price = extract_price(price_text)
            
            # Get original price (if available)
            original_price_element = card.find('span', {'class': 'a-text-price'})
            original_price_text = original_price_element.get_text().strip() if original_price_element else price_text
            original_price = extract_price(original_price_text)
            
            # Calculate discount
            discount = 0
            if original_price > 0 and price > 0 and original_price > price:
                discount = int(((original_price - price) / original_price) * 100)
            
            # Get rating
            rating_element = card.find('span', {'class': 'a-icon-alt'})
            rating_text = rating_element.get_text().strip() if rating_element else '0 out of 5 stars'
            try:
                rating = float(rating_text.split()[0])
            except (ValueError, IndexError):
                rating = 0
            
            # Get number of reviews
            reviews_element = card.find('span', {'class': 'a-size-base s-underline-text'})
            reviews_text = reviews_element.get_text().strip() if reviews_element else '0'
            reviews = 0
            try:
                reviews = int(''.join(filter(str.isdigit, reviews_text)))
            except ValueError:
                pass
            
            # Get image URL
            image_element = card.find('img', {'class': 's-image'})
            image_url = image_element.get('src') if image_element else ''
            
            # Create product dictionary
            product = {
                'id': product_id,
                'name': title,
                'price': price,
                'original_price': original_price,
                'discount': discount,
                'rating': rating,
                'reviews': reviews,
                'url': product_url,
                'image_url': image_url,
                'source': 'amazon'
            }
            
            products.append(product)
            
        except Exception as e:
            logger.warning(f"Error processing Amazon product card: {str(e)}")
    
    logger.info(f"Successfully scraped {len(products)} products from Amazon")
    return products

def scrape_flipkart(query, limit=20, max_retries=3):
    """
    Scrape Flipkart for products matching the query
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        max_retries (int): Maximum number of retries
        
    Returns:
        list: List of product dictionaries
    """
    products = []
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    
    logger.info(f"Scraping Flipkart for: {query}")
    
    # Get the search results page
    response = get_with_fallback(url, max_attempts=max_retries)
    if not response:
        logger.error("Failed to get Flipkart search results page")
        return products
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Find all product cards
    product_cards = soup.find_all('div', {'class': '_1AtVbE'})
    if not product_cards:
        # Try alternative selectors if the primary one fails
        product_cards = soup.find_all('div', {'class': '_4ddWXP'})
    if not product_cards:
        product_cards = soup.find_all('div', {'class': '_2kHMtA'})
    
    logger.info(f"Found {len(product_cards)} product cards on Flipkart")
    
    # Extract information from each product card
    processed_count = 0
    for card in product_cards:
        if processed_count >= limit:
            break
            
        try:
            # Get product URL and title
            title_element = card.find('div', {'class': '_4rR01T'}) or card.find('a', {'class': 's1Q9rs'})
            if not title_element:
                continue
                
            link_element = card.find('a', {'class': '_1fQZEK'}) or card.find('a', {'class': '_2rpwqI'}) or card.find('a', {'class': 's1Q9rs'})
            if not link_element:
                continue
                
            product_url = urljoin('https://www.flipkart.com', link_element.get('href', ''))
            title = title_element.get_text().strip()
            
            # Get product ID
            product_id = extract_flipkart_product_id(product_url)
            if not product_id:
                logger.warning(f"Could not extract product ID from URL: {product_url}")
                continue
            
            # Get price
            price_element = card.find('div', {'class': '_30jeq3'})
            price_text = price_element.get_text().strip() if price_element else '0'
            price = extract_price(price_text)
            
            # Get original price (if available)
            original_price_element = card.find('div', {'class': '_3I9_wc'})
            original_price_text = original_price_element.get_text().strip() if original_price_element else price_text
            original_price = extract_price(original_price_text)
            
            # Calculate discount
            discount = 0
            discount_element = card.find('div', {'class': '_3Ay6Sb'})
            if discount_element:
                discount_text = discount_element.get_text().strip()
                discount_match = re.search(r'(\d+)%', discount_text)
                if discount_match:
                    discount = int(discount_match.group(1))
            elif original_price > 0 and price > 0 and original_price > price:
                discount = int(((original_price - price) / original_price) * 100)
            
            # Get rating
            rating_element = card.find('div', {'class': '_3LWZlK'})
            rating_text = rating_element.get_text().strip() if rating_element else '0'
            try:
                rating = float(rating_text)
            except ValueError:
                rating = 0
            
            # Get number of reviews
            reviews_element = card.find('span', {'class': '_2_R_DZ'})
            reviews_text = reviews_element.get_text().strip() if reviews_element else '0'
            reviews = 0
            reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
            if reviews_match:
                reviews = int(reviews_match.group(1).replace(',', ''))
            
            # Get image URL
            image_element = card.find('img', {'class': '_396cs4'})
            if not image_element:
                image_element = card.find('img', {'class': '_2r_T1I'})
            image_url = image_element.get('src') if image_element else ''
            
            # Create product dictionary
            product = {
                'id': product_id,
                'name': title,
                'price': price,
                'original_price': original_price,
                'discount': discount,
                'rating': rating,
                'reviews': reviews,
                'url': product_url,
                'image_url': image_url,
                'source': 'flipkart'
            }
            
            products.append(product)
            processed_count += 1
            
        except Exception as e:
            logger.warning(f"Error processing Flipkart product card: {str(e)}")
    
    logger.info(f"Successfully scraped {len(products)} products from Flipkart")
    return products

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
        # Create a session with a random user agent
        session = create_robust_session()
        
        # Make a HEAD request first to check if the URL is valid
        response = session.head(url, timeout=10, allow_redirects=True)
        
        # Check if the response is OK
        if response.status_code == 200:
            return True
            
        # If HEAD fails, try GET as some websites block HEAD requests
        if response.status_code in [403, 405]:
            response = session.get(url, timeout=10)
            return response.status_code == 200
            
        return False
        
    except Exception as e:
        logger.warning(f"Error verifying URL {url}: {str(e)}")
        return False

def get_product_details(url, source):
    """
    Get detailed information about a product
    
    Args:
        url (str): Product URL
        source (str): Source website (amazon or flipkart)
        
    Returns:
        dict: Product details
    """
    try:
        # Get the product page
        response = get_with_fallback(url)
        if not response:
            logger.error(f"Failed to get product page: {url}")
            return {}
        
        # Extract text content using trafilatura
        text_content = trafilatura.extract(response.text)
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract product details based on source
        if source == 'amazon':
            return parse_amazon_product_details(soup, text_content, url)
        elif source == 'flipkart':
            return parse_flipkart_product_details(soup, text_content, url)
        
        return {}
        
    except Exception as e:
        logger.error(f"Error getting product details for {url}: {str(e)}")
        return {}

def parse_amazon_product_details(soup, text_content, url):
    """
    Parse product details from Amazon product page
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object of the product page
        text_content (str): Extracted text content from trafilatura
        url (str): Product URL
        
    Returns:
        dict: Product details
    """
    details = {}
    
    try:
        # Extract product ID
        product_id = extract_amazon_product_id(url)
        details['id'] = product_id
        
        # Extract product name
        title_element = soup.find('span', {'id': 'productTitle'})
        details['name'] = title_element.get_text().strip() if title_element else ''
        
        # Extract price
        price_element = soup.find('span', {'class': 'a-price-whole'})
        price_text = price_element.get_text().strip() if price_element else '0'
        details['price'] = extract_price(price_text)
        
        # Extract original price
        original_price_element = soup.find('span', {'class': 'a-text-price'})
        original_price_text = original_price_element.get_text().strip() if original_price_element else price_text
        details['original_price'] = extract_price(original_price_text)
        
        # Calculate discount
        if details['original_price'] > 0 and details['price'] > 0 and details['original_price'] > details['price']:
            details['discount'] = int(((details['original_price'] - details['price']) / details['original_price']) * 100)
        else:
            details['discount'] = 0
        
        # Extract rating
        rating_element = soup.find('span', {'id': 'acrPopover'})
        rating_text = rating_element.get('title') if rating_element else '0 out of 5 stars'
        try:
            details['rating'] = float(rating_text.split()[0])
        except (ValueError, IndexError):
            details['rating'] = 0
        
        # Extract number of reviews
        reviews_element = soup.find('span', {'id': 'acrCustomerReviewText'})
        reviews_text = reviews_element.get_text().strip() if reviews_element else '0'
        try:
            details['reviews'] = int(''.join(filter(str.isdigit, reviews_text)))
        except ValueError:
            details['reviews'] = 0
        
        # Extract image URL
        image_element = soup.find('img', {'id': 'landingImage'})
        if not image_element:
            image_element = soup.find('img', {'class': 'a-dynamic-image'})
        details['image_url'] = image_element.get('src') if image_element else ''
        
        # Extract product description
        description = ''
        description_element = soup.find('div', {'id': 'productDescription'})
        if description_element:
            description = description_element.get_text().strip()
        else:
            # If no specific description element is found, use trafilatura's extracted content
            description = text_content
        
        details['description'] = description
        details['url'] = url
        details['source'] = 'amazon'
        
        return details
        
    except Exception as e:
        logger.error(f"Error parsing Amazon product details: {str(e)}")
        
        # Return basic details even if parsing fails
        if not details.get('id'):
            details['id'] = extract_amazon_product_id(url) or 'unknown'
        if not details.get('url'):
            details['url'] = url
        if not details.get('source'):
            details['source'] = 'amazon'
            
        return details

def parse_flipkart_product_details(soup, text_content, url):
    """
    Parse product details from Flipkart product page
    
    Args:
        soup (BeautifulSoup): BeautifulSoup object of the product page
        text_content (str): Extracted text content from trafilatura
        url (str): Product URL
        
    Returns:
        dict: Product details
    """
    details = {}
    
    try:
        # Extract product ID
        product_id = extract_flipkart_product_id(url)
        details['id'] = product_id
        
        # Extract product name
        title_element = soup.find('span', {'class': 'B_NuCI'})
        details['name'] = title_element.get_text().strip() if title_element else ''
        
        # Extract price
        price_element = soup.find('div', {'class': '_30jeq3 _16Jk6d'})
        price_text = price_element.get_text().strip() if price_element else '0'
        details['price'] = extract_price(price_text)
        
        # Extract original price
        original_price_element = soup.find('div', {'class': '_3I9_wc _2p6lqe'})
        original_price_text = original_price_element.get_text().strip() if original_price_element else price_text
        details['original_price'] = extract_price(original_price_text)
        
        # Calculate discount
        discount_element = soup.find('div', {'class': '_3Ay6Sb _31Dcoz'})
        if discount_element:
            discount_text = discount_element.get_text().strip()
            discount_match = re.search(r'(\d+)%', discount_text)
            if discount_match:
                details['discount'] = int(discount_match.group(1))
            else:
                details['discount'] = 0
        elif details.get('original_price', 0) > 0 and details.get('price', 0) > 0 and details['original_price'] > details['price']:
            details['discount'] = int(((details['original_price'] - details['price']) / details['original_price']) * 100)
        else:
            details['discount'] = 0
        
        # Extract rating
        rating_element = soup.find('div', {'class': '_3LWZlK'})
        rating_text = rating_element.get_text().strip() if rating_element else '0'
        try:
            details['rating'] = float(rating_text)
        except ValueError:
            details['rating'] = 0
        
        # Extract number of reviews
        reviews_element = soup.find('span', {'class': '_2_R_DZ'})
        reviews_text = reviews_element.get_text().strip() if reviews_element else '0'
        reviews = 0
        reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
        if reviews_match:
            reviews = int(reviews_match.group(1).replace(',', ''))
        details['reviews'] = reviews
        
        # Extract image URL
        image_element = soup.find('img', {'class': '_396cs4 _2amPTt _3qGmMb'})
        if not image_element:
            image_element = soup.find('img', {'class': '_396cs4'})
        details['image_url'] = image_element.get('src') if image_element else ''
        
        # Extract product description
        description = ''
        description_element = soup.find('div', {'class': '_1mXcCf RmoJUa'})
        if description_element:
            description = description_element.get_text().strip()
        else:
            # If no specific description element is found, use trafilatura's extracted content
            description = text_content
        
        details['description'] = description
        details['url'] = url
        details['source'] = 'flipkart'
        
        return details
        
    except Exception as e:
        logger.error(f"Error parsing Flipkart product details: {str(e)}")
        
        # Return basic details even if parsing fails
        if not details.get('id'):
            details['id'] = extract_flipkart_product_id(url) or 'unknown'
        if not details.get('url'):
            details['url'] = url
        if not details.get('source'):
            details['source'] = 'flipkart'
            
        return details

def search_products(query, limit=20):
    """
    Search for products across multiple platforms
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return per platform
        
    Returns:
        dict: Dictionary with platform names as keys and lists of products as values
    """
    results = {
        "amazon": [],
        "flipkart": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Scrape products from Amazon India
    try:
        amazon_products = scrape_amazon_india(query, limit)
        results["amazon"] = amazon_products
    except Exception as e:
        logger.error(f"Error scraping Amazon: {str(e)}")
    
    # Scrape products from Flipkart
    try:
        flipkart_products = scrape_flipkart(query, limit)
        results["flipkart"] = flipkart_products
    except Exception as e:
        logger.error(f"Error scraping Flipkart: {str(e)}")
    
    return results

# For testing
if __name__ == "__main__":
    results = search_products("laptop", limit=5)
    print(json.dumps(results, indent=2))