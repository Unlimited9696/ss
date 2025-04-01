"""
Simple and direct web scraper for price tracking applications.
Uses BeautifulSoup for reliable content extraction and has basic error handling.
"""
import json
import random
import re
import time
import logging
from urllib.parse import urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of user agents to rotate through
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-S906N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/80.0.3987.119 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G996U Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
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

def scrape_amazon_india(query, limit=20, max_retries=3):
    """Scrape Amazon India for products using BeautifulSoup"""
    products = []
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    response = None
    
    logger.info(f"Scraping Amazon India for: {query}")
    
    # Multiple retries with backoff
    for attempt in range(max_retries):
        try:
            headers = {
                "User-Agent": get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                # Add referrer to appear more legitimate
                "Referer": "https://www.amazon.in/",
            }
            
            # Use a shorter timeout to avoid hanging
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                break
                
            # If we got a 503 (Service Unavailable) or other error, try again with a different approach
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed with status code: {response.status_code}")
            
            # Try with a mobile user agent if we're on the last attempt
            if attempt == max_retries - 1:
                try:
                    mobile_headers = {
                        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    }
                    
                    # Try the mobile URL
                    mobile_url = f"https://www.amazon.in/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords={query.replace(' ', '+')}"
                    response = requests.get(mobile_url, headers=mobile_headers, timeout=8)
                    
                    if response.status_code == 200:
                        logger.info("Successfully fetched Amazon page using mobile user agent")
                        break
                except Exception as e:
                    logger.error(f"Mobile fallback attempt failed: {str(e)}")
            
            # If we haven't broken out of the loop yet, use exponential backoff
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
                
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt+1}/{max_retries} timed out")
            
            # If this is the last attempt, try one more time with a modified approach
            if attempt == max_retries - 1:
                try:
                    # Try with very basic headers and a shorter timeout
                    simple_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    }
                    response = requests.get(url, headers=simple_headers, timeout=5)
                    if response.status_code == 200:
                        break
                except Exception as e:
                    logger.error(f"Simple headers fallback attempt failed: {str(e)}")
            
            # Use exponential backoff
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"Attempt {attempt+1}/{max_retries} failed with error: {str(e)}")
            
            # Use exponential backoff
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
    
    try:
        # If we still don't have a successful response, return empty products list
        if response is None or response.status_code != 200:
            logger.error(f"Failed to get valid response from Amazon after {max_retries} attempts")
            return products
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors for Amazon product cards
        all_product_cards = []
        
        # First try the standard selector for desktop layout
        product_cards = soup.select('div[data-component-type="s-search-result"]')
        if product_cards:
            all_product_cards.extend(product_cards)
        
        # Try fallback for desktop layout
        product_cards = soup.select('div.s-result-item')
        if product_cards:
            for card in product_cards:
                # Only add if not already in the list and it looks like a product card
                if card not in all_product_cards and card.select_one('h2, .a-text-normal'):
                    all_product_cards.append(card)
        
        # Try mobile layout
        product_cards = soup.select('div.s-item-container')
        if product_cards:
            all_product_cards.extend(product_cards)
        
        # Try another mobile layout
        product_cards = soup.select('.a-section.a-spacing-none')
        if product_cards:
            # Filter to only include cards that have a title
            for card in product_cards:
                if card.select_one('h2, .a-text-normal') and card not in all_product_cards:
                    all_product_cards.append(card)
                    
        # Remove duplicates while preserving order
        seen = set()
        product_cards = [card for card in all_product_cards if not (card in seen or seen.add(card))]
            
        logger.info(f"Found {len(product_cards)} product cards on Amazon")
        
        # Process each product card
        processed_count = 0
        for card in product_cards:
            if processed_count >= limit:
                break
                
            try:
                # Get product name - try multiple selectors
                title_elem = (card.select_one('h2 a span') or 
                             card.select_one('h2') or 
                             card.select_one('.a-text-normal') or
                             card.select_one('a.a-link-normal span') or
                             card.select_one('.a-size-base-plus'))
                             
                if not title_elem:
                    continue
                    
                name = title_elem.get_text().strip()
                if not name:
                    continue
                
                # Get product URL
                link_elem = (card.select_one('h2 a') or 
                            card.select_one('a.a-link-normal[href*="/dp/"]') or
                            card.select_one('a[href*="/dp/"]'))
                            
                if not link_elem:
                    continue
                    
                product_url = link_elem.get('href', '')
                if not product_url:
                    continue
                    
                url = urljoin('https://www.amazon.in', product_url)
                
                # Extract product ID from URL
                product_id = "AZ" + str(random.randint(10000, 99999))  # Fallback ID
                id_match = re.search(r'/dp/([A-Z0-9]{10})', url)
                if id_match:
                    product_id = id_match.group(1)
                
                # Get price - try multiple selectors
                price_elem = (card.select_one('.a-price .a-offscreen') or 
                             card.select_one('.a-price-whole') or
                             card.select_one('.a-color-price') or
                             card.select_one('.a-price') or
                             card.select_one('span[data-a-color="price"]'))
                             
                price_text = price_elem.get_text().strip() if price_elem else '0'
                price = extract_price(price_text)
                
                # Get original price - try multiple selectors
                original_price_elem = (card.select_one('.a-text-price') or 
                                     card.select_one('span.a-text-price span.a-offscreen') or
                                     card.select_one('.a-text-strike'))
                                     
                original_price_text = original_price_elem.get_text().strip() if original_price_elem else price_text
                original_price = extract_price(original_price_text)
                
                # Calculate discount
                discount = 0
                if original_price > price and price > 0:
                    discount = int(((original_price - price) / original_price) * 100)
                
                # Try to get discount directly if available
                discount_elem = card.select_one('span.a-color-price') or card.select_one('span.a-letter-space')
                if discount_elem and "%" in discount_elem.get_text():
                    discount_match = re.search(r'(\d+)%', discount_elem.get_text())
                    if discount_match:
                        discount = int(discount_match.group(1))
                
                # Get rating
                rating_elem = (card.select_one('i.a-icon-star-small, i.a-icon-star') or 
                              card.select_one('span[aria-label*="stars"]') or
                              card.select_one('.a-icon-alt'))
                              
                rating = 0
                if rating_elem:
                    rating_text = rating_elem.get_text().strip() or rating_elem.get('aria-label', '0')
                    rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                
                # Get number of reviews
                reviews_elem = (card.select_one('span.a-size-base.s-underline-text') or 
                               card.select_one('a[href*="customerReviews"]') or
                               card.select_one('a[href*="reviews"]'))
                               
                reviews = 0
                if reviews_elem:
                    reviews_text = reviews_elem.get_text().strip()
                    reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                    if reviews_match:
                        reviews = int(reviews_match.group(1).replace(',', ''))
                
                # Get image URL
                image_elem = card.select_one('img.s-image') or card.select_one('img[src*="images"]')
                image_url = image_elem.get('src') if image_elem else ''
                
                # Make sure we have essential data
                if not name or price <= 0:
                    continue
                    
                # Make sure original price is not less than price
                if original_price < price:
                    original_price = price
                
                product = {
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': url,
                    'image_url': image_url,
                    'source': 'amazon'
                }
                
                products.append(product)
                processed_count += 1
            
            except Exception as e:
                logger.error(f"Error processing Amazon product card: {str(e)}")
        
        logger.info(f"Successfully scraped {len(products)} products from Amazon")
        
    except Exception as e:
        logger.error(f"Error scraping Amazon: {str(e)}")
    
    return products

