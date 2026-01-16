"""
Lambda function to generate application kit (cover letter + bullets)
"""
import json
import uuid

from shared.yutori_client import YutoriClient
from shared.dynamodb_utils import DynamoDBClient
from shared.s3_utils import S3Client
from shared.models import ApplicationKit, JobStatus


def lambda_handler(event, context):
    """
    Generate application kit for a job
    
    Request body:
    {
        "job_id": "uuid",
        "resume_s3_key": "resumes/demo_user/resume.pdf" (optional, uses latest if not provided)
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        job_id = body.get('job_id')
        resume_s3_key = body.get('resume_s3_key')
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'job_id is required'})
            }
        
        # Initialize clients
        yutori_client = YutoriClient()
        db_client = DynamoDBClient()
        s3_client = S3Client()
        
        # Get job details
        job = db_client.get_job(job_id)
        if not job:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Job not found'})
            }
        
        # Get resume
        if not resume_s3_key:
            # Get the latest resume
            resumes = s3_client.list_user_resumes()
            if not resumes:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'No resume found. Please upload a resume first.'})
                }
            resume_s3_key = sorted(resumes)[-1]  # Get most recent
        
        # Read resume (assuming PDF - in production, you'd extract text)
        resume_bytes = s3_client.get_resume(resume_s3_key)
        # For now, using placeholder. In production, use PDF parser
        resume_text = "[Resume content would be extracted here]"
        
        # Generate application kit
        print(f"Generating kit for job: {job['title']} at {job['company']}")
        kit_data = yutori_client.generate_application_kit(
            job_description=job['description'],
            resume_text=resume_text,
            job_title=job['title'],
            company=job['company']
        )
        
        # Store cover letter in S3
        cover_letter_s3_key = s3_client.upload_cover_letter(
            content=kit_data['cover_letter'],
            job_id=job_id
        )
        
        # Create kit record
        kit = ApplicationKit(
            kit_id=str(uuid.uuid4()),
            job_id=job_id,
            cover_letter=kit_data['cover_letter'],
            resume_bullets=kit_data['resume_bullets'],
            cover_letter_s3_key=cover_letter_s3_key
        )
        
        db_client.create_kit(kit.to_dynamodb())
        
        # Update job status
        db_client.update_job_status(job_id, JobStatus.KIT_GENERATED.value)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'kit_id': kit.kit_id,
                'job_id': job_id,
                'cover_letter': kit.cover_letter,
                'resume_bullets': kit.resume_bullets,
                'cover_letter_url': s3_client.get_presigned_url(cover_letter_s3_key)
            })
        }
    
    except Exception as e:
        print(f"Error in generate_kit: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
