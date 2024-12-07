import json
from datetime import datetime
from database import Base, Event, Ticket, get_db_session
from sqlalchemy import create_engine
import os
import pathlib
import requests
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

def init_db():
    """Initialize the database tables"""
    # Database connection settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'tixel')
    DB_USER = os.getenv('DB_USER', 'tixel')
    DB_PASS = os.getenv('DB_PASS', 'tixel')

    # Create engine
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    # Drop all tables
    Base.metadata.drop_all(engine)
    
    # Recreate all tables
    Base.metadata.create_all(engine)
    
    return engine

def load_json_from_s3(bucket_url='https://tixel-data.s3.ap-southeast-2.amazonaws.com/events/'):
    """Load all JSON files from S3 bucket, caching them locally"""
    # Create data directory if it doesn't exist
    data_dir = pathlib.Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Parse bucket URL to get bucket name and region
    parsed_url = urlparse(bucket_url)
    bucket_name = parsed_url.netloc.split('.')[0]
    
    # Get list of files using S3 REST API
    list_url = f"https://{bucket_name}.s3.ap-southeast-2.amazonaws.com/?prefix=events/"
    try:
        response = requests.get(list_url)
        response.raise_for_status()
        # Parse XML response
        root = ElementTree.fromstring(response.content)
        # Find all Key elements (file paths)
        namespace = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
        files = [key.text for key in root.findall('.//s3:Key', namespace) 
                if key.text.endswith('.json') and key.text != 'events/index.json']
    except requests.RequestException as e:
        print(f"Error listing bucket contents: {e}")
        return []
    except ElementTree.ParseError as e:
        print(f"Error parsing bucket listing: {e}")
        return []
    
    all_events = []
    for file_path in files:
        # Get relative path from events/ directory
        relative_path = file_path.replace('events/', '', 1)
        
        # Local cache path
        local_path = data_dir / relative_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if we have a cached version
        json_data = None
        if local_path.exists():
            print(f"Loading {relative_path} from local cache...")
            try:
                with open(local_path, 'r') as f:
                    json_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading cached file {local_path}, will download fresh copy")
                json_data = None
        
        # Download from S3 if not cached or cache is invalid
        if json_data is None:
            print(f"Downloading {relative_path} from S3...")
            file_url = urljoin(bucket_url, relative_path)
            try:
                response = requests.get(file_url)
                response.raise_for_status()
                json_data = response.json()
                
                # Cache the file locally
                with open(local_path, 'w') as f:
                    json.dump(json_data, f, indent=2)
            except requests.RequestException as e:
                print(f"Error downloading {relative_path}: {e}")
                continue
        
        # Handle different JSON structures
        if isinstance(json_data, dict):
            # If it's a dict, events might be nested under category keys
            for category, events in json_data.items():
                if isinstance(events, list):
                    for event in events:
                        event['category'] = category  # Add category to event data
                        all_events.append(event)
        elif isinstance(json_data, list):
            all_events.extend(json_data)
    
    print(f"Loaded {len(all_events)} events")
    return all_events

def extract_venue_details(event_data):
    """Extract venue details from event data"""
    venue = {}
    # Try to get venue details from different possible locations in the JSON
    if 'venue' in event_data:
        venue = event_data['venue']
    elif 'cityTag' in event_data:
        venue = {
            'city': event_data['cityTag'].get('title'),
            'country': event_data.get('country')
        }
    return venue

def unix_to_datetime(timestamp):
    """Convert Unix timestamp to datetime"""
    if not timestamp:
        return None
    try:
        # Handle both string and integer timestamps
        if isinstance(timestamp, str):
            timestamp = int(timestamp)
        return datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError):
        return None

def process_event_data(event_data, snapshot_timestamp):
    """Process a single event's data and return Event and Ticket objects"""
    try:
        # Extract required fields
        event_id = event_data.get('id')
        title = event_data.get('title')
        starts_at = unix_to_datetime(event_data.get('startsAt'))
        ends_at = unix_to_datetime(event_data.get('endsAt'))
        
        if not all([event_id, title, starts_at, ends_at]):
            print(f"Missing required fields for event {event_id}")
            return None, []
        
        # Extract venue details
        venue = event_data.get('venue', {})
        venue_name = venue.get('title')
        venue_city = venue.get('city')
        venue_address = venue.get('streetAddress')
        
        # Extract category and genre
        category = event_data.get('categoryTag', {}).get('title')
        genre = event_data.get('genreTag', {}).get('title')
        
        # Create Event object
        event = Event(
            id=event_id,
            title=title,
            venue_name=venue_name,
            venue_city=venue_city,
            venue_address=venue_address,
            start_time=starts_at,
            end_time=ends_at,
            category=category,
            genre=genre,
            is_festival=event_data.get('isFestival', False),
            raw_data=event_data,
            snapshot_timestamp=snapshot_timestamp
        )
        
        # Extract tickets
        tickets = []
        available_tickets = event_data.get('tickets', {}).get('available', [])
        for ticket_data in available_tickets:
            ticket = Ticket(
                event_id=event_id,
                price=ticket_data.get('price'),
                currency=ticket_data.get('currency', 'AUD'),
                ticket_type=ticket_data.get('type'),
                quantity=ticket_data.get('quantity'),
                raw_data=ticket_data,
                snapshot_timestamp=snapshot_timestamp
            )
            tickets.append(ticket)
        
        return event, tickets
        
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return None, []

def populate_database():
    """Main function to populate the database"""
    # Initialize database
    engine = init_db()
    session = get_db_session()
    
    try:
        # Load data from S3
        print("Loading data from S3...")
        events = load_json_from_s3()
        print(f"Loaded {len(events)} events")
        
        # Process each event
        processed_count = 0
        error_count = 0
        for event_data in events:
            try:
                if not event_data.get('id'):
                    print("Skipping event without ID")
                    continue
                    
                snapshot_timestamp = datetime.now()
                event, tickets = process_event_data(event_data, snapshot_timestamp)
                
                # Skip events without required data
                if not event:
                    print(f"Skipping event {event_data.get('id')}: missing required data")
                    continue
                
                # Add event and tickets to session
                session.merge(event)
                for ticket in tickets:
                    session.merge(ticket)
                
                # Commit after each event to avoid memory issues
                session.commit()
                processed_count += 1
                if processed_count % 10 == 0:
                    print(f"Processed {processed_count} events")
                
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                error_count += 1
                session.rollback()
                continue
        
        print(f"Database population complete!")
        print(f"Successfully processed {processed_count} events")
        print(f"Failed to process {error_count} events")
        
    except Exception as e:
        print(f"Error populating database: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def test_s3_loading():
    """Test function to verify S3 loading functionality"""
    events = load_json_from_s3()
    print(f"\nSuccessfully loaded {len(events)} events")
    if events:
        print("\nSample event data:")
        print(json.dumps(events[0], indent=2))

if __name__ == "__main__":
    # Uncomment to run full database population
    populate_database()
    
    # Test S3 loading only
    # test_s3_loading()
