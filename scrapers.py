import requests
from bs4 import BeautifulSoup
import re
import json
import random
import time
import uuid
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# User agent rotation to avoid blocking
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41'
]

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)

def scrape_amazon(query):
    """
    Scrape Amazon for product information
    
    Args:
        query (str): Search query
        
    Returns:
        list: List of product dictionaries
    """
    try:
        # Encode the search query
        encoded_query = quote_plus(query)
        url = f"https://www.amazon.com/s?k={encoded_query}"
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Send request with a timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Amazon results: {response.status_code}")
            return []
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product containers
        products = []
        product_cards = soup.select('div[data-component-type="s-search-result"]')
        
        for card in product_cards[:20]:  # Limit to first 20 products
            try:
                # Extract product details
                product_id = card.get('data-asin', str(uuid.uuid4()))
                
                # Name
                name_element = card.select_one('h2 a span')
                name = name_element.text.strip() if name_element else 'Unknown Product'
                
                # URL
                url_element = card.select_one('h2 a')
                product_url = 'https://www.amazon.com' + url_element['href'] if url_element else ''
                
                # Price
                price_element = card.select_one('span.a-price > span.a-offscreen')
                price_text = price_element.text.strip() if price_element else '$0.00'
                price = float(re.sub(r'[^\d.]', '', price_text) or 0)
                
                # Original price (if discounted)
                original_price_element = card.select_one('span.a-price.a-text-price > span.a-offscreen')
                original_price_text = original_price_element.text.strip() if original_price_element else price_text
                original_price = float(re.sub(r'[^\d.]', '', original_price_text) or price)
                
                # Calculate discount
                discount = round(((original_price - price) / original_price) * 100) if original_price > price else 0
                
                # Ratings and reviews
                rating_element = card.select_one('span[aria-label*="stars"]')
                rating_text = rating_element['aria-label'] if rating_element else '0 stars'
                rating = float(re.search(r'([\d.]+)', rating_text).group(1)) if re.search(r'([\d.]+)', rating_text) else 0
                
                reviews_element = card.select_one('span[aria-label*="stars"] + span')
                reviews_text = reviews_element.text.strip() if reviews_element else '0'
                reviews = int(re.sub(r'[^\d]', '', reviews_text) or 0)
                
                # Image URL
                image_element = card.select_one('img.s-image')
                image_url = image_element['src'] if image_element else ''
                
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
                    'source': 'amazon'
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Amazon product: {str(e)}")
                continue
        
        return products
    
    except Exception as e:
        logger.error(f"Error scraping Amazon: {str(e)}")
        return []

def scrape_flipkart(query):
    """
    Scrape Flipkart for product information
    
    Args:
        query (str): Search query
        
    Returns:
        list: List of product dictionaries
    """
    try:
        # Encode the search query
        encoded_query = quote_plus(query)
        url = f"https://www.flipkart.com/search?q={encoded_query}"
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # Send request with a timeout
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Flipkart results: {response.status_code}")
            return []
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all product containers
        products = []
        product_cards = soup.select('div._1AtVbE')
        
        for card in product_cards[:20]:  # Limit to first 20 products
            try:
                # Extract product details
                product_id = str(uuid.uuid4())  # Generate a unique ID for each product
                
                # Name
                name_element = card.select_one('div._4rR01T') or card.select_one('a.s1Q9rs') or card.select_one('a.IRpwTa')
                if not name_element:
                    continue  # Skip if no name found
                
                name = name_element.text.strip()
                
                # URL
                url_element = card.select_one('a._1fQZEK') or card.select_one('a.s1Q9rs') or card.select_one('a._2rpwqI')
                product_url = 'https://www.flipkart.com' + url_element['href'] if url_element and 'href' in url_element.attrs else ''
                
                # Price
                price_element = card.select_one('div._30jeq3')
                price_text = price_element.text.strip() if price_element else '₹0'
                price = float(re.sub(r'[^\d.]', '', price_text) or 0)
                
                # Original price (if discounted)
                original_price_element = card.select_one('div._3I9_wc')
                original_price_text = original_price_element.text.strip() if original_price_element else price_text
                original_price = float(re.sub(r'[^\d.]', '', original_price_text) or price)
                
                # Calculate discount
                discount_element = card.select_one('div._3Ay6Sb')
                if discount_element:
                    discount_text = discount_element.text.strip()
                    discount = int(re.sub(r'[^\d]', '', discount_text) or 0)
                else:
                    discount = round(((original_price - price) / original_price) * 100) if original_price > price else 0
                
                # Ratings and reviews
                rating_element = card.select_one('div._3LWZlK')
                rating = float(rating_element.text.strip()) if rating_element else 0
                
                reviews_element = card.select_one('span._2_R_DZ')
                reviews_text = reviews_element.text.strip() if reviews_element else '0'
                reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                reviews = int(re.sub(r'[^\d]', '', reviews_match.group(1)) if reviews_match else 0)
                
                # Image URL
                image_element = card.select_one('img._396cs4') or card.select_one('img._2r_T1I')
                image_url = image_element['src'] if image_element and 'src' in image_element.attrs else ''
                
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
                    'source': 'flipkart'
                }
                
                products.append(product)
                
            except Exception as e:
                logger.error(f"Error parsing Flipkart product: {str(e)}")
                continue
        
        return products
    
    except Exception as e:
        logger.error(f"Error scraping Flipkart: {str(e)}")
        return []
