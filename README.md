# tixel-scraper
Web scrapper to collect data for tixel listings
# Potential TODO: 
- Use Github actions to deploy to lambda [link](https://aws.amazon.com/blogs/compute/using-github-actions-to-deploy-serverless-applications/)

# Running the repo
To run the script locally:
```
poetry run python main.py
```

To check all saved JSONs:
```
aws s3 ls s3://tixel-data/events/ --recursive --human-readable
```

To download a single file:
```
aws s3 cp s3://tixel-data/events/20230606/FOOD_AND_DRINK-tickets.json .
```

# General Notes 
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
