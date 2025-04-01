# This file would normally contain database models
# Since we're using in-memory storage for this implementation,
# we're defining product data structures here instead

class Product:
    """
    Representation of a product with pricing information
    """
    def __init__(self, id, name, price, original_price, discount, rating, reviews, url, image_url, source):
        self.id = id
        self.name = name
        self.price = price
        self.original_price = original_price
        self.discount = discount
        self.rating = rating
        self.reviews = reviews
        self.url = url
        self.image_url = image_url
        self.source = source
    
    def to_dict(self):
        """Convert product to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'original_price': self.original_price,
            'discount': self.discount,
            'rating': self.rating,
            'reviews': self.reviews,
            'url': self.url,
            'image_url': self.image_url,
            'source': self.source
        }
