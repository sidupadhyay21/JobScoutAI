"""
Lambda function to get task status and results
"""
import json
from decimal import Decimal

from shared.dynamodb_utils import DynamoDBClient


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Get task status and results
    
    Path parameter: task_id
    
    Returns:
    {
        "task_id": "...",
        "status": "pending|processing|completed|failed",
        "result": {...},  // if completed
        "error_message": "...",  // if failed
        "created_at": 123456789,
        "updated_at": 123456789
    }
    """
    try:
        # Get task_id from path parameters
        task_id = event.get('pathParameters', {}).get('task_id')
        
        if not task_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'task_id is required'})
            }
        
        # Get task from DynamoDB
        dynamodb = DynamoDBClient()
        task = dynamodb.get_task(task_id)
        
        if not task:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Task not found'})
            }
        
        # Return task data
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(task, cls=DecimalEncoder)
        }
    
    except Exception as e:
        print(f"Error in get_task: {str(e)}")
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
                'message': 'Failed to get task status'
            })
        }
