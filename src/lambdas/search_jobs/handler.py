"""
Lambda function to search for jobs using Yutori Research API
"""
import json
import os
from shared.yutori_client import YutoriClient
from shared.dynamodb_utils import DynamoDBClient
from shared.models import Job, JobStatus


def lambda_handler(event, context):
    """
    Search for jobs using Yutori Research API
    
    Request body:
    {
        "query": "software engineer",
        "location": "San Francisco, CA",
        "max_results": 10
    }
    
    Returns:
    {
        "jobs": [...],
        "count": 10,
        "task_id": "..."
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        query = body.get('query')
        location = body.get('location', '')
        max_results = body.get('max_results', 20)
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'query is required'})
            }
        
        # Initialize clients
        yutori = YutoriClient()
        dynamodb = DynamoDBClient()
        
        # Build search query
        search_query = f"{query}"
        if location:
            search_query += f" in {location}"
        
        print(f"Searching for: {search_query}")
        
        # Call Yutori Research API
        result = yutori.search_jobs(
            query=search_query,
            location=location,
            max_results=max_results
        )
        
        print(f"Yutori response: {result}")
        
        # Parse and save jobs
        jobs = []
        if isinstance(result, list):
            job_list = result
        else:
            job_list = result.get('jobs', [])
            
        for job_data in job_list:
            job = Job(
                title=job_data.get('title', 'Untitled'),
                company=job_data.get('company', 'Unknown'),
                location=job_data.get('location', location),
                description=job_data.get('description', ''),
                url=job_data.get('url', ''),
                posted_date=job_data.get('posted_date'),
                salary_range=job_data.get('salary_range'),
                status=JobStatus.SAVED
            )
            
            # Save to DynamoDB
            dynamodb.save_job(job)
            jobs.append(job.to_dict())
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'jobs': jobs,
                'count': len(jobs),
                'message': 'Jobs retrieved successfully'
            })
        }
    
    except Exception as e:
        print(f"Error in search_jobs: {str(e)}")
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
                'message': 'Failed to search jobs'
            })
        }
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
