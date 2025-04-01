from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def start_scheduler(app):
    """
    Start a background scheduler to update prices periodically
    
    Args:
        app: Flask application instance
    """
    scheduler = BackgroundScheduler()
    
    def update_prices_job():
        """Job to update prices for all tracked products"""
        with app.app_context():
            logger.info("Running scheduled price update job")
            try:
                # We access the update_prices function directly instead of making an HTTP request
                # This avoids potential networking issues and is more efficient
                from app import update_prices
                result = update_prices()
                if result.status_code == 200:
                    logger.info("Scheduled price update completed successfully")
                else:
                    logger.error(f"Scheduled price update failed: {result.status_code}")
            except Exception as e:
                logger.error(f"Error running scheduled price update: {str(e)}")
    
    # Schedule the job to run every 12 hours
    scheduler.add_job(update_prices_job, 'interval', hours=12)
    
    # Start the scheduler
    scheduler.start()
    
    logger.info("Price update scheduler started")
    
    return scheduler