def scrape_meesho(query, limit=20, max_retries=3):
    """Scrape Meesho for products using BeautifulSoup"""
    products = []
    url = f"https://www.meesho.com/search?q={query.replace(' ', '%20')}"
    response = None
    
    logger.info(f"Scraping Meesho for: {query}")
    
    # Use a shorter timeout and reduced retry count to prevent hanging
    for attempt in range(max_retries):
        try:
            # Rotate user agents to avoid blocking
            user_agent = get_random_user_agent()
                
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
            
            # Use a shorter timeout to avoid server hanging
            timeout = 5 if attempt == 0 else 3
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            
            # Check immediately if the status code is valid
            if response.status_code == 200:
                # Only read a small part of the response to verify it's valid
                content_sample = next(response.iter_content(1024), None)
                if content_sample:
                    # Read the rest of the content
                    full_content = content_sample + response.content
                    response._content = full_content
                    break
                
            logger.warning(f"Attempt {attempt+1}/{max_retries} failed with status code: {response.status_code}")
            
            # Use a shorter backoff time for Meesho
            if attempt < max_retries - 1:
                sleep_time = 1 + random.uniform(0, 0.5)
                time.sleep(sleep_time)
        
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt+1}/{max_retries} timed out")
            # Skip backoff on timeout - just try with different params immediately
            continue
        
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error on attempt {attempt+1}/{max_retries}")
            # Skip backoff on connection errors
            continue
        
        except Exception as e:
            logger.error(f"Attempt {attempt+1}/{max_retries} failed with error: {str(e)}")
            # Skip retries if we get a serious error
            break
    
    try:
        # If we still don't have a valid response, return empty products list
        if response is None or response.status_code != 200:
            logger.error(f"Failed to get valid response from Meesho after {max_retries} attempts")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors to find product cards
        all_product_cards = []
        
        # First try the standard selectors for Meesho product cards
        product_cards = soup.select('div[data-testid="product-card"]')
        if product_cards:
            all_product_cards.extend(product_cards)
            
        # Try alternative selectors if needed
        product_cards = soup.select('div.ProductList__GridCol-sc-8lnc8o-0')
        if product_cards:
            all_product_cards.extend(product_cards)
            
        # Try another alternative layout
        product_cards = soup.select('a[href*="/product/"]')
        if product_cards:
            all_product_cards.extend(product_cards)
            
        # More generic approach - look for divs containing product info
        price_elements = soup.select('h5[data-testid="product-price"], span.actual-price')
        for price_elem in price_elements:
            parent = price_elem.find_parent('div')
            if parent and parent not in all_product_cards:
                all_product_cards.append(parent)
                
        # Remove duplicates while preserving order
        seen = set()
        product_cards = [card for card in all_product_cards if not (card in seen or seen.add(card))]
            
        logger.info(f"Found {len(product_cards)} product cards on Meesho")
        
        processed_count = 0
        
        # Process each product card
        for card in product_cards:
            if processed_count >= limit:
                break
                
            try:
                # Look for product name in multiple possible locations
                title_elem = (card.select_one('p[data-testid="product-name"]') or 
                             card.select_one('div.product-name') or 
                             card.select_one('h4.NewProductCard__ProductTitle-sc-j0e7tu-4') or
                             card.select_one('p.NewProductCard__ProductTitle-sc-j0e7tu-4'))
                             
                if not title_elem:
                    # Try to find any element that might contain the product name
                    for elem in card.select('p, h4, h5'):
                        text = elem.get_text().strip()
                        if len(text) > 10 and len(text) < 200:
                            title_elem = elem
                            break
                
                if not title_elem:
                    continue
                    
                name = title_elem.get_text().strip()
                if not name:
                    continue
                
                # Get product URL - for Meesho, the entire card is often clickable
                link_elem = card if card.name == 'a' else card.find_parent('a')
                
                if not link_elem:
                    # Try to find links inside the card
                    link_elem = card.select_one('a[href*="/product/"]')
                
                if not link_elem:
                    continue
                    
                url = urljoin('https://www.meesho.com', link_elem.get('href', ''))
                
                # Extract product ID from URL
                product_id = "ME" + str(random.randint(10000, 99999))  # Fallback ID
                id_match = re.search(r'/product/([a-zA-Z0-9-]+)', url)
                if id_match:
                    product_id = id_match.group(1)
                
                # Get price - try different selectors for Meesho pricing
                price_elem = (
                    card.select_one('h5[data-testid="product-price"]') or 
                    card.select_one('span.actual-price') or
                    card.select_one('h5.NewProductCard__StyledDesktopMRP-sc-j0e7tu-6') or
                    card.select_one('div.product-price')
                )
                
                price_text = price_elem.get_text().strip() if price_elem else '0'
                price = extract_price(price_text)
                
                # Get original price
                original_price_elem = (
                    card.select_one('span[data-testid="product-strike-price"]') or 
                    card.select_one('span.strike-price') or
                    card.select_one('span.NewProductCard__StyledDesktopStrikedPrice-sc-j0e7tu-7')
                )
                
                original_price_text = original_price_elem.get_text().strip() if original_price_elem else price_text
                original_price = extract_price(original_price_text)
                
                # Ensure original price is not less than current price
                if original_price < price:
                    original_price = price
                
                # Get discount
                discount = 0
                discount_elem = (
                    card.select_one('span[data-testid="product-discount"]') or 
                    card.select_one('span.discount') or
                    card.select_one('span.NewProductCard__StyledDesktopDiscountPercentage-sc-j0e7tu-8')
                )
                
                if discount_elem:
                    discount_text = discount_elem.get_text().strip()
                    discount_match = re.search(r'(\d+)%', discount_text)
                    if discount_match:
                        discount = int(discount_match.group(1))
                elif original_price > price and price > 0:
                    discount = int(((original_price - price) / original_price) * 100)
                
                # Get rating
                rating_elem = (
                    card.select_one('span[data-testid="product-rating"]') or 
                    card.select_one('div.product-rating') or
                    card.select_one('span.NewProductCard__StyledRatingValue-sc-j0e7tu-13')
                )
                
                rating = 0
                if rating_elem:
                    try:
                        rating_text = rating_elem.get_text().strip()
                        rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                    except ValueError:
                        pass
                
                # Get number of reviews
                reviews_elem = (
                    card.select_one('span[data-testid="product-rating-count"]') or 
                    card.select_one('div.rating-count') or
                    card.select_one('span.NewProductCard__StyledRatingCount-sc-j0e7tu-14')
                )
                
                reviews = 0
                if reviews_elem:
                    reviews_text = reviews_elem.get_text().strip()
                    reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                    if reviews_match:
                        reviews = int(reviews_match.group(1).replace(',', ''))
                
                # Get image URL
                image_elem = (
                    card.select_one('img[data-testid="product-image"]') or 
                    card.select_one('img.product-image') or
                    card.select_one('img.NewProductCard__ProductImage-sc-j0e7tu-3') or
                    card.select_one('img')
                )
                
                image_url = ""
                if image_elem:
                    if image_elem.has_attr('src'):
                        image_url = image_elem['src']
                    elif image_elem.has_attr('data-src'):
                        image_url = image_elem['data-src']
                
                # Make sure we have valid data
                if not name or price <= 0:
                    continue
                
                product = {
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': url,
                    'image_url': image_url,
                    'source': 'meesho'
                }
                
                products.append(product)
                processed_count += 1
            
            except Exception as e:
                logger.error(f"Error processing Meesho product card: {str(e)}")
        
        logger.info(f"Successfully scraped {len(products)} products from Meesho")
        
    except Exception as e:
        logger.error(f"Error scraping Meesho: {str(e)}")
    
    return products

