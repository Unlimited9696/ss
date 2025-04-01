const ProductCard = ({ product, onSelect, isSelected, isBestDeal = false }) => {
    const [imageError, setImageError] = React.useState(false);
    const [isHovered, setIsHovered] = React.useState(false);
    
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

    // Calculate discounted percentages
    const discountPercent = product.discount || 0;
    
    // Handle image error
    const handleImageError = () => {
        setImageError(true);
    };
    
    // Get site logo and color based on source
    const getSiteInfo = (source) => {
        switch(source.toLowerCase()) {
            case 'amazon':
                return { 
                    icon: <i className="fab fa-amazon text-lg"></i>,
                    bgColor: "bg-orange-100", 
                    textColor: "text-orange-800",
                    borderColor: "border-orange-300",
                    gradientFrom: "from-orange-50",
                    gradientTo: "to-orange-100",
                    gradientAccent: "bg-gradient-to-r from-orange-500 to-amber-500",
                    name: "Amazon"
                };
            case 'meesho':
                return { 
                    icon: <i className="fas fa-store-alt text-lg"></i>,
                    bgColor: "bg-pink-100", 
                    textColor: "text-pink-800",
                    borderColor: "border-pink-300",
                    gradientFrom: "from-pink-50",
                    gradientTo: "to-pink-100",
                    gradientAccent: "bg-gradient-to-r from-pink-500 to-rose-500",
                    name: "Meesho"
                };
            default:
                return { 
                    icon: <i className="fas fa-store text-lg"></i>,
                    bgColor: "bg-gray-100", 
                    textColor: "text-gray-800",
                    borderColor: "border-gray-300",
                    gradientFrom: "from-gray-50",
                    gradientTo: "to-gray-100",
                    gradientAccent: "bg-gradient-to-r from-gray-500 to-gray-600",
                    name: source || "Store"
                };
        }
    };
    
    const siteInfo = getSiteInfo(product.source);

    return (
        <div 
            className={`bg-white rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300 ${
                isSelected ? 'ring-2 ring-primary-500 ring-offset-2' : ''
            } ${
                isBestDeal ? 'border-2 border-accent-500' : 'border border-gray-200'
            } relative transform hover:-translate-y-1`}
            onClick={() => onSelect(product)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
        >
            {/* Best Deal Badge */}
            {isBestDeal && (
                <div className="absolute -top-1 -right-1 z-10">
                    <div className="relative">
                        <div className="bg-gradient-to-r from-accent-500 to-accent-600 text-white font-bold py-1 px-3 rounded-bl-lg rounded-tr-lg shadow-md">
                            <i className="fas fa-trophy mr-1 text-accent-200"></i> BEST DEAL
                        </div>
                        <div className="absolute top-0 right-0 w-0 h-0 border-t-8 border-r-8 border-accent-800 transform translate-x-full"></div>
                    </div>
                </div>
            )}

            {/* Discount Badge */}
            {discountPercent > 0 && (
                <div className="absolute top-3 left-0 z-10">
                    <div className="bg-gradient-to-r from-green-600 to-green-500 text-white font-bold py-1 pl-2 pr-4 rounded-r-full shadow-md">
                        <span className="text-green-100">-</span>{discountPercent}<span className="text-green-100">%</span>
                    </div>
                </div>
            )}

            {/* Product Image */}
            <div className="relative pt-[75%] overflow-hidden bg-gradient-to-br from-gray-50 to-white">
                {imageError ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
                        <div className="text-center p-4">
                            <i className="fas fa-image text-gray-300 text-4xl mb-2"></i>
                            <p className="text-sm text-gray-500">Image unavailable</p>
                        </div>
                    </div>
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center p-4 transition-transform duration-300" 
                        style={{transform: isHovered ? 'scale(1.05)' : 'scale(1)'}}>
                        <img 
                            src={product.image_url} 
                            alt={product.name}
                            className="max-w-full max-h-full object-contain"
                            onError={handleImageError}
                        />
                    </div>
                )}
                
                {/* Product Source Badge */}
                <div className={`absolute top-3 right-3 ${siteInfo.gradientAccent} text-white rounded-full px-3 py-1 text-xs font-semibold flex items-center shadow-lg`}>
                    {siteInfo.icon}
                    <span className="ml-1">{siteInfo.name}</span>
                </div>
            </div>

            <div className="p-5">
                {/* Product Info */}
                <div className="flex flex-col h-full">
                    <div className="flex-grow">
                        {/* Product Name */}
                        <h3 className="mb-3 text-lg font-semibold text-gray-800 line-clamp-2 h-12 leading-tight" title={product.name}>
                            {product.name || "Unnamed Product"}
                        </h3>

                        {/* Ratings */}
                        <div className="flex items-center mb-4 bg-gray-50 rounded-lg p-2">
                            <div className="flex text-accent-500">
                                {[...Array(5)].map((_, i) => (
                                    <i key={i} className={`fas fa-star ${i < Math.round(product.rating || 0) ? 'text-yellow-400' : 'text-gray-200'} text-lg`}></i>
                                ))}
                            </div>
                            <span className="ml-2 text-sm text-gray-600 font-medium">
                                {(product.reviews || 0).toLocaleString()}
                            </span>
                        </div>
                    </div>

                    {/* Price Section */}
                    <div className="mt-2">
                        {discountPercent > 0 && (
                            <div className="flex items-center mb-2">
                                <span className="text-gray-500 line-through text-sm mr-2">
                                    {formatPrice(product.original_price)}
                                </span>
                                <span className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-0.5 rounded-full">
                                    Save {formatPrice(product.original_price - product.price)}
                                </span>
                            </div>
                        )}
                        
                        {/* Current Price */}
                        <div className="flex items-center">
                            <div className="text-2xl font-bold text-primary-700">
                                {formatPrice(product.price)}
                            </div>
                        </div>
                    </div>

                    {/* Visit Store Button */}
                    <div className="mt-4 flex space-x-3">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onSelect(product);
                            }}
                            className="flex-1 bg-white hover:bg-gray-50 text-primary-700 border border-primary-300 py-2.5 px-4 rounded-lg transition-colors text-sm font-medium shadow-sm hover:shadow"
                        >
                            <i className="fas fa-chart-line mr-2"></i> Track Price
                        </button>
                        <a 
                            href={product.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex-1 gradient-accent text-white py-2.5 px-4 rounded-lg transition-all duration-300 text-center text-sm font-medium shadow-md hover:shadow-lg flex items-center justify-center"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <i className="fas fa-external-link-alt mr-2"></i> Visit Store
                        </a>
                    </div>
                </div>
            </div>
            
            {/* Selection indicator */}
            {isSelected && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 via-secondary-500 to-accent-500"></div>
            )}
        </div>
    );
};
