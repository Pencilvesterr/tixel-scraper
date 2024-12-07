import json
from datetime import datetime

from s3 import S3
from tixel_api import TixelAPI, Category
from logger_config import setup_logger

logger = setup_logger('main')

def lambda_handler(event, context):
    city = "Sydney"
    all_data = {}
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    logger.info(f"Starting event collection for {city} at {timestamp}")
    
    try:
        # Create a single API instance to reuse the session
        api = TixelAPI()
        
        # Fetch events for all categories
        for category in Category:
            logger.info(f"Processing category: {category}")
            events = api.get_all_events_for_category(city, category)
            all_data[str(category)] = events
            logger.info(f"Completed {category}: {len(events)} events collected")

        # Upload to S3
        logger.info("Uploading data to S3")
        s3 = S3()
        
        # Save combined file
        combined_filename = f"events/{timestamp}/all_events.json"
        logger.info(f"Uploading combined events file to {combined_filename}")
        s3.upload_file(combined_filename, json.dumps(all_data).encode())

        total_events = sum(len(events) for events in all_data.values())
        logger.info(f"Successfully processed {len(all_data)} categories with {total_events} total events")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data successfully fetched and stored',
                'timestamp': timestamp,
                'categories_processed': len(all_data),
                'total_events': total_events
            })
        }

    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    lambda_handler(None, None)
