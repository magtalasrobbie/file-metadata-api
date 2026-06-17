import json
import boto3
import os
import uuid
from botocore.exceptions import ClientError

# Initialize the S3 client outside the handler.
s3 = boto3.client('s3')

BUCKET_NAME = os.environ['BUCKET_NAME']
URL_EXPIRATION = 300  # seconds — presigned URL expires in 5 minutes


def lambda_handler(event, context):
    # Parse the request body.
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }

    # Extract the original filename the user wants to upload.
    file_name = body.get('fileName')
    file_type = body.get('fileType')

    if not file_name or not file_type:
        return {
            'statusCode': 400,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'fileName and fileType are required'})
        }

    # Generate a unique ID for this file.
    file_id = str(uuid.uuid4())
    s3_key = f"{file_id}/{file_name}"

    try:
        # Generate a presigned URL for a PUT operation.
        # This creates a temporary URL that allows the client to upload
        # directly to S3 without going through Lambda.
        presigned_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': s3_key,
                'ContentType': file_type
            },
            ExpiresIn=URL_EXPIRATION
        )
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Failed to generate upload URL'})
        }

    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': json.dumps({
            'uploadUrl': presigned_url,
            'fileId': file_id,
            's3Key': s3_key
        })
    }


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
    }