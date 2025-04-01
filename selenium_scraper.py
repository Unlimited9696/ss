import os
import re
import json
import time
import random
import logging
import traceback
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User agents collection for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
]

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)

def create_webdriver(headless=True):
    """Create and configure a Chrome WebDriver with proper settings to avoid detection"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Add required arguments for running in Replit
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # Set random user agent
    chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
    
    # Disable automation flags
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Create and return the WebDriver
    try:
        # Use webdriver-manager to handle driver installation automatically
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Successfully created Chrome WebDriver using webdriver-manager")
    except Exception as first_error:
        logger.warning(f"Failed to create Chrome WebDriver with webdriver-manager: {str(first_error)}")
        try:
            # Try to use Chromium directly
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Successfully created Chrome WebDriver using system Chromium")
        except Exception as second_error:
            logger.error(f"Failed to create WebDriver with system Chromium: {str(second_error)}")
            # As a last resort, fall back to request-based scraping
            from bs4 import BeautifulSoup
            import requests
            logger.warning("Falling back to traditional request-based scraping")
            return None
    
    # Execute CDP commands to avoid detection
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        })
    except Exception as e:
        logger.warning(f"Couldn't set CDP commands: {str(e)}")
    
    return driver

def safe_get_element_text(driver, by, selector, wait_time=5, default=""):
    """Safely get text from an element with a timeout"""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((by, selector))
        )
        return element.text.strip()
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        return default

def safe_get_element_attribute(driver, by, selector, attribute, wait_time=5, default=""):
    """Safely get an attribute from an element with a timeout"""
    try:
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((by, selector))
        )
        return element.get_attribute(attribute) or default
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        return default

def extract_price(price_text):
    """Extract numeric price value from text containing ₹ symbol and commas"""
    if not price_text:
        return 0
    
    # Remove ₹ symbol, commas, spaces and other non-digit characters except decimal point
    digits_only = re.sub(r'[^\d.]', '', price_text)
    
    try:
        return float(digits_only)
    except ValueError:
        return 0

def random_sleep(min_seconds=1, max_seconds=3):
    """Sleep for a random amount of time to mimic human behavior"""
    time.sleep(random.uniform(min_seconds, max_seconds))

def scrape_amazon_with_bs4(query, limit=20):
    """
    Fallback method that uses BeautifulSoup to scrape Amazon when Selenium fails
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        
    Returns:
        list: List of product dictionaries
    """
    import requests
    from bs4 import BeautifulSoup
    
    products = []
    
    try:
        # Encode search query for URL
        search_query = query.replace(' ', '+')
        url = f"https://www.amazon.in/s?k={search_query}"
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        logger.info(f"Making BS4 request to Amazon URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Amazon search results: HTTP {response.status_code}")
            return products
            
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find all product cards
        product_cards = soup.select('div[data-component-type="s-search-result"]')
        logger.info(f"Found {len(product_cards)} product cards on Amazon with BS4")
        
        count = 0
        for card in product_cards:
            if count >= limit:
                break
                
            try:
                # Skip sponsored products
                if card.select_one('.s-sponsored-label-info-icon'):
                    continue
                
                # Extract title
                title_element = card.select_one('h2 a span')
                if not title_element:
                    continue
                title = title_element.text.strip()
                
                # Get link
                link_element = card.select_one('h2 a')
                if not link_element:
                    continue
                link = link_element.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.amazon.in{link}"
                
                # Extract product ID from URL
                product_id = None
                if '/dp/' in link:
                    product_id = link.split('/dp/')[1].split('/')[0].split('?')[0]
                
                # Get image
                img_element = card.select_one('img')
                img_url = img_element.get('src', '') if img_element else ''
                
                # Get price
                price = 0
                price_element = card.select_one('.a-price .a-offscreen')
                if price_element:
                    price = extract_price(price_element.text)
                else:
                    # Try alternative price selector
                    price_element = card.select_one('.a-price-whole')
                    if price_element:
                        price = extract_price("₹" + price_element.text)
                    else:
                        continue  # Skip products without price
                
                # Get original price (if discounted)
                original_price = price
                original_price_element = card.select_one('.a-text-price .a-offscreen')
                if original_price_element:
                    original_price = extract_price(original_price_element.text)
                
                # Calculate discount percentage
                discount = 0
                if original_price > price and original_price > 0:
                    discount = round(((original_price - price) / original_price) * 100)
                
                # Get ratings
                rating = 0
                rating_element = card.select_one('.a-icon-star-small')
                if rating_element:
                    rating_text = rating_element.text.strip()
                    try:
                        # Extract the numeric rating (e.g., "4.5 out of 5 stars" -> 4.5)
                        rating = float(rating_text.split(' ')[0])
                    except (ValueError, IndexError):
                        pass
                
                # Get review count
                reviews = 0
                reviews_element = card.select_one('.a-size-base.s-underline-text')
                if reviews_element:
                    reviews_text = reviews_element.text.replace(',', '')
                    try:
                        reviews = int(''.join(filter(str.isdigit, reviews_text)))
                    except ValueError:
                        pass
                
                # Create product object
                product = {
                    'id': product_id or f"amazon-{count}",
                    'name': title,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': link,
                    'image_url': img_url,
                    'source': 'amazon'
                }
                
                products.append(product)
                count += 1
                
            except Exception as e:
                logger.warning(f"Error extracting Amazon product with BS4: {str(e)}")
                continue
        
        logger.info(f"Successfully scraped {len(products)} products from Amazon with BS4")
        
    except Exception as e:
        logger.error(f"Error in BS4 Amazon scraping: {str(e)}")
    
    return products

def get_amazon_in_products(query, limit=20, max_retries=3):
    """
    Get products from Amazon India using Selenium for enhanced scraping,
    with fallback to BeautifulSoup if Selenium fails
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        max_retries (int): Maximum number of retries for failed operations
        
    Returns:
        list: List of product dictionaries
    """
    products = []
    driver = None
    
    try:
        logger.info(f"Starting Amazon.in scrape for query: {query}")
        driver = create_webdriver(headless=True)
        
        # If driver creation failed, immediately fall back to BS4
        if not driver:
            logger.warning("Could not create WebDriver for Amazon, falling back to BS4")
            return scrape_amazon_with_bs4(query, limit=limit)
        
        # Encode search query for URL
        search_query = query.replace(' ', '+')
        url = f"https://www.amazon.in/s?k={search_query}"
        
        logger.info(f"Navigating to Amazon URL: {url}")
        driver.get(url)
        
        # Wait for search results to load
        random_sleep(2, 5)
        
        # Check if we're blocked or have a CAPTCHA
        if "Sorry, we just need to make sure you're not a robot" in driver.page_source:
            logger.warning("Amazon CAPTCHA detected, falling back to BS4")
            return scrape_amazon_with_bs4(query, limit=limit)
            
        # Get all product cards
        product_cards = driver.find_elements(By.CSS_SELECTOR, 
            'div[data-component-type="s-search-result"]')
        
        logger.info(f"Found {len(product_cards)} product cards on Amazon")
        
        count = 0
        for card in product_cards:
            if count >= limit:
                break
                
            try:
                # Extract product information
                title_element = card.find_element(By.CSS_SELECTOR, 'h2 a span')
                title = title_element.text.strip()
                
                # Skip sponsored products
                if "Sponsored" in card.text:
                    continue
                    
                # Get link
                link_element = card.find_element(By.CSS_SELECTOR, 'h2 a')
                link = link_element.get_attribute('href')
                
                # Extract product ID from URL
                product_id = None
                if '/dp/' in link:
                    product_id = link.split('/dp/')[1].split('/')[0].split('?')[0]
                
                # Get image
                img_element = card.find_element(By.CSS_SELECTOR, 'img')
                img_url = img_element.get_attribute('src')
                
                # Get price
                price_text = ""
                try:
                    price_element = card.find_element(By.CSS_SELECTOR, '.a-price .a-offscreen')
                    price_text = price_element.get_attribute('innerHTML')
                except NoSuchElementException:
                    # Try alternative price selector
                    try:
                        price_element = card.find_element(By.CSS_SELECTOR, '.a-price-whole')
                        price_text = "₹" + price_element.text
                    except NoSuchElementException:
                        continue  # Skip products without price
                
                price = extract_price(price_text)
                
                # Get original price (if discounted)
                original_price = price
                try:
                    original_price_element = card.find_element(By.CSS_SELECTOR, '.a-text-price .a-offscreen')
                    original_price_text = original_price_element.get_attribute('innerHTML')
                    original_price = extract_price(original_price_text)
                except NoSuchElementException:
                    pass  # No discount
                
                # Calculate discount percentage
                discount = 0
                if original_price > price and original_price > 0:
                    discount = round(((original_price - price) / original_price) * 100)
                
                # Get ratings
                rating = 0
                try:
                    rating_element = card.find_element(By.CSS_SELECTOR, 'i.a-icon-star-small')
                    rating_text = rating_element.get_attribute('innerHTML') or ""
                    if "stars" in rating_text.lower():
                        rating = float(rating_text.split(' ')[0])
                except (NoSuchElementException, ValueError, IndexError):
                    pass
                
                # Get review count
                reviews = 0
                try:
                    reviews_element = card.find_element(By.CSS_SELECTOR, 'span.a-size-base.s-underline-text')
                    reviews_text = reviews_element.text.replace(',', '')
                    reviews = int(reviews_text) if reviews_text.isdigit() else 0
                except (NoSuchElementException, ValueError):
                    pass
                
                # Create product object
                product = {
                    'id': product_id or f"amazon-{count}",
                    'name': title,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': link,
                    'image_url': img_url,
                    'source': 'amazon'
                }
                
                products.append(product)
                count += 1
                
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.warning(f"Error extracting product from Amazon: {str(e)}")
                continue
        
        # If we didn't get any products with Selenium, try BS4
        if len(products) == 0:
            logger.warning("No products found with Selenium, falling back to BS4")
            products = scrape_amazon_with_bs4(query, limit=limit)
            
        logger.info(f"Successfully scraped {len(products)} products from Amazon")
        return products
        
    except Exception as e:
        logger.error(f"Error scraping Amazon with Selenium: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fall back to BS4 if Selenium fails
        logger.info("Falling back to BS4 for Amazon scraping")
        fallback_products = scrape_amazon_with_bs4(query, limit=limit)
        if fallback_products:
            return fallback_products
            
        # Return whatever we got before the error
        return products
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def scrape_flipkart_with_bs4(query, limit=20):
    """
    Fallback method that uses BeautifulSoup to scrape Flipkart when Selenium fails
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        
    Returns:
        list: List of product dictionaries
    """
    import requests
    from bs4 import BeautifulSoup
    
    products = []
    
    try:
        # Encode search query for URL
        search_query = query.replace(' ', '+')
        url = f"https://www.flipkart.com/search?q={search_query}"
        
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        logger.info(f"Making BS4 request to Flipkart URL: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch Flipkart search results: HTTP {response.status_code}")
            return products
            
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find all product cards - different card layouts on Flipkart
        product_cards = soup.select('._1AtVbE')
        logger.info(f"Found {len(product_cards)} potential product cards on Flipkart with BS4")
        
        count = 0
        for card in product_cards:
            if count >= limit:
                break
                
            try:
                # Check if this is actually a product card (contains product info)
                title_element = card.select_one('._4rR01T, .s1Q9rs, .IRpwTa')
                if not title_element:
                    continue  # Not a product card
                
                # Extract product title
                title = title_element.text.strip()
                if not title:
                    continue
                
                # Get link
                link_element = card.select_one('a._1fQZEK, a.s1Q9rs, a._2rpwqI')
                if not link_element:
                    continue
                link = link_element.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://www.flipkart.com{link}"
                
                # Extract product ID from URL
                product_id = None
                if 'pid=' in link:
                    product_id = link.split('pid=')[1].split('&')[0]
                elif '/p/' in link:
                    product_id = link.split('/p/')[1].split('?')[0]
                
                # Get image
                img_url = ""
                img_element = card.select_one('img._396cs4, img._2r_T1I')
                if img_element:
                    img_url = img_element.get('src', '')
                
                # Get price
                price = 0
                price_element = card.select_one('._30jeq3')
                if price_element:
                    price = extract_price(price_element.text)
                else:
                    continue  # Skip products without price
                
                # Get original price (if discounted)
                original_price = price
                original_price_element = card.select_one('._3I9_wc')
                if original_price_element:
                    original_price = extract_price(original_price_element.text)
                
                # Calculate discount percentage
                discount = 0
                discount_element = card.select_one('._3Ay6Sb')
                if discount_element:
                    discount_text = discount_element.text
                    if "%" in discount_text:
                        try:
                            discount_match = re.search(r'(\d+)%', discount_text)
                            if discount_match:
                                discount = int(discount_match.group(1))
                        except (ValueError, AttributeError):
                            pass
                
                if discount == 0 and original_price > price and original_price > 0:
                    discount = round(((original_price - price) / original_price) * 100)
                
                # Get ratings
                rating = 0
                rating_element = card.select_one('._3LWZlK')
                if rating_element:
                    try:
                        rating = float(rating_element.text)
                    except ValueError:
                        pass
                
                # Get review count
                reviews = 0
                review_element = card.select_one('._2_R_DZ, ._13vcmD')
                if review_element:
                    review_text = review_element.text
                    if "ratings" in review_text.lower() or "reviews" in review_text.lower():
                        numbers = re.findall(r'\d+,?\d*', review_text)
                        if numbers:
                            try:
                                reviews = int(numbers[0].replace(',', ''))
                            except ValueError:
                                pass
                
                # Create product object
                product = {
                    'id': product_id or f"flipkart-{count}",
                    'name': title,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': link,
                    'image_url': img_url,
                    'source': 'flipkart'
                }
                
                products.append(product)
                count += 1
                
            except Exception as e:
                logger.warning(f"Error extracting Flipkart product with BS4: {str(e)}")
                continue
        
        logger.info(f"Successfully scraped {len(products)} products from Flipkart with BS4")
        
    except Exception as e:
        logger.error(f"Error in BS4 Flipkart scraping: {str(e)}")
    
    return products

def get_flipkart_products(query, limit=20, max_retries=3):
    """
    Get products from Flipkart using Selenium for enhanced scraping,
    with fallback to BeautifulSoup if Selenium fails
    
    Args:
        query (str): Search query
        limit (int): Maximum number of products to return
        max_retries (int): Maximum number of retries for failed operations
        
    Returns:
        list: List of product dictionaries
    """
    products = []
    driver = None
    
    try:
        logger.info(f"Starting Flipkart scrape for query: {query}")
        driver = create_webdriver(headless=True)
        
        # If driver creation failed, immediately fall back to BS4
        if not driver:
            logger.warning("Could not create WebDriver for Flipkart, falling back to BS4")
            return scrape_flipkart_with_bs4(query, limit=limit)
        
        # Encode search query for URL
        search_query = query.replace(' ', '+')
        url = f"https://www.flipkart.com/search?q={search_query}"
        
        logger.info(f"Navigating to Flipkart URL: {url}")
        driver.get(url)
        
        # Wait for search results to load
        random_sleep(2, 5)
        
        # Close login popup if it appears
        try:
            close_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z"))
            )
            close_button.click()
            random_sleep(1, 2)
        except TimeoutException:
            pass  # No popup appeared
            
        # Get all product cards
        product_cards = driver.find_elements(By.CSS_SELECTOR, 
            '._1AtVbE')
        
        logger.info(f"Found {len(product_cards)} potential product cards on Flipkart")
        
        count = 0
        for card in product_cards:
            if count >= limit:
                break
                
            try:
                # Check if this is actually a product card (contains product info)
                try:
                    title_element = card.find_element(By.CSS_SELECTOR, '._4rR01T, .s1Q9rs, .IRpwTa')
                except NoSuchElementException:
                    continue  # Not a product card
                    
                # Extract product title
                title = title_element.text.strip()
                if not title:
                    continue
                
                # Get link
                link_element = card.find_element(By.CSS_SELECTOR, 'a._1fQZEK, a.s1Q9rs, a._2rpwqI')
                link = link_element.get_attribute('href')
                
                # Extract product ID from URL
                product_id = None
                if 'pid=' in link:
                    product_id = link.split('pid=')[1].split('&')[0]
                elif '/p/' in link:
                    product_id = link.split('/p/')[1].split('?')[0]
                
                # Get image
                img_url = ""
                try:
                    img_element = card.find_element(By.CSS_SELECTOR, 'img._396cs4, img._2r_T1I')
                    img_url = img_element.get_attribute('src')
                except NoSuchElementException:
                    pass
                
                # Get price
                price = 0
                try:
                    price_element = card.find_element(By.CSS_SELECTOR, '._30jeq3')
                    price_text = price_element.text
                    price = extract_price(price_text)
                except NoSuchElementException:
                    continue  # Skip products without price
                
                # Get original price (if discounted)
                original_price = price
                try:
                    original_price_element = card.find_element(By.CSS_SELECTOR, '._3I9_wc')
                    original_price_text = original_price_element.text
                    original_price = extract_price(original_price_text)
                except NoSuchElementException:
                    pass  # No discount
                
                # Calculate discount percentage
                discount = 0
                try:
                    discount_element = card.find_element(By.CSS_SELECTOR, '._3Ay6Sb')
                    discount_text = discount_element.text
                    if "%" in discount_text:
                        discount = int(re.search(r'(\d+)%', discount_text).group(1))
                except (NoSuchElementException, AttributeError):
                    if original_price > price and original_price > 0:
                        discount = round(((original_price - price) / original_price) * 100)
                
                # Get ratings
                rating = 0
                try:
                    rating_element = card.find_element(By.CSS_SELECTOR, '._3LWZlK')
                    rating_text = rating_element.text
                    rating = float(rating_text)
                except (NoSuchElementException, ValueError):
                    pass
                
                # Get review count
                reviews = 0
                try:
                    review_element = card.find_element(By.CSS_SELECTOR, '._2_R_DZ, ._13vcmD')
                    review_text = review_element.text
                    if "ratings" in review_text.lower() or "reviews" in review_text.lower():
                        numbers = re.findall(r'\d+,?\d*', review_text)
                        if numbers:
                            reviews = int(numbers[0].replace(',', ''))
                except (NoSuchElementException, ValueError, IndexError):
                    pass
                
                # Create product object
                product = {
                    'id': product_id or f"flipkart-{count}",
                    'name': title,
                    'price': price,
                    'original_price': original_price,
                    'discount': discount,
                    'rating': rating,
                    'reviews': reviews,
                    'url': link,
                    'image_url': img_url,
                    'source': 'flipkart'
                }
                
                products.append(product)
                count += 1
                
            except (NoSuchElementException, StaleElementReferenceException) as e:
                logger.warning(f"Error extracting product from Flipkart: {str(e)}")
                continue
        
        # If we didn't get any products with Selenium, try BS4
        if len(products) == 0:
            logger.warning("No products found with Selenium for Flipkart, falling back to BS4")
            products = scrape_flipkart_with_bs4(query, limit=limit)
            
        logger.info(f"Successfully scraped {len(products)} products from Flipkart")
        return products
        
    except Exception as e:
        logger.error(f"Error scraping Flipkart with Selenium: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fall back to BS4 if Selenium fails
        logger.info("Falling back to BS4 for Flipkart scraping")
        fallback_products = scrape_flipkart_with_bs4(query, limit=limit)
        if fallback_products:
            return fallback_products
            
        # Return whatever we got before the error
        return products
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def verify_product_url(url, source):
    """
    Check if a product URL is valid by making a request
    
    Args:
        url (str): Product URL to verify
        source (str): Source website (amazon or flipkart)
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    if not url:
        return False
    
    import requests
    
    try:
        # Use requests instead of Selenium for faster checks
        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/'
        }
        
        logger.info(f"Verifying URL with requests: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"URL returned status code {response.status_code}: {url}")
            return False
        
        # Check for product availability markers in the HTML
        html_content = response.text.lower()
        
        if source.lower() == 'amazon':
            # Check if it's a valid Amazon product page
            return 'producttitle' in html_content or 'a-box-group' in html_content
        elif source.lower() == 'flipkart':
            # Check if it's a valid Flipkart product page
            return 'producttitle' in html_content or 'prod-right-container' in html_content
        
        return False
        
    except Exception as e:
        logger.warning(f"URL verification failed for {url}: {str(e)}")
        return False