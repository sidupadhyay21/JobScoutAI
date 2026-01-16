"""
Lambda function to fill job application forms using TinyFish Web Agent API
"""
import json
import os
import hashlib
from datetime import datetime
import boto3

from shared.dynamodb_utils import DynamoDBClient


def lambda_handler(event, context):
    """
    Fill job application form using TinyFish Web Agent
    
    Request body:
    {
        "job_id": "abc123",
        "application_data": {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "resume_url": "https://...",
            "cover_letter": "..."
        }
    }
    
    Returns task_id for async tracking
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        job_id = body.get('job_id')
        application_data = body.get('application_data', {})
        custom_url = body.get('application_url')  # Optional custom URL
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'job_id is required'})
            }
        
        # Get job details from DynamoDB (if not custom)
        dynamodb = DynamoDBClient()
        job = None
        application_url = custom_url
        
        if job_id != 'custom':
            job = dynamodb.get_job(job_id)
            
            if not job:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Job not found'})
                }
            
            # Use job URL if no custom URL provided
            if not application_url:
                application_url = job.get('url')
        
        # Create task for async processing
        task_id = hashlib.sha256(
            f"{job_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        task_data = {
            'task_id': task_id,
            'task_type': 'form_fill',
            'user_id': job.get('user_id', 'demo_user') if job else 'demo_user',
            'status': 'pending',
            'created_at': int(datetime.now().timestamp()),
            'updated_at': int(datetime.now().timestamp()),
            'job_id': job_id,
            'job_title': job.get('title') if job else 'Custom Application',
            'company': job.get('company') if job else 'Custom Company',
            'application_url': application_url
        }
        
        dynamodb.create_task(task_data)
        
        # Invoke background Lambda to fill form using TinyFish
        lambda_client = boto3.client('lambda')
        background_function = os.environ.get('BACKGROUND_FILL_FUNCTION')
        
        lambda_client.invoke(
            FunctionName=background_function,
            InvocationType='Event',
            Payload=json.dumps({
                'task_id': task_id,
                'application_url': application_url,
                'job_title': job.get('title') if job else 'Custom Application',
                'company': job.get('company') if job else 'Custom Company',
                'application_data': application_data
            })
        )
        
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'task_id': task_id,
                'message': 'Form filling started',
                'job_title': job.get('title') if job else 'Custom Application',
                'company': job.get('company') if job else 'Custom Company',
                'application_url': application_url
            })
        }
    
    except Exception as e:
        print(f"Error in fill_form: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
