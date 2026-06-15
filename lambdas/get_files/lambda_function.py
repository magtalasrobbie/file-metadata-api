import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')
TABLE_NAME = 'file-metadata'


def lambda_handler(event, context):
    path_parameters = event.get('pathParameters')

    if path_parameters and path_parameters.get('fileId'):
        return get_file_by_id(path_parameters['fileId'])
    else:
        # No fileId — return all records.
        return get_all_files()


def get_file_by_id(file_id):
    try:
        response = dynamodb.get_item(
            TableName=TABLE_NAME,
            # get_item requires the full typed key format.
            Key={'fileId': {'S': file_id}}
        )
    except ClientError as e:
        print(f"Error fetching item: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Failed to retrieve file'})
        }

    # get_item returns an empty response if the key doesn't exist.
    # We check for 'Item' before trying to access it.
    item = response.get('Item')
    if not item:
        return {
            'statusCode': 404,
            'headers': cors_headers(),
            'body': json.dumps({'error': f'File {file_id} not found'})
        }

    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': json.dumps(deserialize_item(item))
    }


def get_all_files():
    try:
        response = dynamodb.scan(TableName=TABLE_NAME)
    except ClientError as e:
        print(f"Error scanning table: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Failed to retrieve files'})
        }

    items = [deserialize_item(item) for item in response.get('Items', [])]

    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': json.dumps({'files': items, 'count': len(items)})
    }


def deserialize_item(item):
    deserialized = {}
    for key, value in item.items():
        if 'S' in value:
            deserialized[key] = value['S']
        elif 'N' in value:
            deserialized[key] = int(value['N'])
        else:
            deserialized[key] = str(value)
    return deserialized


def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS'
    }