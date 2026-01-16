"""
Background Lambda function to perform Yutori job search asynchronously
"""
import json
import hashlib
from datetime import datetime

from shared.yutori_client import YutoriClient
from shared.dynamodb_utils import DynamoDBClient
from shared.models import Job, JobStatus


def lambda_handler(event, context):
    """
    Execute Yutori job search and update task status
    
    Event:
    {
        "task_id": "...",
        "query": "software engineer",
        "location": "San Francisco, CA",
        "max_results": 10
    }
    """
    try:
        task_id = event.get('task_id')
        query = event.get('query')
        location = event.get('location', '')
        max_results = event.get('max_results', 20)
        
        print(f"Starting background search for task {task_id}: {query}")
        
        # Initialize clients
        dynamodb = DynamoDBClient()
        yutori = YutoriClient()
        
        # Update task status to processing
        dynamodb.update_task_status(task_id, 'processing')
        
        try:
            # Call Yutori Research API (this can take 10+ minutes)
            # For now, use mock data but structure is ready for real API
            print(f"Calling Yutori API for: {query} in {location}")
            
            # Real Yutori call (uncomment when ready):
            # yutori_jobs = yutori.search_jobs(query, location, max_results)
            
            # Mock data for testing (remove when Yutori is ready)
            mock_jobs_data = [
                {
                    'title': f'{query.title()} - Senior',
                    'company': 'TechCorp Inc',
                    'location': location or 'San Francisco, CA',
                    'description': f'We are looking for an experienced {query} to join our team. Must have 5+ years of experience.',
                    'url': 'https://example.com/job/1',
                    'posted_date': '2 days ago',
                    'salary_range': '$120k - $180k'
                },
                {
                    'title': f'{query.title()} - Mid Level',
                    'company': 'StartupXYZ',
                    'location': location or 'San Francisco, CA',
                    'description': f'Join our growing team as a {query}. Work on cutting-edge technology.',
                    'url': 'https://example.com/job/2',
                    'posted_date': '1 week ago',
                    'salary_range': '$100k - $150k'
                },
                {
                    'title': f'{query.title()}',
                    'company': 'BigTech Co',
                    'location': location or 'Remote',
                    'description': f'Remote {query} position with competitive salary and benefits.',
                    'url': 'https://example.com/job/3',
                    'posted_date': '3 days ago',
                    'salary_range': '$130k - $200k'
                }
            ]
            
            # Save jobs to DynamoDB
            jobs = []
            for job_data in mock_jobs_data[:max_results]:
                job = Job(
                    job_id=hashlib.sha256(f"{job_data['title']}_{job_data['company']}".encode()).hexdigest()[:16],
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    description=job_data['description'],
                    url=job_data['url'],
                    source='yutori_research',  # Will be real source when Yutori integrated
                    status=JobStatus.FOUND
                )
                
                # Save job to DynamoDB
                dynamodb.create_job(job.to_dynamodb())
                
                # Add to results
                job_dict = job.dict()
                job_dict['posted_date'] = job_data.get('posted_date')
                job_dict['salary_range'] = job_data.get('salary_range')
                jobs.append(job_dict)
            
            # Update task with results
            result_data = {
                'jobs': jobs,
                'count': len(jobs)
            }
            
            dynamodb.update_task_status(
                task_id,
                'completed',
                result=result_data
            )
            
            print(f"Task {task_id} completed with {len(jobs)} jobs")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'task_id': task_id,
                    'status': 'completed',
                    'jobs_found': len(jobs)
                })
            }
            
        except Exception as search_error:
            # Update task with error
            error_message = str(search_error)
            print(f"Search failed for task {task_id}: {error_message}")
            
            dynamodb.update_task_status(
                task_id,
                'failed',
                error_message=error_message
            )
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'task_id': task_id,
                    'status': 'failed',
                    'error': error_message
                })
            }
    
    except Exception as e:
        print(f"Error in background_search: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to update task status if possible
        if 'task_id' in locals():
            try:
                dynamodb = DynamoDBClient()
                dynamodb.update_task_status(task_id, 'failed', error_message=str(e))
            except:
                pass
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
