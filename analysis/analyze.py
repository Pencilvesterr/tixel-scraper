from database import Event, Ticket, get_db_session
from sqlalchemy import func, create_engine
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os

"""
This script performs basic analysis on the events and tickets data in the database.
It's designed to be used to test the data locally. Please use the jupyter notebook for real analysis.
"""

# Database connection settings
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'tixel')
DB_USER = os.getenv('DB_USER', 'tixel')
DB_PASS = os.getenv('DB_PASS', 'tixel')

def analyze_events():
    # Get both session and engine for different query types
    session = get_db_session()
    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        # Basic statistics
        total_events = session.query(Event).count()
        total_tickets = session.query(Ticket).count()
        print(f"Total events: {total_events}")
        print(f"Total tickets: {total_tickets}")
        
        # Load events into pandas for more complex analysis
        events_df = pd.read_sql("""
            SELECT 
                id,
                title,
                start_time,
                end_time,
                venue_name,
                venue_city,
                category,
                genre,
                is_festival,
                snapshot_timestamp
            FROM events
        """, engine)
        
        tickets_df = pd.read_sql("""
            SELECT 
                id,
                event_id,
                price,
                currency,
                ticket_type,
                snapshot_timestamp
            FROM tickets
        """, engine)
        
        print(f"\nLoaded {len(events_df)} events and {len(tickets_df)} tickets")
        
        # Events by category
        print("\nEvents by category:")
        print(events_df['category'].value_counts())
        
        # Events by city
        print("\nEvents by city:")
        print(events_df['venue_city'].value_counts().head())
        
        # Festival vs non-festival events
        print("\nFestival vs Non-Festival Events:")
        print(events_df['is_festival'].value_counts())
        
        # Average ticket prices by category
        price_stats = tickets_df.merge(
            events_df[['id', 'category']], 
            left_on='event_id', 
            right_on='id'
        ).groupby('category').agg({
            'price': ['mean', 'min', 'max', 'count']
        }).round(2)
        
        print("\nTicket price statistics by category:")
        print(price_stats)
        
        # Ticket types distribution
        print("\nTicket types distribution:")
        print(tickets_df['ticket_type'].value_counts().head())
        
        # Create visualizations
        plt.figure(figsize=(12, 6))
        
        # Price distribution by category
        plt.subplot(1, 2, 1)
        sns.boxplot(data=tickets_df.merge(
            events_df[['id', 'category']], 
            left_on='event_id', 
            right_on='id'
        ), x='category', y='price')
        plt.xticks(rotation=45)
        plt.title('Ticket Prices by Category')
        
        # Events by city
        plt.subplot(1, 2, 2)
        events_df['venue_city'].value_counts().head().plot(kind='bar')
        plt.title('Top Cities by Number of Events')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('event_analysis.png')
        print("\nCreated visualization: event_analysis.png")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    analyze_events()
