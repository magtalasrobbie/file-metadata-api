import json
import boto3
import urllib.parse
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# Initialize clients outside the handler for reuse across invocations.
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(
            record['s3']['object']['key']
        )

        file_size = record['s3']['object']['size']
        key_parts = key.split('/', 1)
        file_id = key_parts[0]
        file_name = key_parts[1] if len(key_parts) > 1 else key

        try:
            response = s3.head_object(Bucket=bucket, Key=key)
            content_type = response.get('ContentType', 'unknown')
        except ClientError as e:
            print(f"Error fetching S3 object metadata: {e}")
            content_type = 'unknown'

        uploaded_at = datetime.now(timezone.utc).isoformat()

        item = {
            'fileId': {'S': file_id},
            'fileName': {'S': file_name},
            'fileSize': {'N': str(file_size)},
            'fileType': {'S': content_type},
            'uploadedAt': {'S': uploaded_at},
            'bucketName': {'S': bucket},
            's3Key': {'S': key}
        }

        try:
            dynamodb.put_item(
                TableName=TABLE_NAME,
                Item=item
            )
            print(f"Metadata stored for file: {file_name}, ID: {file_id}")
        except ClientError as e:
            print(f"Error writing to DynamoDB: {e}")
            raise

    return {'statusCode': 200, 'body': 'Metadata extracted successfully'}