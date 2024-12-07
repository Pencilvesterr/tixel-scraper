import boto3
from logger_config import setup_logger

logger = setup_logger('s3')

class S3:
    def __init__(self, bucket_name: str = "tixel-data", region: str = "ap-southeast-2"):
        self.logger = logger.getChild('S3')
        self.s3_client = boto3.client("s3", region_name=region)
        self.bucket_name = bucket_name
        self.logger.info(f"Initializing S3 client for bucket '{bucket_name}' in region '{region}'")
        self._create_bucket(bucket_name)

    def _create_bucket(self, bucket_name):
        self.logger.debug("Checking if bucket exists")
        response = self.s3_client.list_buckets()
        buckets = response["Buckets"]
        if bucket_name in [bucket["Name"] for bucket in buckets]:
            self.logger.debug(f"Bucket '{bucket_name}' already exists")
            return

        self.logger.info(f"Creating bucket '{bucket_name}'")
        location = {"LocationConstraint": "ap-southeast-2"}
        try:
            self.s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
            self.logger.info(f"Successfully created bucket '{bucket_name}'")
        except Exception as e:
            self.logger.error(f"Failed to create bucket '{bucket_name}': {str(e)}", exc_info=True)
            raise

    def upload_file(self, file_name: str, data: bytes):
        self.logger.info(f"Uploading {len(data)} bytes to '{file_name}'")
        try:
            self.s3_client.put_object(Bucket=self.bucket_name, Key=file_name, Body=data)
            self.logger.debug(f"Successfully uploaded '{file_name}'")
        except Exception as e:
            self.logger.error(f"Failed to upload '{file_name}': {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    s3 = S3()
    s3.upload_file("data.json", b'{"data": "test"}')
