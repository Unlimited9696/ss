const PriceChart = ({ historyData, product }) => {
    const chartRef = React.useRef(null);
    const [chartInstance, setChartInstance] = React.useState(null);
    const [chartError, setChartError] = React.useState(null);

    // Format price for display
    const formatPrice = (price) => {
        if (price === undefined || price === null) return "N/A";
        
        return new Intl.NumberFormat('en-IN', { 
            style: 'currency', 
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(price);
    };

    // Calculate price statistics
    const calculateStats = () => {
        const defaultPrice = product?.price || 0;
        
        if (!historyData || !Array.isArray(historyData) || historyData.length === 0) {
            return {
                lowestPrice: defaultPrice,
                highestPrice: defaultPrice,
                averagePrice: defaultPrice,
                current: defaultPrice,
                priceChange: 0,
                priceChangePercent: 0,
                lowestDate: null,
                highestDate: null,
                daysTracked: 0
            };
        }

        try {
            // Filter out any invalid prices
            const validData = historyData.filter(item => 
                item && typeof item.price === 'number' && !isNaN(item.price) && item.price > 0
            );
            
            if (validData.length === 0) {
                throw new Error("No valid price data found");
            }
            
            const prices = validData.map(item => item.price);
            const lowestPrice = Math.min(...prices);
            const highestPrice = Math.max(...prices);
            const averagePrice = prices.reduce((sum, price) => sum + price, 0) / prices.length;
            
            // Find dates for highest and lowest prices
            const lowestPriceItem = validData.find(item => item.price === lowestPrice);
            const highestPriceItem = validData.find(item => item.price === highestPrice);
            
            // Calculate price change (current vs first recorded)
            const current = prices[prices.length - 1];
            const first = prices[0];
            const priceChange = current - first;
            const priceChangePercent = first > 0 ? (priceChange / first) * 100 : 0;
            
            // Calculate days tracked
            const daysTracked = validData.length;

            return {
                lowestPrice,
                highestPrice,
                averagePrice,
                current,
                priceChange,
                priceChangePercent,
                lowestDate: lowestPriceItem?.date || null,
                highestDate: highestPriceItem?.date || null,
                daysTracked
            };
        } catch (error) {
            console.error("Error calculating stats:", error);
            setChartError("Could not calculate price statistics due to invalid data.");
            
            return {
                lowestPrice: defaultPrice,
                highestPrice: defaultPrice,
                averagePrice: defaultPrice,
                current: defaultPrice,
                priceChange: 0,
                priceChangePercent: 0,
                lowestDate: null,
                highestDate: null,
                daysTracked: 0
            };
        }
    };

    const stats = calculateStats();

    // Format date in a more readable way
    const formatDate = (dateString) => {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-IN', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        } catch (e) {
            return dateString;
        }
    };

    // Create or update chart when history data changes
    useEffect(() => {
        if (!historyData || !Array.isArray(historyData) || historyData.length === 0) {
            return;
        }
        
        try {
            const ctx = chartRef.current?.getContext('2d');
            if (!ctx) return;
            
            // Destroy previous chart if it exists
            if (chartInstance) {
                chartInstance.destroy();
            }
            
            // Reset any previous errors
            setChartError(null);
            
            // Filter out any invalid data points
            const validData = historyData.filter(item => 
                item && typeof item.price === 'number' && !isNaN(item.price) && item.date
            );
            
            if (validData.length === 0) {
                setChartError("No valid price data found for this product.");
                return;
            }
            
            // Sort by date
            validData.sort((a, b) => new Date(a.date) - new Date(b.date));
            
            // Prepare data for chart
            const labels = validData.map(item => formatDate(item.date));
            const prices = validData.map(item => item.price);
            
            // Calculate price gradients (green if price decreases, red if it increases)
            let gradientColor;
            
            if (prices.length >= 2) {
                const priceChange = prices[prices.length - 1] - prices[0];
                gradientColor = priceChange < 0 ? '#10b981' : '#ef4444';
            } else {
                gradientColor = '#0ea5e9';
            }
            
            // Create gradient for the area under the line
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, `${gradientColor}33`); // 20% opacity
            gradient.addColorStop(1, `${gradientColor}00`); // 0% opacity
            
            // Create new chart
            const newChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Price',
                        data: prices,
                        borderColor: gradientColor,
                        backgroundColor: gradient,
                        borderWidth: 2,
                        pointBackgroundColor: gradientColor,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Price: ${formatPrice(context.raw)}`;
                                },
                                title: function(context) {
                                    return formatDate(context[0].label);
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return formatPrice(value);
                                }
                            }
                        }
                    }
                }
            });
            
            setChartInstance(newChartInstance);
        } catch (error) {
            console.error("Error creating chart:", error);
            setChartError("There was a problem displaying the price history chart.");
        }
        
        // Cleanup function
        return () => {
            if (chartInstance) {
                chartInstance.destroy();
            }
        };
    }, [historyData]);

    // If there's no history data yet
    if (!historyData || !Array.isArray(historyData) || historyData.length === 0) {
        return (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <div className="text-4xl text-gray-300 mb-3">
                    <i className="fas fa-chart-line"></i>
                </div>
                <h3 className="text-gray-700 text-lg font-medium mb-2">No Price History Yet</h3>
                <p className="text-gray-500 max-w-md mx-auto">
                    We've just started tracking this product. Check back later to see how the price changes over time.
                </p>
                <div className="mt-6 p-4 bg-white rounded-lg border border-gray-200">
                    <h4 className="font-medium text-gray-700 mb-2">Current Product Price</h4>
                    <p className="text-2xl font-bold">{formatPrice(product?.price)}</p>
                    <p className="text-sm text-gray-500 mt-2">
                        From {product?.source?.charAt(0).toUpperCase() + product?.source?.slice(1) || 'Store'}
                    </p>
                </div>
            </div>
        );
    }

    // If there was an error creating the chart
    if (chartError) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <div className="text-3xl text-red-300 mb-3">
                    <i className="fas fa-exclamation-triangle"></i>
                </div>
                <h3 className="text-red-700 font-medium mb-2">Chart Error</h3>
                <p className="text-red-600 mb-4">{chartError}</p>
                <p className="text-gray-600">
                    We're still tracking the price; try selecting a different product or check back later.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Price change summary */}
            <div className="bg-gradient-to-r from-primary-50 via-secondary-50 to-primary-100 rounded-lg p-5 border border-primary-200 shadow-md">
                <div className="flex flex-wrap items-center justify-between">
                    <div>
                        <h3 className="font-semibold text-gray-800 text-lg flex items-center">
                            <div className="bg-primary-500 text-white p-2 rounded-full mr-3">
                                <i className="fas fa-exchange-alt"></i>
                            </div>
                            Price Change Summary
                        </h3>
                        <p className="text-sm text-gray-600 mt-2 ml-11">
                            Tracking for <span className="font-medium">{stats.daysTracked}</span> {stats.daysTracked === 1 ? 'day' : 'days'}
                        </p>
                    </div>
                    <div className={`px-4 py-2 rounded-full text-sm font-medium shadow-sm ${
                        stats.priceChange < 0 
                            ? 'bg-gradient-to-r from-green-500 to-green-600 text-white' 
                            : stats.priceChange > 0 
                                ? 'bg-gradient-to-r from-red-500 to-red-600 text-white' 
                                : 'bg-gradient-to-r from-gray-200 to-gray-300 text-gray-800'
                    }`}>
                        <span className="text-lg">{stats.priceChange < 0 ? '↓' : stats.priceChange > 0 ? '↑' : '='}</span>
                        <span className="ml-1">{formatPrice(Math.abs(stats.priceChange))}</span>
                        <span className="ml-1">({Math.abs(stats.priceChangePercent).toFixed(1)}%)</span>
                    </div>
                </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                {/* Price statistics cards */}
                <div className="lg:col-span-1 grid grid-cols-2 lg:grid-cols-1 gap-4">
                    <div className="bg-gradient-to-br from-white to-gray-50 rounded-lg p-5 shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
                        <div className="flex items-center mb-3">
                            <div className="bg-primary-100 text-primary-600 p-2 rounded-full mr-3">
                                <i className="fas fa-tag"></i>
                            </div>
                            <h3 className="text-sm font-medium text-gray-500">Current Price</h3>
                        </div>
                        <p className="text-3xl font-bold text-gray-800">{formatPrice(stats.current)}</p>
                        <div className="mt-2 text-xs text-gray-500 flex items-center">
                            <i className="fas fa-clock mr-1"></i>
                            Last updated: {formatDate(historyData[historyData.length - 1]?.date)}
                        </div>
                    </div>
                    
                    <div className="bg-gradient-to-br from-white to-green-50 rounded-lg p-5 shadow-md border border-green-200 hover:shadow-lg transition-shadow">
                        <div className="flex items-center mb-3">
                            <div className="bg-green-100 text-green-600 p-2 rounded-full mr-3">
                                <i className="fas fa-arrow-down"></i>
                            </div>
                            <h3 className="text-sm font-medium text-gray-500">Lowest Price</h3>
                        </div>
                        <p className="text-3xl font-bold text-green-600">{formatPrice(stats.lowestPrice)}</p>
                        {stats.lowestDate && (
                            <div className="mt-2 text-xs text-gray-500 flex items-center">
                                <i className="fas fa-calendar-alt mr-1"></i>
                                {formatDate(stats.lowestDate)}
                            </div>
                        )}
                    </div>
                    
                    <div className="bg-gradient-to-br from-white to-red-50 rounded-lg p-5 shadow-md border border-red-200 hover:shadow-lg transition-shadow">
                        <div className="flex items-center mb-3">
                            <div className="bg-red-100 text-red-600 p-2 rounded-full mr-3">
                                <i className="fas fa-arrow-up"></i>
                            </div>
                            <h3 className="text-sm font-medium text-gray-500">Highest Price</h3>
                        </div>
                        <p className="text-3xl font-bold text-red-600">{formatPrice(stats.highestPrice)}</p>
                        {stats.highestDate && (
                            <div className="mt-2 text-xs text-gray-500 flex items-center">
                                <i className="fas fa-calendar-alt mr-1"></i>
                                {formatDate(stats.highestDate)}
                            </div>
                        )}
                    </div>
                    
                    <div className="bg-gradient-to-br from-white to-blue-50 rounded-lg p-5 shadow-md border border-blue-200 hover:shadow-lg transition-shadow">
                        <div className="flex items-center mb-3">
                            <div className="bg-blue-100 text-blue-600 p-2 rounded-full mr-3">
                                <i className="fas fa-calculator"></i>
                            </div>
                            <h3 className="text-sm font-medium text-gray-500">Average Price</h3>
                        </div>
                        <p className="text-3xl font-bold text-blue-600">{formatPrice(stats.averagePrice)}</p>
                        <div className="mt-2 text-xs text-gray-500 flex items-center">
                            <i className="fas fa-chart-line mr-1"></i>
                            Based on {stats.daysTracked} price points
                        </div>
                    </div>
                </div>
                
                {/* Chart */}
                <div className="lg:col-span-3 bg-white rounded-lg p-5 shadow-md border border-gray-200">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                            <div className="bg-primary-500 text-white p-2 rounded-full mr-3">
                                <i className="fas fa-chart-line"></i>
                            </div>
                            Price History Chart
                        </h3>
                        <div className="text-sm text-gray-500 bg-primary-50 px-3 py-1 rounded-full">
                            <i className="fas fa-info-circle mr-1"></i> 
                            {historyData.length} data points
                        </div>
                    </div>
                    <div className="h-80 p-2">
                        <canvas ref={chartRef}></canvas>
                    </div>
                    <div className="text-xs text-center text-gray-500 mt-4 bg-gray-50 p-2 rounded-md">
                        <i className="fas fa-sync-alt mr-1"></i>
                        Updated automatically every 12 hours
                    </div>
                </div>
            </div>
            
            {/* Buy timing recommendation */}
            <div className="bg-gradient-to-r from-white to-accent-50 rounded-lg p-5 shadow-md border border-accent-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    <div className="bg-accent-500 text-white p-2 rounded-full mr-3">
                        <i className="fas fa-lightbulb"></i>
                    </div>
                    Buy Recommendation
                </h3>
                <div className="p-4 rounded-lg border border-accent-100 bg-white">
                    {stats.current <= stats.lowestPrice * 1.05 ? (
                        <div className="flex items-center">
                            <div className="bg-green-100 text-green-600 p-3 rounded-full mr-4">
                                <i className="fas fa-check-circle text-xl"></i>
                            </div>
                            <div>
                                <h4 className="font-semibold text-green-600">Great time to buy!</h4>
                                <p className="text-gray-600">Current price is at or near the lowest recorded price.</p>
                            </div>
                        </div>
                    ) : stats.current >= stats.highestPrice * 0.95 ? (
                        <div className="flex items-center">
                            <div className="bg-red-100 text-red-600 p-3 rounded-full mr-4">
                                <i className="fas fa-hand-paper text-xl"></i>
                            </div>
                            <div>
                                <h4 className="font-semibold text-red-600">Consider waiting for a price drop</h4>
                                <p className="text-gray-600">Current price is near the highest recorded.</p>
                            </div>
                        </div>
                    ) : stats.current < stats.averagePrice ? (
                        <div className="flex items-center">
                            <div className="bg-blue-100 text-blue-600 p-3 rounded-full mr-4">
                                <i className="fas fa-thumbs-up text-xl"></i>
                            </div>
                            <div>
                                <h4 className="font-semibold text-blue-600">Good time to buy</h4>
                                <p className="text-gray-600">Price is below average, which is a decent deal.</p>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center">
                            <div className="bg-gray-100 text-gray-600 p-3 rounded-full mr-4">
                                <i className="fas fa-clock text-xl"></i>
                            </div>
                            <div>
                                <h4 className="font-semibold text-gray-700">You might want to wait</h4>
                                <p className="text-gray-600">Price is above average. Better deals may come soon.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
