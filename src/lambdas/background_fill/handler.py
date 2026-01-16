"""
Background Lambda function to fill forms using TinyFish Web Agent API
"""
import json
import os
import requests
from typing import Dict, Any

from shared.dynamodb_utils import DynamoDBClient


def fill_form_with_tinyfish(job_url: str, application_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use TinyFish (Mino) API to fill job application form
    
    TinyFish API docs: https://docs.mino.ai/
    """
    api_key = os.environ.get('TINYFISH_API_KEY')
    
    if not api_key:
        raise ValueError("TINYFISH_API_KEY not configured")
    
    # Mino API endpoint (TinyFish rebranded to Mino)
    mino_url = "https://mino.ai/v1/automation/run"
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Create automation goal with instructions
    goal = f"""
Navigate to this job application page and fill out the form, then SUBMIT it.

Application URL: {job_url}

Fill in these details:
- Full Name: {application_data.get('full_name', 'Not provided')}
- Email: {application_data.get('email', 'Not provided')}
- Phone: {application_data.get('phone', 'Not provided')}

If there's a cover letter field, paste this:
{application_data.get('cover_letter', 'Not provided')}

If there's a resume upload field, note that resume URL is: {application_data.get('resume_url', 'Not provided')}

Additional information:
- LinkedIn: {application_data.get('linkedin', 'Not provided')}
- Portfolio: {application_data.get('portfolio', 'Not provided')}
- Years of Experience: {application_data.get('years_experience', 'Not provided')}

Instructions:
1. Navigate to the application page
2. Fill in all visible form fields with the appropriate data
3. Click the "Submit" or "Apply" button to submit the application
4. Wait for confirmation that the application was submitted
5. Return a JSON object with all fields you filled in the format: {{"field_name": "value_filled", "submitted": true}}
"""

    payload = {
        "url": job_url,
        "goal": goal,
        "browserProfile": "stealth",  # Use stealth mode to avoid bot detection
        "responseFormat": "json"
    }
    
    response = requests.post(mino_url, headers=headers, json=payload, timeout=320)
    response.raise_for_status()
    
    result = response.json()
    
    return {
        'session_id': result.get('sessionId'),
        'status': result.get('status'),
        'screenshot_url': result.get('screenshotUrl'),
        'filled_fields': result.get('resultJson', {}),
        'logs': result.get('logs', []),
        'message': 'Form filled and submitted successfully'
    }


def lambda_handler(event, context):
    """
    Background process to fill form using TinyFish
    """
    task_id = event.get('task_id')
    application_url = event.get('application_url')
    job_title = event.get('job_title', 'Job Application')
    company = event.get('company', 'Company')
    application_data = event.get('application_data')
    
    dynamodb = DynamoDBClient()
    
    try:
        # Update task status to processing
        dynamodb.update_task_status(task_id, 'processing')
        
        # Fill form using TinyFish
        result = fill_form_with_tinyfish(application_url, application_data)
        
        # Update task with success
        dynamodb.update_task_status(
            task_id=task_id,
            status='completed',
            filled_fields=result.get('filled_fields'),
            result={
                'session_id': result.get('session_id'),
                'screenshot_url': result.get('screenshot_url'),
                'message': result.get('message'),
                'job_title': job_title,
                'company': company,
                'application_url': application_url
            }
        )
        
        return {'statusCode': 200, 'body': json.dumps(result)}
        
    except Exception as e:
        print(f"Error in background_fill: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update task with failure
        dynamodb.update_task_status(
            task_id=task_id,
            status='failed',
            error_message=str(e)
        )
        
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
