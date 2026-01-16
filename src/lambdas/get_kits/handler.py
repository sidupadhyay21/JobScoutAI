"""
Lambda function to get application kits
"""
import json

from shared.dynamodb_utils import DynamoDBClient
from shared.s3_utils import S3Client


def lambda_handler(event, context):
    """
    Get application kits
    
    Query parameters:
    - job_id: filter kits by job (optional)
    - kit_id: get specific kit (optional)
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        job_id = params.get('job_id')
        kit_id = params.get('kit_id')
        
        # Initialize clients
        db_client = DynamoDBClient()
        s3_client = S3Client()
        
        if kit_id:
            # Get specific kit
            kit = db_client.get_kit(kit_id)
            if not kit:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Kit not found'})
                }
            kits = [kit]
        elif job_id:
            # Get kits for specific job
            kits = db_client.get_kits_by_job(job_id)
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Either job_id or kit_id is required'})
            }
        
        # Add presigned URLs for cover letters
        for kit in kits:
            if kit.get('cover_letter_s3_key'):
                kit['cover_letter_url'] = s3_client.get_presigned_url(
                    kit['cover_letter_s3_key']
                )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'kits': kits,
                'count': len(kits)
            })
        }
    
    except Exception as e:
        print(f"Error in get_kits: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