def search_products(query, limit=20, max_retries=3):
    """
    Search for products across multiple e-commerce sites
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return per site
        max_retries (int): Maximum number of retries for each scraper
        
    Returns:
        dict: Dictionary with site names as keys and lists of products as values
    """
    results = {
        "amazon": [],
        "meesho": [],
        "timestamp": datetime.now().isoformat()
    }
    
    # Safety mechanism: if query is too short or contains invalid characters, return empty results
    if not query or len(query.strip()) < 2:
        logger.warning("Query is too short or empty")
        return results
    
    try:
        # Try to get products from Amazon with retries
        amazon_products = scrape_amazon_india(query, limit, max_retries)
        results["amazon"] = amazon_products
    except Exception as e:
        logger.error(f"Error scraping Amazon: {str(e)}")
        results["amazon"] = []
    
    try:
        # Try to get products from Meesho with retries
        meesho_products = []
        # Only attempt Meesho if Amazon worked (to avoid server overload)
        if len(results["amazon"]) > 0:
            meesho_products = scrape_meesho(query, limit, max_retries)
        results["meesho"] = meesho_products
    except Exception as e:
        logger.error(f"Error scraping Meesho: {str(e)}")
        results["meesho"] = []
    
    return results

def verify_product_url(url, source):
    """Verify if a product URL is valid by sending a HEAD request"""
    try:
        headers = {
            "User-Agent": get_random_user_agent(),
        }
        
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        return response.status_code == 200
    
    except Exception as e:
        logger.error(f"Error verifying URL {url}: {str(e)}")
        return False

