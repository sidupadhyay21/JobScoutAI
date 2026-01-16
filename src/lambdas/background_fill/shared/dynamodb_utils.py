"""
DynamoDB utilities for CRUD operations
"""
import boto3
from boto3.dynamodb.conditions import Key
from typing import Dict, Any, List, Optional
import os


class DynamoDBClient:
    """DynamoDB client wrapper"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.jobs_table = self.dynamodb.Table(os.environ['JOBS_TABLE_NAME'])
        self.kits_table = self.dynamodb.Table(os.environ['KITS_TABLE_NAME'])
        self.tasks_table = self.dynamodb.Table(os.environ['TASKS_TABLE_NAME'])
    
    # Jobs table operations
    def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job entry"""
        self.jobs_table.put_item(Item=job_data)
        return job_data
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        response = self.jobs_table.get_item(Key={'job_id': job_id})
        return response.get('Item')
    
    def update_job_status(self, job_id: str, status: str) -> None:
        """Update job status"""
        self.jobs_table.update_item(
            Key={'job_id': job_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': int(datetime.now().timestamp())
            }
        )
    
    def list_jobs(self, user_id: str = "demo_user", limit: int = 50) -> List[Dict[str, Any]]:
        """List jobs for a user"""
        response = self.jobs_table.query(
            IndexName='user-created-index',
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        return response.get('Items', [])
    
    # Kits table operations
    def create_kit(self, kit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application kit"""
        self.kits_table.put_item(Item=kit_data)
        return kit_data
    
    def get_kit(self, kit_id: str) -> Optional[Dict[str, Any]]:
        """Get a kit by ID"""
        response = self.kits_table.get_item(Key={'kit_id': kit_id})
        return response.get('Item')
    
    def get_kits_by_job(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all kits for a job"""
        response = self.kits_table.query(
            IndexName='job-index',
            KeyConditionExpression=Key('job_id').eq(job_id)
        )
        return response.get('Items', [])
    
    # Tasks table operations
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new form fill task"""
        self.tasks_table.put_item(Item=task_data)
        return task_data
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID"""
        response = self.tasks_table.get_item(Key={'task_id': task_id})
        return response.get('Item')
    
    def update_task_status(self, task_id: str, status: str, 
                          filled_fields: Optional[Dict[str, str]] = None,
                          error_message: Optional[str] = None,
                          result: Optional[Dict[str, Any]] = None) -> None:
        """Update task status and fields"""
        from datetime import datetime
        
        update_expr = 'SET #status = :status, updated_at = :updated_at'
        expr_names = {'#status': 'status'}
        expr_values = {
            ':status': status,
            ':updated_at': int(datetime.now().timestamp())
        }
        
        if status in ['completed', 'failed']:
            update_expr += ', completed_at = :completed_at'
            expr_values[':completed_at'] = int(datetime.now().timestamp())
        
        if filled_fields:
            update_expr += ', filled_fields = :filled_fields'
            expr_values[':filled_fields'] = filled_fields
        
        if error_message:
            update_expr += ', error_message = :error_message'
            expr_values[':error_message'] = error_message
            
        if result:
            update_expr += ', #result = :result'
            expr_names['#result'] = 'result'  # Reserved keyword
            expr_values[':result'] = result
        
        self.tasks_table.update_item(
            Key={'task_id': task_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
    
    def get_tasks_by_job(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a job"""
        response = self.tasks_table.query(
            IndexName='job-status-index',
            KeyConditionExpression=Key('job_id').eq(job_id)
        )
        return response.get('Items', [])
