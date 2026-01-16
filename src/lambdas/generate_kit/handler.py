"""
Lambda function to generate application kit (cover letter + resume bullets)
"""
import json
import hashlib
from datetime import datetime

from shared.models import ApplicationKit, Job
from shared.dynamodb_utils import DynamoDBClient


def lambda_handler(event, context):
    """
    Generate tailored application kit for a job
    
    Request body:
    {
        "job_id": "job_123",
        "resume_s3_key": "resumes/demo_user/resume.pdf",
        "user_context": "5 years Python experience, AWS expert..."
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        job_id = body.get('job_id')
        resume_s3_key = body.get('resume_s3_key')
        user_context = body.get('user_context', '')
        
        if not job_id or not resume_s3_key:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'job_id and resume_s3_key are required'})
            }
        
        # Get job details from DynamoDB
        dynamodb = DynamoDBClient()
        job_data = dynamodb.get_job(job_id)
        
        if not job_data:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Job not found'})
            }
        
        # For now, generate mock kit (Yutori integration would go here)
        # In production, this would call Yutori API with job description + resume
        cover_letter = generate_mock_cover_letter(
            job_data.get('title'),
            job_data.get('company'),
            user_context
        )
        
        resume_bullets = generate_mock_resume_bullets(
            job_data.get('title'),
            user_context
        )
        
        # Create kit ID
        kit_id = hashlib.sha256(
            f"{job_id}_{resume_s3_key}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Create ApplicationKit model
        kit = ApplicationKit(
            kit_id=kit_id,
            job_id=job_id,
            cover_letter=cover_letter,
            resume_bullets=resume_bullets
        )
        
        # Save to DynamoDB
        dynamodb.create_kit(kit.to_dynamodb())
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'kit_id': kit_id,
                'cover_letter': cover_letter,
                'resume_bullets': resume_bullets,
                'message': 'Application kit generated successfully'
            })
        }
    
    except Exception as e:
        print(f"Error in generate_kit: {str(e)}")
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


def generate_mock_cover_letter(job_title: str, company: str, user_context: str) -> str:
    """Generate a mock cover letter based on job and user context"""
    context_snippet = user_context[:100] if user_context else "my extensive background"
    
    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With {context_snippet}, I am confident in my ability to contribute effectively to your team.

Throughout my career, I have developed a comprehensive skill set that aligns well with the requirements of this role. My experience has equipped me with strong technical abilities, problem-solving skills, and a collaborative mindset that would make me a valuable addition to {company}.

I am particularly drawn to {company} because of its reputation for innovation and excellence in the industry. I am excited about the opportunity to bring my expertise to your team and contribute to your continued success.

Thank you for considering my application. I look forward to the opportunity to discuss how my background and skills would benefit {company}.

Sincerely,
[Your Name]"""


def generate_mock_resume_bullets(job_title: str, user_context: str) -> list:
    """Generate mock resume bullets tailored to the job"""
    return [
        f"• Led development of scalable solutions resulting in 40% improvement in system performance and reliability",
        f"• Collaborated with cross-functional teams to deliver high-impact projects aligned with {job_title} responsibilities",
        f"• Implemented best practices and modern technologies to enhance product quality and user experience",
        f"• Mentored junior team members and contributed to knowledge sharing initiatives",
        f"• Demonstrated strong problem-solving abilities in fast-paced, dynamic environments"
    ]
