const ComparisonTable = ({ products, onSelect, selectedProductId }) => {
    const [sortConfig, setSortConfig] = useState({
        key: 'price',
        direction: 'ascending'
    });
    const [visibleColumns, setVisibleColumns] = useState({
        store: true,
        product: true,
        price: true,
        discount: true,
        rating: true,
        actions: true
    });
    const [hoveredRowId, setHoveredRowId] = useState(null);

    // Format price to show currency symbol and 2 decimal places
    const formatPrice = (price) => {
        if (!price && price !== 0) return "Price unavailable";
        
        return new Intl.NumberFormat('en-IN', { 
            style: 'currency', 
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        }).format(price);
    };

    // Handle sort change
    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    // Sort products based on current sort configuration
    const sortedProducts = React.useMemo(() => {
        if (!products || !Array.isArray(products)) return [];
        
        return [...products].sort((a, b) => {
            // Handle undefined values
            const aValue = a[sortConfig.key] ?? 0;
            const bValue = b[sortConfig.key] ?? 0;
            
            if (aValue < bValue) {
                return sortConfig.direction === 'ascending' ? -1 : 1;
            }
            if (aValue > bValue) {
                return sortConfig.direction === 'ascending' ? 1 : -1;
            }
            return 0;
        });
    }, [products, sortConfig.key, sortConfig.direction]);

    // Get site logo/icon based on source
    const getSiteInfo = (source) => {
        switch((source || "").toLowerCase()) {
            case 'amazon':
                return {
                    icon: <i className="fab fa-amazon"></i>,
                    color: "text-orange-600",
                    bgColor: "bg-orange-100",
                    borderColor: "border-orange-200",
                    gradientColor: "from-orange-500 to-amber-500",
                    name: "Amazon"
                };
            case 'meesho':
                return {
                    icon: <i className="fas fa-store-alt"></i>,
                    color: "text-pink-600",
                    bgColor: "bg-pink-100",
                    borderColor: "border-pink-200",
                    gradientColor: "from-pink-500 to-rose-500",
                    name: "Meesho"
                };
            default:
                return {
                    icon: <i className="fas fa-store"></i>,
                    color: "text-gray-600",
                    bgColor: "bg-gray-100",
                    borderColor: "border-gray-200",
                    gradientColor: "from-gray-500 to-gray-600",
                    name: source || "Store"
                };
        }
    };

    // Generate sort icon based on current sort configuration
    const getSortIcon = (key) => {
        if (sortConfig.key === key) {
            return sortConfig.direction === 'ascending' 
                ? <i className="fas fa-sort-up ml-1"></i> 
                : <i className="fas fa-sort-down ml-1"></i>;
        }
        return <i className="fas fa-sort ml-1 text-gray-300"></i>;
    };

    // Toggle column visibility
    const toggleColumn = (column) => {
        setVisibleColumns({
            ...visibleColumns,
            [column]: !visibleColumns[column]
        });
    };

    // Get the lowest priced product
    const getLowestPricedProduct = () => {
        if (!sortedProducts || sortedProducts.length === 0) return null;
        return sortedProducts.reduce((lowest, current) => 
            (current.price < lowest.price) ? current : lowest, sortedProducts[0]);
    };

    // Get the highest rated product
    const getHighestRatedProduct = () => {
        if (!sortedProducts || sortedProducts.length === 0) return null;
        return sortedProducts.reduce((highest, current) => 
            (current.rating > highest.rating) ? current : highest, sortedProducts[0]);
    };

    const lowestPricedProduct = getLowestPricedProduct();
    const highestRatedProduct = getHighestRatedProduct();

    if (!products || !Array.isArray(products) || products.length === 0) {
        return (
            <div className="bg-gradient-to-br from-gray-50 to-white border border-gray-200 rounded-lg p-8 text-center shadow-md">
                <div className="text-4xl text-gray-300 mb-3">
                    <i className="fas fa-table"></i>
                </div>
                <h3 className="text-gray-700 text-lg font-medium mb-2">No Products to Compare</h3>
                <p className="text-gray-500 max-w-md mx-auto">
                    We couldn't find any products matching your search criteria. 
                    Try modifying your search or try again later.
                </p>
            </div>
        );
    }

    // Get total number of products and sources
    const totalProducts = sortedProducts.length;
    const uniqueSources = [...new Set(sortedProducts.map(p => p.source))];

    return (
        <div className="space-y-4">
            {/* Table stats and controls */}
            <div className="flex flex-wrap items-center justify-between bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4 text-sm shadow-sm border border-primary-200">
                <div className="text-gray-700 mb-3 md:mb-0 flex items-center">
                    <i className="fas fa-table text-primary-500 mr-2"></i>
                    <span className="font-medium text-primary-800">{totalProducts}</span> products from 
                    <span className="font-medium text-primary-800 mx-1">{uniqueSources.length}</span> 
                    {uniqueSources.length === 1 ? "store" : "stores"}
                </div>
                
                <div className="flex space-x-2">
                    <button 
                        onClick={() => setSortConfig({ key: 'price', direction: 'ascending' })}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${sortConfig.key === 'price' && sortConfig.direction === 'ascending' 
                            ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md' 
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'}`}
                    >
                        <i className="fas fa-sort-amount-down-alt mr-1"></i> Price: Low to High
                    </button>
                    <button 
                        onClick={() => setSortConfig({ key: 'rating', direction: 'descending' })}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${sortConfig.key === 'rating' && sortConfig.direction === 'descending' 
                            ? 'bg-gradient-to-r from-yellow-500 to-amber-500 text-white shadow-md' 
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'}`}
                    >
                        <i className="fas fa-star mr-1"></i> Best Rated
                    </button>
                    <button 
                        onClick={() => setSortConfig({ key: 'discount', direction: 'descending' })}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all duration-200 ${sortConfig.key === 'discount' && sortConfig.direction === 'descending' 
                            ? 'bg-gradient-to-r from-accent-500 to-accent-600 text-white shadow-md' 
                            : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'}`}
                    >
                        <i className="fas fa-percent mr-1"></i> Highest Discount
                    </button>
                </div>
            </div>
            
            {/* Table */}
            <div className="overflow-x-auto border border-gray-200 rounded-xl shadow-md bg-white">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                        <tr className="bg-gradient-to-r from-gray-50 to-gray-100">
                            {visibleColumns.store && (
                                <th scope="col" className="py-3.5 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Store
                                </th>
                            )}
                            {visibleColumns.product && (
                                <th scope="col" className="py-3.5 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Product
                                </th>
                            )}
                            {visibleColumns.price && (
                                <th 
                                    scope="col" 
                                    className="py-3.5 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                                    onClick={() => requestSort('price')}
                                >
                                    <span className="flex items-center">
                                        Price {getSortIcon('price')}
                                    </span>
                                </th>
                            )}
                            {visibleColumns.discount && (
                                <th 
                                    scope="col" 
                                    className="py-3.5 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                                    onClick={() => requestSort('discount')}
                                >
                                    <span className="flex items-center">
                                        Discount {getSortIcon('discount')}
                                    </span>
                                </th>
                            )}
                            {visibleColumns.rating && (
                                <th 
                                    scope="col" 
                                    className="py-3.5 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors"
                                    onClick={() => requestSort('rating')}
                                >
                                    <span className="flex items-center">
                                        Rating {getSortIcon('rating')}
                                    </span>
                                </th>
                            )}
                            {visibleColumns.actions && (
                                <th scope="col" className="py-3.5 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            )}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {sortedProducts.map((product) => {
                            const siteInfo = getSiteInfo(product.source);
                            const rowId = `${product.source || 'unknown'}-${product.id || Math.random().toString(36).substring(2)}`;
                            const isSelected = selectedProductId === product.id;
                            const isLowestPrice = product.id === lowestPricedProduct?.id;
                            const isHighestRated = product.id === highestRatedProduct?.id && product.rating >= 4;

                            return (
                                <tr 
                                    key={rowId}
                                    className={`transition-colors ${
                                        isSelected ? 'bg-primary-50 border-l-4 border-l-primary-500' : 
                                        hoveredRowId === rowId ? 'bg-gray-50' : 'bg-white'
                                    } cursor-pointer relative`}
                                    onClick={() => onSelect(product)}
                                    onMouseEnter={() => setHoveredRowId(rowId)}
                                    onMouseLeave={() => setHoveredRowId(null)}
                                >
                                    {/* Row badges */}
                                    <div className="absolute right-0 -top-1 flex space-x-1 z-10">
                                        {isLowestPrice && (
                                            <div className="bg-green-100 text-green-800 text-xs px-1.5 py-0.5 rounded-bl-md border border-green-200 font-medium whitespace-nowrap">
                                                <i className="fas fa-tags text-green-500 mr-1"></i> Best Price
                                            </div>
                                        )}
                                        {isHighestRated && (
                                            <div className="bg-yellow-100 text-yellow-800 text-xs px-1.5 py-0.5 rounded-bl-md border border-yellow-200 font-medium whitespace-nowrap">
                                                <i className="fas fa-star text-yellow-500 mr-1"></i> Top Rated
                                            </div>
                                        )}
                                    </div>

                                    {visibleColumns.store && (
                                        <td className="py-4 px-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className={`bg-gradient-to-r ${siteInfo.gradientColor} text-white p-1.5 rounded-full shadow-sm mr-2.5`}>
                                                    {siteInfo.icon}
                                                </div>
                                                <span className="font-medium text-gray-900">{siteInfo.name}</span>
                                            </div>
                                        </td>
                                    )}
                                    {visibleColumns.product && (
                                        <td className="py-4 px-4">
                                            <div className="max-w-xs overflow-hidden">
                                                <div className="text-sm font-medium text-gray-800 line-clamp-2 leading-snug" title={product.name || "Unknown product"}>
                                                    {product.name || "Unknown product"}
                                                </div>
                                            </div>
                                        </td>
                                    )}
                                    {visibleColumns.price && (
                                        <td className="py-4 px-4 whitespace-nowrap">
                                            <span className={`text-sm font-bold ${isLowestPrice ? 'text-green-600' : 'text-gray-900'}`}>
                                                {formatPrice(product.price)}
                                            </span>
                                        </td>
                                    )}
                                    {visibleColumns.discount && (
                                        <td className="py-4 px-4 whitespace-nowrap">
                                            {(product.discount || 0) > 0 ? (
                                                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                                                    product.discount >= 20 ? 'bg-accent-500 text-white' :
                                                    product.discount >= 10 ? 'bg-green-100 text-green-800' :
                                                    'bg-gray-100 text-gray-800'
                                                }`}>
                                                    {product.discount}% OFF
                                                </span>
                                            ) : (
                                                <span className="text-gray-400 text-sm">—</span>
                                            )}
                                        </td>
                                    )}
                                    {visibleColumns.rating && (
                                        <td className="py-4 px-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="flex">
                                                    {[...Array(5)].map((_, i) => (
                                                        <i key={i} className={`fas fa-star ${i < Math.round(product.rating || 0) ? 'text-yellow-400' : 'text-gray-200'}`}></i>
                                                    ))}
                                                </div>
                                                <span className="ml-2 text-xs text-gray-500 font-medium">
                                                    {((product.reviews || 0) > 0) ? `(${(product.reviews || 0).toLocaleString()})` : ""}
                                                </span>
                                            </div>
                                        </td>
                                    )}
                                    {visibleColumns.actions && (
                                        <td className="py-4 px-4 whitespace-nowrap text-right text-sm">
                                            <div className="flex space-x-2">
                                                <button 
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onSelect(product);
                                                    }}
                                                    className={`text-xs py-2 px-3 rounded-lg transition-all ${
                                                        isSelected 
                                                            ? 'bg-primary-500 text-white shadow-sm' 
                                                            : 'bg-primary-50 hover:bg-primary-100 text-primary-700 border border-primary-200'
                                                    }`}
                                                >
                                                    <i className="fas fa-chart-line mr-1.5"></i> Track
                                                </button>
                                                <a 
                                                    href={product.url} 
                                                    target="_blank" 
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="text-xs bg-gradient-to-r from-accent-500 to-accent-600 hover:from-accent-600 hover:to-accent-700 text-white py-2 px-3 rounded-lg transition-all shadow-sm hover:shadow"
                                                >
                                                    <i className="fas fa-external-link-alt mr-1.5"></i> Visit
                                                </a>
                                            </div>
                                        </td>
                                    )}
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
            
            {/* Help text */}
            <div className="text-xs text-gray-500 p-3 bg-gray-50 rounded-lg border border-gray-200 hidden sm:block">
                <i className="fas fa-info-circle mr-1 text-primary-500"></i>
                Click on a product row to see its price history and trend analysis. Click on column headers to change sorting.
            </div>
        </div>
    );
};
