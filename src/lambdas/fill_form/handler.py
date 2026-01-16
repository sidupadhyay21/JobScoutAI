"""
Lambda function to fill job application form using Yutori Browsing API
"""
import json
import uuid
import base64
from datetime import datetime

from shared.yutori_client import YutoriClient
from shared.dynamodb_utils import DynamoDBClient
from shared.s3_utils import S3Client
from shared.models import FormFillTask, TaskStatus, JobStatus


def lambda_handler(event, context):
    """
    Fill job application form (stops before submit)
    
    Request body:
    {
        "job_id": "uuid",
        "application_url": "https://...",
        "form_data": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "cover_letter": "Dear Hiring Manager..."
        }
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        job_id = body.get('job_id')
        application_url = body.get('application_url')
        form_data = body.get('form_data', {})
        
        if not job_id or not application_url:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'job_id and application_url are required'})
            }
        
        # Initialize clients
        yutori_client = YutoriClient()
        db_client = DynamoDBClient()
        s3_client = S3Client()
        
        # Verify job exists
        job = db_client.get_job(job_id)
        if not job:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Job not found'})
            }
        
        # Create task
        task_id = str(uuid.uuid4())
        task = FormFillTask(
            task_id=task_id,
            job_id=job_id,
            application_url=application_url,
            status=TaskStatus.PENDING
        )
        db_client.create_task(task.to_dynamodb())
        
        # Update task to in-progress
        db_client.update_task_status(task_id, TaskStatus.IN_PROGRESS.value)
        
        # Fill form using Yutori Browsing API
        print(f"Filling form for job: {job['title']} at {application_url}")
        result = yutori_client.fill_application_form(
            application_url=application_url,
            form_data=form_data,
            stop_before_submit=True
        )
        
        # Process screenshots
        screenshot_keys = []
        for i, screenshot in enumerate(result.get('screenshots', [])):
            # Screenshot data is base64 encoded image
            if isinstance(screenshot, dict):
                image_data = base64.b64decode(screenshot.get('data', ''))
                step_name = screenshot.get('name', f'step_{i}')
            else:
                image_data = base64.b64decode(screenshot)
                step_name = f'step_{i}'
            
            s3_key = s3_client.upload_screenshot(
                image_data=image_data,
                task_id=task_id,
                step=step_name
            )
            screenshot_keys.append(s3_key)
        
        # Update task with results
        db_client.update_task_status(
            task_id=task_id,
            status=TaskStatus.COMPLETED.value,
            filled_fields=result.get('filled_fields', {})
        )
        
        # Update DynamoDB with screenshot keys
        from datetime import datetime
        db_client.tasks_table.update_item(
            Key={'task_id': task_id},
            UpdateExpression='SET screenshot_s3_keys = :keys',
            ExpressionAttributeValues={':keys': screenshot_keys}
        )
        
        # Update job status
        db_client.update_job_status(job_id, JobStatus.READY_TO_SUBMIT.value)
        
        # Generate presigned URLs for screenshots
        screenshot_urls = [
            s3_client.get_presigned_url(key) for key in screenshot_keys
        ]
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'task_id': task_id,
                'job_id': job_id,
                'status': 'completed',
                'filled_fields': result.get('filled_fields', {}),
                'screenshot_urls': screenshot_urls,
                'stopped_at': result.get('stopped_at', 'submit button'),
                'message': 'Form filled successfully. Ready for manual review before submission.'
            })
        }
    
    except Exception as e:
        print(f"Error in fill_form: {str(e)}")
        
        # Update task status to failed if task was created
        if 'task_id' in locals():
            db_client.update_task_status(
                task_id=task_id,
                status=TaskStatus.FAILED.value,
                error_message=str(e)
            )
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
