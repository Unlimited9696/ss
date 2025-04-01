const { useState, useEffect } = React;

const App = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [priceHistory, setPriceHistory] = useState(null);
    const [isHistoryLoading, setIsHistoryLoading] = useState(false);

    // Handle search submission
    const handleSearch = async (query) => {
        setSearchQuery(query);
        setIsLoading(true);
        setError(null);
        setSelectedProduct(null);
        setPriceHistory(null);
        
        try {
            const data = await searchProducts(query);
            setSearchResults(data);
        } catch (err) {
            setError(err.message || 'Failed to fetch search results');
        } finally {
            setIsLoading(false);
        }
    };

    // Handle product selection
    const handleProductSelect = async (product) => {
        setSelectedProduct(product);
        setIsHistoryLoading(true);
        
        try {
            const historyData = await getPriceHistory(searchQuery, product.id, product.source);
            setPriceHistory(historyData);
        } catch (err) {
            console.error('Failed to fetch price history:', err);
        } finally {
            setIsHistoryLoading(false);
        }
    };

    // Calculate best deal
    const getBestDeal = () => {
        if (!searchResults) return null;
        
        let bestDeal = null;
        let lowestPrice = Infinity;
        
        // Check Amazon products
        if (searchResults.amazon) {
            searchResults.amazon.forEach(product => {
                if (product.price < lowestPrice) {
                    lowestPrice = product.price;
                    bestDeal = product;
                }
            });
        }
        
        // Check Flipkart products
        if (searchResults.flipkart) {
            searchResults.flipkart.forEach(product => {
                if (product.price < lowestPrice) {
                    lowestPrice = product.price;
                    bestDeal = product;
                }
            });
        }
        
        return bestDeal;
    };

    // Get all products for comparison
    const getAllProducts = () => {
        if (!searchResults) return [];
        
        let allProducts = [];
        
        if (searchResults.amazon) {
            allProducts = [...allProducts, ...searchResults.amazon];
        }
        
        if (searchResults.flipkart) {
            allProducts = [...allProducts, ...searchResults.flipkart];
        }
        
        // Sort by price (lowest first)
        return allProducts.sort((a, b) => a.price - b.price);
    };

    return (
        <div className="flex flex-col min-h-screen bg-gray-50">
            {/* Header */}
            <header className="w-full py-5 px-6 gradient-bg text-white shadow-lg">
                <div className="container mx-auto flex flex-col md:flex-row justify-between items-center">
                    <div className="flex items-center mb-4 md:mb-0">
                        <div className="flex items-center bg-white bg-opacity-20 p-2 rounded-full mr-3">
                            <i className="fas fa-tags text-3xl text-white"></i>
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold">PriceTracker</h1>
                            <p className="text-xs text-gray-200">Find the best deals across Indian e-commerce sites</p>
                        </div>
                    </div>
                    <div className="w-full md:w-1/2">
                        <ProductSearch onSearch={handleSearch} />
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-grow container mx-auto px-4 py-8">
                {/* Loading State */}
                {isLoading && (
                    <div className="flex flex-col justify-center items-center py-20">
                        <div className="relative">
                            <div className="relative mx-auto w-28 h-28 mb-6">
                                <div className="absolute top-0 left-0 w-full h-full border-4 border-primary-200 rounded-full"></div>
                                <div className="absolute top-0 left-0 w-full h-full border-4 border-primary-500 rounded-full border-t-transparent animate-spin"></div>
                                <div className="absolute top-0 left-0 w-full h-full border-4 border-accent-300 rounded-full border-t-transparent border-b-transparent animate-spin" style={{animationDuration: '1.8s'}}></div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <i className="fas fa-search text-primary-500 text-2xl animate-pulse"></i>
                                </div>
                            </div>
                        </div>
                        
                        <h3 className="text-xl font-medium text-gray-900 mb-2">Searching across stores...</h3>
                        <p className="text-gray-500 text-center max-w-md">
                            We're finding the best deals for "<span className="text-primary-600 font-medium">{searchQuery}</span>" across popular Indian e-commerce sites.
                        </p>
                        
                        <div className="bg-gradient-to-r from-gray-50 to-primary-50 p-4 rounded-lg border border-gray-200 max-w-md mt-5">
                            <div className="flex items-start space-x-3">
                                <div className="mt-1 text-accent-500">
                                    <i className="fas fa-info-circle"></i>
                                </div>
                                <div>
                                    <h4 className="font-medium text-gray-700 mb-1">Real-time price search</h4>
                                    <p className="text-sm text-gray-600">
                                        Our AI-powered scrapers are collecting data from multiple sources. This may take up to 30 seconds due to anti-scraping protections.
                                    </p>
                                    <div className="flex items-center mt-3 space-x-4">
                                        <div className="flex items-center space-x-1">
                                            <div className="animate-pulse h-2 w-2 bg-green-400 rounded-full"></div>
                                            <span className="text-xs text-gray-500">Amazon.in</span>
                                        </div>
                                        <div className="flex items-center space-x-1">
                                            <div className="animate-pulse h-2 w-2 bg-blue-400 rounded-full" style={{animationDelay: '0.2s'}}></div>
                                            <span className="text-xs text-gray-500">Flipkart</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div className="mt-6 loader-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-6 my-6 max-w-2xl mx-auto shadow-md">
                        <div className="flex items-center mb-4">
                            <div className="flex-shrink-0 bg-red-100 rounded-full p-3">
                                <i className="fas fa-exclamation-triangle text-red-500 text-xl"></i>
                            </div>
                            <h3 className="ml-4 text-xl font-semibold text-gray-900">We encountered a problem</h3>
                        </div>
                        <p className="mb-4 text-gray-700">{error}</p>
                        <div className="bg-white p-4 rounded-md border border-red-100 mb-4 frosted-glass">
                            <p className="text-sm text-gray-600">
                                Sometimes e-commerce websites temporarily block our search requests. 
                                Please try again in a few minutes or try a different search term.
                            </p>
                        </div>
                        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
                            <h4 className="text-primary-700 font-medium mb-2 flex items-center">
                                <i className="fas fa-lightbulb text-yellow-500 mr-2"></i>
                                Suggestion
                            </h4>
                            <p className="text-gray-700">
                                Try these popular terms that typically work well:
                            </p>
                            <div className="flex flex-wrap gap-2 mt-3">
                                {["smartphone", "laptop", "headphones", "smartwatch", "camera"].map((term, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleSearch(term)}
                                        className="px-3 py-1.5 bg-white border border-primary-200 text-primary-700 rounded-full hover:bg-primary-50 transition-colors text-sm"
                                    >
                                        {term}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="flex flex-wrap gap-4 mt-6">
                            <button
                                onClick={() => handleSearch(searchQuery)}
                                className="px-4 py-2 gradient-accent text-white rounded-lg hover:shadow-md transition-all"
                            >
                                <i className="fas fa-redo mr-2"></i>Try Again
                            </button>
                            <button
                                onClick={() => {
                                    setSearchQuery('');
                                    setError(null);
                                }}
                                className="px-4 py-2 bg-white border border-gray-300 text-gray-800 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                <i className="fas fa-search mr-2"></i>New Search
                            </button>
                        </div>
                    </div>
                )}

                {/* Results */}
                {searchResults && !isLoading && (
                    <div className="grid grid-cols-1 gap-6">
                        {/* Best Deal Section */}
                        {getBestDeal() && (
                            <div className="bg-gradient-to-r from-accent-50 via-secondary-50 to-primary-50 rounded-lg p-6 shadow-md border border-accent-200">
                                <h2 className="text-xl font-bold mb-3 text-gray-800 flex items-center">
                                    <div className="bg-accent-500 text-white p-2 rounded-full mr-3">
                                        <i className="fas fa-award"></i>
                                    </div>
                                    Best Deal Found
                                </h2>
                                <div className="flex flex-col md:flex-row">
                                    <ProductCard 
                                        product={getBestDeal()} 
                                        onSelect={handleProductSelect}
                                        isSelected={selectedProduct && selectedProduct.id === getBestDeal().id}
                                        isBestDeal={true}
                                    />
                                </div>
                            </div>
                        )}

                        {/* Selected Product Detail */}
                        {selectedProduct && (
                            <div className="bg-white rounded-lg p-6 shadow-md border border-primary-100">
                                <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center">
                                    <div className="bg-primary-500 text-white p-2 rounded-full mr-3">
                                        <i className="fas fa-chart-line"></i>
                                    </div>
                                    Price History & Trends
                                </h2>
                                
                                {isHistoryLoading ? (
                                    <div className="flex justify-center items-center py-8">
                                        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary-600"></div>
                                        <span className="ml-3 text-gray-600">Loading price history...</span>
                                    </div>
                                ) : (
                                    <PriceChart 
                                        historyData={priceHistory} 
                                        product={selectedProduct}
                                    />
                                )}
                            </div>
                        )}

                        {/* Comparison Table */}
                        <div className="bg-white rounded-lg p-6 shadow-md border border-gray-200">
                            <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center">
                                <div className="bg-gray-700 text-white p-2 rounded-full mr-3">
                                    <i className="fas fa-balance-scale"></i>
                                </div>
                                Price Comparison
                            </h2>
                            <ComparisonTable 
                                products={getAllProducts()} 
                                onSelect={handleProductSelect}
                                selectedProductId={selectedProduct ? selectedProduct.id : null}
                            />
                        </div>

                        {/* Product Cards Grid */}
                        <div className="bg-gradient-to-br from-gray-50 to-white rounded-lg p-6 shadow-md border border-gray-200">
                            <h2 className="text-xl font-bold mb-4 text-gray-800 flex items-center">
                                <div className="gradient-accent text-white p-2 rounded-full mr-3">
                                    <i className="fas fa-shopping-cart"></i>
                                </div>
                                All Products
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                {getAllProducts().map(product => (
                                    <ProductCard 
                                        key={`${product.source}-${product.id}`}
                                        product={product} 
                                        onSelect={handleProductSelect}
                                        isSelected={selectedProduct && selectedProduct.id === product.id}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!searchResults && !isLoading && !error && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <div className="relative w-32 h-32 mb-6">
                            <div className="absolute top-0 left-0 w-full h-full bg-primary-100 rounded-full pulse-animation"></div>
                            <div className="absolute inset-0 flex items-center justify-center text-6xl text-primary-500">
                                <i className="fas fa-search"></i>
                            </div>
                        </div>
                        <h2 className="text-3xl font-bold text-gray-800 mb-3">Search for a product</h2>
                        <p className="text-gray-500 max-w-lg mb-8 text-lg">
                            Enter a product name to compare prices from Amazon, Flipkart, and more.
                            We'll find the best deals for you!
                        </p>
                        <div className="flex flex-wrap justify-center gap-3">
                            {["smartphone", "laptop", "watch", "headphones", "camera"].map((item, index) => (
                                <button 
                                    key={index}
                                    onClick={() => handleSearch(item)}
                                    className="px-4 py-2 bg-white border border-gray-300 rounded-full text-gray-700 hover:bg-gray-50 transition-colors"
                                >
                                    {item}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="gradient-bg text-white py-8 px-4">
                <div className="container mx-auto">
                    <div className="flex flex-col md:flex-row justify-between items-center">
                        <div className="mb-6 md:mb-0">
                            <div className="flex items-center">
                                <div className="flex items-center bg-white bg-opacity-10 p-2 rounded-full mr-3">
                                    <i className="fas fa-tags text-xl text-white"></i>
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold">PriceTracker</h2>
                                    <p className="text-sm text-gray-200 mt-1">
                                        Compare prices across Indian e-commerce sites
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="flex space-x-6">
                            <a href="#" className="text-white hover:text-accent-300 transition-colors text-xl">
                                <i className="fab fa-twitter"></i>
                            </a>
                            <a href="#" className="text-white hover:text-accent-300 transition-colors text-xl">
                                <i className="fab fa-facebook"></i>
                            </a>
                            <a href="#" className="text-white hover:text-accent-300 transition-colors text-xl">
                                <i className="fab fa-instagram"></i>
                            </a>
                        </div>
                    </div>
                    <hr className="border-white border-opacity-20 my-6" />
                    <div className="flex flex-col md:flex-row justify-between items-center text-sm text-gray-300">
                        <p>
                            &copy; {new Date().getFullYear()} PriceTracker. All rights reserved.
                        </p>
                        <div className="mt-4 md:mt-0 flex space-x-6">
                            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                            <a href="#" className="hover:text-white transition-colors">Contact Us</a>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

// Render the App component
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
