from enum import Enum

from boto3.s3.transfer import S3Transfer

from s3 import S3


class Category(Enum):
    MUSIC = "music"
    FESTIVAL = "festival"
    SPORTS = "sports"
    THEATRE = "theatre"
    COMEDY = "comedy"
    FOOD_AND_DRINK = "food-and-drink"

    def __str__(self):
        return self.value + "-tickets"



"""
The main api we start from is the following. We can filter by category above with -tickets suffix
https://tixel.com/nuxt-api/kv/db-directory-pages/ALL?page=1&filter=music-tickets&country=AUS&limit=1000

TODO: I want events in a given timeframe. Need to see how to filter, because I can see this on their site e.g. 
https://tixel.com/au/discover/Sydney/music-tickets?page=1

There will either be an event page, or there'll be a list of events
If there's an event page, we'll scrape the event page
If there's a list of events, we'll scrape the list of events

https://tixel.com/au/music-tickets/noel-gallagher
This will return an HTML page
In this response, there's a growthbook link
  growthbook: {
                        apiHost: "https://cdn.growthbook.io",
                        clientKey: "sdk-TFN2oDOEu2ORjAL2"
                    },
We can then call this at https://cdn.growthbook.io/api/features/sdk-TFN2oDOEu2ORjAL2
"""

# https://tixel.com/au/discover/music-tickets
# https://tixel.com/au/discover/festival-tickets
# https://tixel.com/au/discover/sports-tickets
# https://tixel.com/au/discover/theatre-tickets
# https://tixel.com/au/discover/comedy-tickets
# https://tixel.com/au/discover/food-and-drink-tickets


""" 
Trying to get all music events this month in Sydney
https://tixel.com/nuxt-api/events-by-city/au/Sydney?category=music-tickets&dates=%7B%22named%22:%22this-month%22%7D&genres=&limit=100&availableOnly=false&page=1&sortBy=date&sortOrder=asc

After decoding the URL, we get: https://tixel.com/nuxt-api/events-by-city/au/Sydney?category=music-tickets&dates={"named":"this-month"}&genres=&limit=20&availableOnly=false&page=1&sortBy=date&sortOrder=asc
"""

import json
import requests
from datetime import datetime
from pydantic import BaseModel, create_model

endpoint_main = "https://tixel.com/nuxt-api/events-by-city/au/Sydney?category=music-tickets&dates=%7B%22named%22:%22this-month%22%7D&genres=&limit=100&availableOnly=false&page=1&sortBy=date&sortOrder=asc"

def lambda_handler(event, context):
    city = "Sydney"
    category = Category.MUSIC
    try:
        most_recent_events_data = _request_most_recent_events(city=city, category=category)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')


        s3 = S3()
        s3.upload_file(f"most_recent_events_{city}_{category}_{timestamp}.json", json.dumps(most_recent_events_data).encode())

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data successfully fetched and stored',
                'filename': "file_name"
            })
        }

    except requests.exceptions.RequestException as e:
        print(f"Error making HTTP request: {str(e)}")
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

def _request_most_recent_events(city: str, category: Category, limit: int = 100) -> dict:
    endpoint = f"https://tixel.com/nuxt-api/events-by-city/au/{city}?category={category}&dates=%7B%22named%22:%22this-month%22%7D&genres=&limit={limit}&availableOnly=false&page=1&sortBy=date&sortOrder=asc"
    response = requests.get(endpoint)
    response.raise_for_status()
    return response.json()



if __name__ == "__main__":
    lambda_handler(None, None)

