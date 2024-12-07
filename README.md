# Tixel Scraper

A project for scraping and analyzing Tixel event data. The system collects event and ticket data from Tixel, stores it in S3, and provides tools for analysis using PostgreSQL and Jupyter notebooks.

## Project Structure
- `/lambda`: AWS Lambda function for scraping Tixel data
- `/analysis`: Jupyter notebooks and analysis tools for processing event data

## Setup

### Prerequisites
1. [Docker and Docker Compose](https://docs.docker.com/get-docker/)
2. Python 3.12
3. [Poetry](https://python-poetry.org/docs/)
4. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (Only if running the scraper locally)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tixel-scraper.git
cd tixel-scraper
```
2. Optional (for locally running the scrapper):
```bash
cd lambda
poetry install
```

## Running the Data Analysis Environment

1. Start the PostgreSQL database and Jupyter notebook server:
```bash
# From the root directory
docker compose up -d
```

2. Access Jupyter at http://localhost:9999 (no authentication required)

For more details on the analysis tools and notebooks, see `/analysis/README.md`.

## (Optional) API Scrapping
To run the scraper locally (only works on my machine due to AWS credentials):
```bash
cd lambda
poetry run python main.py
```

To check collected data in S3:
```bash
aws s3 ls s3://tixel-data/events/ --recursive --human-readable
```

To download a specific event file:
```bash
aws s3 cp s3://tixel-data/events/[DATE]/all-tickets.json .
```