def generate_dummy_data(query, limit=10):
    """
    Generate dummy product data for testing UI when scraping fails
    Note: This should only be used for development/testing, not in production
    """
    amazon_products = []
    meesho_products = []
    
    for i in range(limit):
        # Amazon dummy product
        amazon_products.append({
            'id': f"A{i}",
            'name': f"Amazon {query.title()} Model {i+1}",
            'price': random.randint(1000, 50000),
            'original_price': random.randint(1000, 60000),
            'discount': random.randint(0, 30),
            'rating': round(random.uniform(3.0, 5.0), 1),
            'reviews': random.randint(10, 5000),
            'url': f"https://www.amazon.in/dp/DUMMY{i}",
            'image_url': f"https://via.placeholder.com/300x300.png?text=Amazon+{query.replace(' ', '+')}+{i+1}",
            'source': 'amazon'
        })
        
        # Meesho dummy product
        meesho_products.append({
            'id': f"M{i}",
            'name': f"Meesho {query.title()} Model {i+1}",
            'price': random.randint(1000, 50000),
            'original_price': random.randint(1000, 60000),
            'discount': random.randint(0, 30),
            'rating': round(random.uniform(3.0, 5.0), 1),
            'reviews': random.randint(10, 5000),
            'url': f"https://www.meesho.com/product/DUMMY{i}",
            'image_url': f"https://via.placeholder.com/300x300.png?text=Meesho+{query.replace(' ', '+')}+{i+1}",
            'source': 'meesho'
        })
    
    return {
        "amazon": amazon_products,
        "meesho": meesho_products,
        "timestamp": datetime.now().isoformat(),
        "is_dummy_data": True
    }

if __name__ == "__main__":
    # Test the scraper
    results = search_products("smartphone", 5)
    print(json.dumps(results, indent=2))