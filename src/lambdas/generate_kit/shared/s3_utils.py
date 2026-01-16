"""
S3 utilities for storing and retrieving artifacts
"""
import boto3
import os
from typing import Optional, Dict, Any
from datetime import datetime
import json


class S3Client:
    """S3 client wrapper for artifact storage"""
    
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bucket_name = os.environ['S3_BUCKET_NAME']
    
    def upload_resume(self, file_content: bytes, user_id: str = "demo_user", 
                     content_type: str = "application/pdf") -> str:
        """Upload resume to S3"""
        timestamp = int(datetime.now().timestamp())
        key = f"resumes/{user_id}/resume_{timestamp}.pdf"
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_content,
            ContentType=content_type,
            Metadata={
                'user_id': user_id,
                'uploaded_at': str(timestamp)
            }
        )
        
        return key
    
    def get_resume(self, s3_key: str) -> bytes:
        """Get resume from S3"""
        response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response['Body'].read()
    
    def upload_cover_letter(self, content: str, job_id: str, 
                           user_id: str = "demo_user") -> str:
        """Upload generated cover letter to S3"""
        timestamp = int(datetime.now().timestamp())
        key = f"cover-letters/{user_id}/{job_id}_{timestamp}.txt"
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='text/plain',
            Metadata={
                'user_id': user_id,
                'job_id': job_id,
                'created_at': str(timestamp)
            }
        )
        
        return key
    
    def get_cover_letter(self, s3_key: str) -> str:
        """Get cover letter from S3"""
        response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response['Body'].read().decode('utf-8')
    
    def upload_screenshot(self, image_data: bytes, task_id: str, 
                         step: str) -> str:
        """Upload screenshot from browser automation"""
        timestamp = int(datetime.now().timestamp())
        key = f"screenshots/{task_id}/{step}_{timestamp}.png"
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=image_data,
            ContentType='image/png',
            Metadata={
                'task_id': task_id,
                'step': step,
                'timestamp': str(timestamp)
            }
        )
        
        return key
    
    def upload_json_artifact(self, data: Dict[str, Any], artifact_type: str,
                            reference_id: str) -> str:
        """Upload JSON artifact (e.g., job search results, filled form data)"""
        timestamp = int(datetime.now().timestamp())
        key = f"artifacts/{artifact_type}/{reference_id}_{timestamp}.json"
        
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2).encode('utf-8'),
            ContentType='application/json',
            Metadata={
                'artifact_type': artifact_type,
                'reference_id': reference_id,
                'timestamp': str(timestamp)
            }
        )
        
        return key
    
    def get_presigned_url(self, s3_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for temporary access"""
        url = self.s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        return url
    
    def list_user_resumes(self, user_id: str = "demo_user") -> list:
        """List all resumes for a user"""
        prefix = f"resumes/{user_id}/"
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )
        
        return [obj['Key'] for obj in response.get('Contents', [])]
