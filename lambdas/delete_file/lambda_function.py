import json
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')


TABLE_NAME = os.environ['TABLE_NAME']

def lambda_handler(event, context):
    path_parameters = event.get('pathParameters')
    if not path_parameters or not path_parameters.get('fileId'):
        return {
            'statusCode': 400,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'fileId is required'})
        }
    return delete_file(path_parameters['fileId'])

def delete_file(file_id):
    try:
        response = dynamodb.get_item(
            TableName=TABLE_NAME,
            Key={'fileId': {'S': file_id}}
        )
    except ClientError as e:
        print(f"Error fetching item: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Failed to retrieve file'})
        }
    
    item = response.get('Item')
    if not item:
        return {
            'statusCode': 404,
            'headers': cors_headers(),
            'body': json.dumps({'error': f'File {file_id} not found'})
        }

    try:
        response = dynamodb.delete_item(
            TableName=TABLE_NAME,
            Key={'fileId': {'S': file_id}}
        )
    except ClientError as e:
        print(f"Error deleting item: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Failed to delete file'})
        }
    
    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': json.dumps({'success': f'File {file_id} deleted'})
    }
    
def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'DELETE, OPTIONS'
    }