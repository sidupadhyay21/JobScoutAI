"""
Lambda function to get jobs list
"""
import json

from shared.dynamodb_utils import DynamoDBClient


def lambda_handler(event, context):
    """
    Get list of jobs for user
    
    Query parameters:
    - limit: max number of jobs to return (default: 50)
    - status: filter by status (optional)
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        limit = int(params.get('limit', 50))
        status_filter = params.get('status')
        
        # Initialize client
        db_client = DynamoDBClient()
        
        # Get jobs
        jobs = db_client.list_jobs(limit=limit)
        
        # Filter by status if requested
        if status_filter:
            jobs = [job for job in jobs if job.get('status') == status_filter]
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'jobs': jobs,
                'count': len(jobs)
            })
        }
    
    except Exception as e:
        print(f"Error in get_jobs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
