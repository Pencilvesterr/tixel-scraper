# Tixel Scraper Lambda Function

This directory contains the AWS Lambda function code for scraping Tixel event data. 
It's setup to run every 6 hours using CloudWatch Events.
It will automatically stop running after 3 months.

## Files
- `main.py`: Main Lambda function handler
- `s3.py`: AWS S3 operations
- `tixel_api.py`: Tixel API operations

## Dependencies
Dependencies are managed with Poetry. To install locally (not required for deployment):
```bash
cd lambda
poetry install
```

## Testing locally
```bash
cd lambda
poetry run python main.py
```

## Deployment to AWS
Deploy the lambda function using terraform:
```bash
cd lambda
# Build the lambda function
./build.sh
# Deploy to AWS
terraform init
terraform apply --auto-approve
```

## Test the lambda function locally
```bash
aws lambda invoke --function-name tixel-scraper --payload {} response.json
```
You can then check the logs with:
```bash
aws lambda get-log-events --function-name tixel-scraper
```
