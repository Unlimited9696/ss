const ProductSearch = ({ onSearch }) => {
    const [query, setQuery] = useState('');
    const [recentSearches, setRecentSearches] = useState([]);
    const [showRecentSearches, setShowRecentSearches] = useState(false);
    const [isInputFocused, setIsInputFocused] = useState(false);
    const inputRef = React.useRef(null);

    // Popular search suggestions
    const popularSearches = [
        "smartphone", "laptop", "headphones", "smartwatch", "camera"
    ];

    // Load recent searches from localStorage on component mount
    useEffect(() => {
        const savedSearches = localStorage.getItem('recentSearches');
        if (savedSearches) {
            setRecentSearches(JSON.parse(savedSearches));
        }
    }, []);

    // Save a new search to localStorage
    const saveSearch = (searchQuery) => {
        // Only save if not empty
        if (!searchQuery.trim()) return;
        
        const updatedSearches = [
            searchQuery,
            ...recentSearches.filter(s => s !== searchQuery)
        ].slice(0, 5); // Keep only the most recent 5 searches
        
        setRecentSearches(updatedSearches);
        localStorage.setItem('recentSearches', JSON.stringify(updatedSearches));
    };

    // Handle form submission
    const handleSubmit = (e) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query.trim());
            saveSearch(query.trim());
            setShowRecentSearches(false);
            setIsInputFocused(false);
            if (inputRef.current) {
                inputRef.current.blur();
            }
        }
    };

    // Handle clicking on a recent search
    const handleRecentSearchClick = (searchQuery) => {
        setQuery(searchQuery);
        onSearch(searchQuery);
        saveSearch(searchQuery);
        setShowRecentSearches(false);
        setIsInputFocused(false);
    };

    // Handle popular search click
    const handlePopularSearchClick = (searchQuery) => {
        setQuery(searchQuery);
        onSearch(searchQuery);
        saveSearch(searchQuery);
        setShowRecentSearches(false);
        setIsInputFocused(false);
    };

    return (
        <div className="relative w-full">
            <form onSubmit={handleSubmit} className="flex">
                <div className="relative flex-grow">
                    <div className={`relative flex items-center ${isInputFocused ? 'frosted-glass shadow-lg' : 'bg-white bg-opacity-20'} rounded-l-lg transition-all duration-300`}>
                        <i className="fas fa-search text-gray-300 absolute left-3"></i>
                        <input
                            ref={inputRef}
                            type="text"
                            placeholder="Search for products..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onFocus={() => {
                                setShowRecentSearches(true);
                                setIsInputFocused(true);
                            }}
                            onBlur={() => {
                                setTimeout(() => setShowRecentSearches(false), 200);
                                setIsInputFocused(false);
                            }}
                            className="w-full pl-10 pr-4 py-3 bg-transparent text-white placeholder-gray-300 rounded-l-lg focus:outline-none"
                        />
                    </div>
                    
                    {/* Recent and popular searches dropdown */}
                    {showRecentSearches && (
                        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg z-10 border border-gray-200 overflow-hidden">
                            {recentSearches.length > 0 && (
                                <div className="p-3">
                                    <h3 className="text-xs text-gray-500 font-semibold mb-2 px-2 flex items-center">
                                        <i className="fas fa-history text-gray-400 mr-2"></i>
                                        Recent Searches
                                    </h3>
                                    <ul className="space-y-1">
                                        {recentSearches.map((search, index) => (
                                            <li key={index}>
                                                <button
                                                    type="button"
                                                    onClick={() => handleRecentSearchClick(search)}
                                                    className="w-full text-left px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors flex items-center"
                                                >
                                                    <i className="fas fa-clock text-gray-400 mr-2 text-sm"></i>
                                                    <span className="line-clamp-1">{search}</span>
                                                </button>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            
                            <div className={`p-3 ${recentSearches.length > 0 ? 'border-t border-gray-200' : ''}`}>
                                <h3 className="text-xs text-gray-500 font-semibold mb-2 px-2 flex items-center">
                                    <i className="fas fa-fire text-gray-400 mr-2"></i>
                                    Popular Searches
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {popularSearches.map((search, index) => (
                                        <button
                                            key={index}
                                            type="button"
                                            onClick={() => handlePopularSearchClick(search)}
                                            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                                        >
                                            {search}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <button 
                    type="submit" 
                    className="gradient-accent text-white px-6 py-3 rounded-r-lg hover:shadow-md focus:outline-none focus:ring-2 focus:ring-accent-400 transition-all duration-300"
                >
                    <i className="fas fa-search"></i>
                </button>
            </form>
        </div>
    );
};
