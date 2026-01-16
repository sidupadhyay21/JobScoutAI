"""
Lambda function to search for jobs using Yutori Research API (async pattern)
"""
import json
import os
import hashlib
from datetime import datetime
import boto3

from shared.dynamodb_utils import DynamoDBClient


def lambda_handler(event, context):
    """
    Create async search task and trigger background processing
    
    Request body:
    {
        "query": "software engineer",
        "location": "San Francisco, CA",
        "max_results": 10
    }
    
    Returns immediately with task_id:
    {
        "task_id": "...",
        "status": "pending",
        "message": "Search task created"
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        query = body.get('query')
        location = body.get('location', '')
        max_results = body.get('max_results', 20)
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'query is required'})
            }
        
        # Create task ID
        task_id = hashlib.sha256(
            f"search_{query}_{location}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Initialize DynamoDB client
        dynamodb = DynamoDBClient()
        
        # Create task in DynamoDB
        task_data = {
            'task_id': task_id,
            'task_type': 'job_search',
            'user_id': 'demo_user',
            'status': 'pending',
            'query': query,
            'location': location,
            'max_results': max_results,
            'created_at': int(datetime.now().timestamp()),
            'updated_at': int(datetime.now().timestamp())
        }
        dynamodb.create_task(task_data)
        
        # Invoke background Lambda asynchronously
        lambda_client = boto3.client('lambda')
        lambda_client.invoke(
            FunctionName=os.environ.get('BACKGROUND_SEARCH_FUNCTION'),
            InvocationType='Event',  # Async invocation
            Payload=json.dumps({
                'task_id': task_id,
                'query': query,
                'location': location,
                'max_results': max_results
            })
        )
        
        print(f"Created search task {task_id} for query: {query}")
        
        return {
            'statusCode': 202,  # Accepted
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'task_id': task_id,
                'status': 'pending',
                'message': 'Search task created. Poll /tasks/{task_id} for results.'
            })
        }
    
    except Exception as e:
        print(f"Error in search_jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to create search task'
            })
        }
