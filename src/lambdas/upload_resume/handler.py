"""
Lambda function to upload resume
"""
import json
import base64

from shared.s3_utils import S3Client


def lambda_handler(event, context):
    """
    Upload resume to S3
    
    Request body:
    {
        "file_content": "base64_encoded_pdf",
        "content_type": "application/pdf"
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        file_content_b64 = body.get('file_content')
        content_type = body.get('content_type', 'application/pdf')
        
        if not file_content_b64:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'file_content is required'})
            }
        
        # Decode base64
        file_content = base64.b64decode(file_content_b64)
        
        # Initialize S3 client
        s3_client = S3Client()
        
        # Upload resume
        s3_key = s3_client.upload_resume(
            file_content=file_content,
            content_type=content_type
        )
        
        # Generate presigned URL
        url = s3_client.get_presigned_url(s3_key)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                's3_key': s3_key,
                'url': url,
                'message': 'Resume uploaded successfully'
            })
        }
    
    except Exception as e:
        print(f"Error in upload_resume: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
