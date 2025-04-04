import os
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from simple_scraper import search_products as scrape_products, verify_product_url
from scheduler import start_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
CORS(app)

# In-memory storage for product data
product_data = {}
price_history = {}

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search_products_route():
    """Search for products and return the data"""
    try:
        query = request.args.get('query', '')

        if not query:
            return jsonify({"error": "No search query provided"}), 400

        # Clean up query to avoid injection or problematic characters
        query = query.strip()[:100]  # Limit length

        # Check if we already have data for this query
        if query in product_data:
            return jsonify(product_data[query])

        # If not, trigger scraping with the new robust scraper
        try:
            app.logger.info(f"Searching for products matching '{query}'")

            # Use new enhanced robust scraper that handles retries internally
            # Wrap the scraper call in a try-except to make sure it doesn't crash the server
            try:
                # First try with default limit
                results = scrape_products(query, limit=20)

                # If no results, try with mobile user agent and smaller limit
                if not results['amazon'] and not results['meesho']:
                    app.logger.info("Retrying with mobile configuration...")
                    results = scrape_products(query, limit=10, mobile=True) # Added mobile flag

            except Exception as scrape_error:
                app.logger.exception(f"Scraper error for '{query}': {str(scrape_error)}")
                results = {
                    "amazon": [],
                    "meesho": [],
                    "timestamp": datetime.now().isoformat(),
                    "error": "Error while scraping products"
                }

            # Ensure we have valid structure
            if not isinstance(results, dict):
                app.logger.warning(f"Search returned invalid result type: {type(results)}")
                results = {
                    "amazon": [],
                    "meesho": [],
                    "timestamp": datetime.now().isoformat(),
                    "error": "Invalid search result format"
                }

            # Validate amazon and meesho results exist in response
            if 'amazon' not in results:
                app.logger.warning("Amazon results missing from search response")
                results['amazon'] = []

            if 'meesho' not in results:
                app.logger.warning("Meesho results missing from search response")
                results['meesho'] = []

            # Ensure timestamp exists
            if 'timestamp' not in results:
                results['timestamp'] = datetime.now().isoformat()

            # Check if we have results
            if not results['amazon'] and not results['meesho']:
                app.logger.warning(f"No results found from any source for query: {query}")
                error_message = f"No products found for '{query}'. Try a different search term."

                return jsonify({
                    "error": error_message,
                    "amazon": [],
                    "meesho": [],
                    "timestamp": datetime.now().isoformat()
                }), 404

            # Store in memory
            product_data[query] = results

            # Initialize price history if not exists
            if query not in price_history:
                price_history[query] = {}

            # Update price history
            current_date = datetime.now().strftime('%Y-%m-%d')
            for source, products in results.items():
                if source not in ['amazon', 'meesho']:
                    continue

                if source not in price_history[query]:
                    price_history[query][source] = {}

                for product in products:
                    # Skip invalid products
                    if not isinstance(product, dict):
                        continue

                    product_id = product.get('id')
                    if not product_id:
                        continue

                    if product_id not in price_history[query][source]:
                        price_history[query][source][product_id] = []

                    # Add today's price to history
                    price_history[query][source][product_id].append({
                        'date': current_date,
                        'price': product.get('price', 0)
                    })

            app.logger.info(f"Successfully found {len(results.get('amazon', []))} Amazon products and {len(results.get('meesho', []))} Meesho products")
            return jsonify(results)

        except Exception as e:
            app.logger.exception(f"Error during product search for '{query}': {str(e)}")
            return jsonify({
                "error": f"An error occurred while searching for products: {str(e)}",
                "amazon": [],
                "meesho": [],
                "timestamp": datetime.now().isoformat()
            }), 500

    except Exception as outer_e:
        # Catch any unexpected errors to make sure server doesn't crash
        app.logger.exception(f"Unexpected error in search_products: {str(outer_e)}")
        return jsonify({
            "error": "An unexpected error occurred. Please try again later.",
            "amazon": [],
            "meesho": [],
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/price-history', methods=['GET'])
def get_price_history():
    """Get historical price data for a product"""
    try:
        query = request.args.get('query', '')
        product_id = request.args.get('product_id', '')
        source = request.args.get('source', '')

        if not query or not product_id or not source:
            return jsonify({"error": "Missing required parameters"}), 400

        # Validate source parameter
        if source not in ['amazon', 'meesho']:
            return jsonify({
                "error": f"Invalid source: '{source}'. Must be 'amazon' or 'meesho'",
                "data": []
            }), 400

        # Handle cases where price history doesn't exist for the query, source, or product
        if query not in price_history:
            app.logger.info(f"No price history for query: {query}")
            return jsonify([]), 200

        if source not in price_history[query]:
            app.logger.info(f"No price history for source: {source} in query: {query}")
            return jsonify([]), 200

        if product_id not in price_history[query][source]:
            app.logger.info(f"No price history for product: {product_id} in source: {source} for query: {query}")
            return jsonify([]), 200

        # Validate price history data structure
        history_data = price_history[query][source][product_id]
        if not isinstance(history_data, list):
            app.logger.warning(f"Invalid price history data structure for {query}/{source}/{product_id}")
            return jsonify([]), 200

        # Return valid price history data
        return jsonify(history_data)

    except Exception as e:
        app.logger.exception(f"Error retrieving price history: {str(e)}")
        return jsonify({
            "error": f"Failed to retrieve price history: {str(e)}",
            "data": []
        }), 500

@app.route('/api/update-prices', methods=['POST'])
def update_prices():
    """Manual trigger to update prices for tracked products"""
    update_results = {
        "success": [],
        "failures": []
    }

    try:
        # Create a copy of keys to avoid modifying the dictionary during iteration
        query_list = list(product_data.keys()) 

        for query in query_list:
            try:
                app.logger.info(f"Updating prices for '{query}'")

                # Use new enhanced robust scraper that handles retries internally
                results = scrape_products(query, limit=20)

                # Ensure we have valid structure
                if not isinstance(results, dict):
                    app.logger.warning(f"Search returned invalid result type: {type(results)}")
                    results = {
                        "amazon": [],
                        "meesho": [],
                        "timestamp": datetime.now().isoformat(),
                        "error": "Invalid search result format"
                    }

                # Validate amazon and meesho results exist in response
                if 'amazon' not in results:
                    app.logger.warning("Amazon results missing from search response")
                    results['amazon'] = []

                if 'meesho' not in results:
                    app.logger.warning("Meesho results missing from search response")
                    results['meesho'] = []

                # Ensure timestamp exists
                if 'timestamp' not in results:
                    results['timestamp'] = datetime.now().isoformat()

                # Check if we have results
                if not results['amazon'] and not results['meesho']:
                    app.logger.warning(f"No results found from any source for query: {query} during price update")
                    error_msg = f"No products found for '{query}'"
                    update_results["failures"].append({"query": query, "reason": error_msg})
                    continue

                # Update stored data
                product_data[query] = results

                # Update price history
                current_date = datetime.now().strftime('%Y-%m-%d')
                for source, products in results.items():
                    if source not in ['amazon', 'meesho']:
                        continue

                    if source not in price_history[query]:
                        price_history[query][source] = {}

                    for product in products:
                        # Skip invalid products
                        if not isinstance(product, dict):
                            continue

                        product_id = product.get('id')
                        if not product_id:
                            continue

                        if product_id not in price_history[query][source]:
                            price_history[query][source][product_id] = []

                        # Add today's price to history
                        price_history[query][source][product_id].append({
                            'date': current_date,
                            'price': product.get('price', 0)
                        })

                # Record success
                update_results["success"].append(query)
                app.logger.info(f"Successfully updated prices for '{query}' with {len(results.get('amazon', []))} Amazon products and {len(results.get('meesho', []))} Meesho products")

            except Exception as e:
                app.logger.error(f"Error updating prices for query '{query}': {str(e)}")
                update_results["failures"].append({"query": query, "reason": str(e)})

        return jsonify({
            "message": f"Price update completed with {len(update_results['success'])} successes and {len(update_results['failures'])} failures",
            "details": update_results
        })

    except Exception as e:
        app.logger.exception(f"Critical error during price update: {str(e)}")
        return jsonify({
            "error": f"Failed to update prices: {str(e)}",
            "details": update_results
        }), 500

# Start the scheduler for periodic updates
start_scheduler(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)