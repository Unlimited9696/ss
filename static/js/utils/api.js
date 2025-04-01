// API utility functions for fetching data from the backend

/**
 * Search for products
 * @param {string} query - Search query
 * @returns {Promise<object>} - Search results
 */
const searchProducts = async (query) => {
    try {
        const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            let errorMessage = 'Failed to search for products';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (jsonError) {
                // If we can't parse the response as JSON, use text content or status instead
                try {
                    const textContent = await response.text();
                    if (textContent && textContent.length < 100) {
                        errorMessage = textContent;
                    } else {
                        errorMessage = `Server error (${response.status})`;
                    }
                } catch (textError) {
                    errorMessage = `Server error (${response.status})`;
                }
            }
            throw new Error(errorMessage);
        }
        
        try {
            return await response.json();
        } catch (jsonError) {
            console.error('Error parsing JSON search results:', jsonError);
            // Return an empty result structure as fallback
            return {
                amazon: [],
                flipkart: [],
                timestamp: new Date().toISOString()
            };
        }
    } catch (error) {
        console.error('Error searching for products:', error);
        throw new Error(error.message || 'An error occurred while searching for products');
    }
};

/**
 * Get price history for a product
 * @param {string} query - Search query
 * @param {string} productId - Product ID
 * @param {string} source - Source (e.g., amazon, flipkart)
 * @returns {Promise<Array>} - Price history data
 */
const getPriceHistory = async (query, productId, source) => {
    try {
        const response = await fetch(`/api/price-history?query=${encodeURIComponent(query)}&product_id=${encodeURIComponent(productId)}&source=${encodeURIComponent(source)}`);
        
        if (!response.ok) {
            let errorMessage = 'Failed to fetch price history';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (jsonError) {
                // If we can't parse the response as JSON, use text content or status instead
                try {
                    const textContent = await response.text();
                    if (textContent && textContent.length < 100) {
                        errorMessage = textContent;
                    } else {
                        errorMessage = `Server error (${response.status})`;
                    }
                } catch (textError) {
                    errorMessage = `Server error (${response.status})`;
                }
            }
            throw new Error(errorMessage);
        }
        
        try {
            return await response.json();
        } catch (jsonError) {
            console.error('Error parsing JSON for price history:', jsonError);
            return []; // Return empty array as fallback
        }
    } catch (error) {
        console.error('Error fetching price history:', error);
        throw new Error(error.message || 'An error occurred while fetching price history');
    }
};

/**
 * Manually update prices
 * @returns {Promise<object>} - Update status
 */
const updatePrices = async () => {
    try {
        const response = await fetch('/api/update-prices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to update prices';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (jsonError) {
                // If we can't parse the response as JSON, use text content or status instead
                try {
                    const textContent = await response.text();
                    if (textContent && textContent.length < 100) {
                        errorMessage = textContent;
                    } else {
                        errorMessage = `Server error (${response.status})`;
                    }
                } catch (textError) {
                    errorMessage = `Server error (${response.status})`;
                }
            }
            throw new Error(errorMessage);
        }
        
        try {
            return await response.json();
        } catch (jsonError) {
            console.error('Error parsing JSON response:', jsonError);
            return { message: 'Operation completed, but response was not valid JSON' };
        }
    } catch (error) {
        console.error('Error updating prices:', error);
        throw new Error(error.message || 'An error occurred while updating prices');
    }
};
