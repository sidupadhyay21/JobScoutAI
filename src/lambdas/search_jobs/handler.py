"""
Lambda function to search for jobs using Yutori Research API
"""
import json
import uuid
from datetime import datetime

from shared.yutori_client import YutoriClient
from shared.dynamodb_utils import DynamoDBClient
from shared.models import Job, JobStatus
from shared.s3_utils import S3Client


def lambda_handler(event, context):
    """
    Search for jobs and store results in DynamoDB
    
    Request body:
    {
        "query": "software engineer Python",
        "location": "San Francisco, CA",
        "max_results": 20
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        query = body.get('query')
        location = body.get('location')
        max_results = body.get('max_results', 20)
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'query parameter is required'})
            }
        
        # Initialize clients
        yutori_client = YutoriClient()
        db_client = DynamoDBClient()
        s3_client = S3Client()
        
        # Search for jobs
        print(f"Searching for jobs: {query} in {location}")
        job_results = yutori_client.search_jobs(
            query=query,
            location=location,
            max_results=max_results
        )
        
        # Store jobs in DynamoDB
        stored_jobs = []
        for job_data in job_results:
            job = Job(
                job_id=str(uuid.uuid4()),
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                location=job_data.get('location', location),
                description=job_data.get('description', ''),
                url=job_data.get('url', ''),
                source=job_data.get('source', 'unknown'),
                status=JobStatus.FOUND,
                metadata=job_data.get('metadata', {})
            )
            
            db_client.create_job(job.to_dynamodb())
            stored_jobs.append({
                'job_id': job.job_id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'url': job.url
            })
        
        # Store raw search results in S3 for audit
        s3_key = s3_client.upload_json_artifact(
            data={
                'query': query,
                'location': location,
                'timestamp': datetime.now().isoformat(),
                'results': job_results
            },
            artifact_type='job_search',
            reference_id=f"search_{int(datetime.now().timestamp())}"
        )
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': f'Found {len(stored_jobs)} jobs',
                'jobs': stored_jobs,
                'search_results_s3_key': s3_key
            })
        }
    
    except Exception as e:
        print(f"Error in search_jobs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
