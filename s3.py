import boto3


class S3:
    def __init__(self, bucket_name: str = "tixel-data", region: str = "ap-southeast-2"):
        self.s3_client = boto3.client("s3", region_name=region)
        self.bucket_name = bucket_name
        self._create_bucket(bucket_name)

    def _create_bucket(self, bucket_name):
        response = self.s3_client.list_buckets()
        buckets = response["Buckets"]
        if bucket_name in [bucket["Name"] for bucket in buckets]:
            return

        location = {"LocationConstraint": "ap-southeast-2"}
        self.s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)

    def upload_file(self, file_name: str, data: bytes):
        self.s3_client.put_object(Bucket=self.bucket_name, Key=file_name, Body=data)

if __name__ == "__main__":
    s3 = S3()
    s3.upload_file("data.json", b'{"data": "test"}')
