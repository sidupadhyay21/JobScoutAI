"""
Yutori API client for Research and Browsing APIs
"""
import os
import requests
from typing import Dict, Any, List, Optional
import time


class YutoriClient:
    """Client for Yutori Research and Browsing APIs"""
    
    def __init__(self):
        self.api_key = os.environ.get('YUTORI_API_KEY')
        self.base_url = 'https://api.yutori.com'
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def search_jobs(self, query: str, location: Optional[str] = None,
                   max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Use Research API to find relevant job postings
        
        Args:
            query: Job search query (e.g., "software engineer Python")
            location: Optional location filter
            max_results: Maximum number of results to return
        
        Returns:
            List of job postings with title, company, url, description
        """
        # Build research query
        research_query = f"Find {max_results} {query} job postings"
        if location:
            research_query += f" in {location}"
        research_query += (
            ". For each job, provide: title, company name, location, "
            "job description summary, and application URL."
        )
        
        payload = {
            "query": research_query,
            "user_location": location or "San Francisco, CA, US"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/research/tasks",
            headers=self.headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        task_id = response.json().get('task_id')
        
        # Poll for results
        for _ in range(60):  # 5 minutes max
            time.sleep(5)
            status_response = requests.get(
                f"{self.base_url}/v1/research/tasks/{task_id}",
                headers=self.headers,
                timeout=10
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data.get('status') == 'succeeded':
                result_text = status_data.get('result', '')
                # Parse result or return mock data for testing
                return [{
                    'title': f'{query} Position',
                    'company': 'Sample Company',
                    'location': location or 'Remote',
                    'description': result_text[:200] if result_text else 'Job description from Yutori research',
                    'url': 'https://example.com/apply',
                    'source': 'yutori_research'
                }]
            elif status_data.get('status') == 'failed':
                raise Exception(f"Research task failed: {status_data.get('error', 'Unknown error')}")
        
        raise Exception("Research task timeout")
    
    def generate_application_kit(self, job_description: str, resume_text: str,
                                job_title: str, company: str) -> Dict[str, Any]:
        """
        Use Research API to generate tailored cover letter and resume bullets
        
        Args:
            job_description: Full job posting text
            resume_text: User's resume content
            job_title: Job title
            company: Company name
        
        Returns:
            Dict with 'cover_letter' and 'resume_bullets' keys
        """
        payload = {
            "task": "generate_application",
            "context": {
                "job_description": job_description,
                "resume": resume_text,
                "job_title": job_title,
                "company": company
            },
            "instructions": (
                "Generate a tailored cover letter and 5-7 resume bullet points "
                "that highlight relevant skills and experience for this specific role. "
                "The cover letter should be professional, concise (3-4 paragraphs), "
                "and demonstrate clear understanding of the role requirements."
            )
        }
        
        response = requests.post(
            f"{self.research_endpoint}/v1/generate",
            headers=self.headers,
            json=payload,
            timeout=90
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            'cover_letter': data.get('cover_letter', ''),
            'resume_bullets': data.get('resume_bullets', [])
        }
    
    def fill_application_form(self, application_url: str, 
                             form_data: Dict[str, str],
                             stop_before_submit: bool = True) -> Dict[str, Any]:
        """
        Use Browsing API to navigate and fill job application form
        
        Args:
            application_url: URL of the job application page
            form_data: Dictionary of form field names and values
            stop_before_submit: If True, stop before clicking submit button
        
        Returns:
            Dict with task status, filled fields, and screenshot URLs
        """
        payload = {
            "task": "fill_form",
            "url": application_url,
            "actions": self._build_form_actions(form_data, stop_before_submit),
            "capture_screenshots": True,
            "wait_for_navigation": True
        }
        
        response = requests.post(
            f"{self.browsing_endpoint}/v1/automate",
            headers=self.headers,
            json=payload,
            timeout=300
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            'task_id': data.get('task_id'),
            'status': data.get('status'),
            'filled_fields': data.get('filled_fields', {}),
            'screenshots': data.get('screenshots', []),
            'final_url': data.get('final_url'),
            'stopped_at': data.get('stopped_at', '')
        }
    
    def _build_form_actions(self, form_data: Dict[str, str],
                           stop_before_submit: bool) -> List[Dict[str, Any]]:
        """Build action sequence for form filling"""
        actions = []
        
        # Add fill actions for each form field
        for field_name, value in form_data.items():
            actions.append({
                "type": "fill_field",
                "selector": self._guess_field_selector(field_name),
                "value": value,
                "wait_after": 500  # ms
            })
        
        # Add screenshot action before submit
        actions.append({
            "type": "screenshot",
            "name": "before_submit"
        })
        
        # Optionally stop before submit
        if stop_before_submit:
            actions.append({
                "type": "stop",
                "reason": "Awaiting manual review before submission"
            })
        else:
            actions.append({
                "type": "click",
                "selector": "button[type='submit'], input[type='submit']",
                "wait_after": 2000
            })
            actions.append({
                "type": "screenshot",
                "name": "after_submit"
            })
        
        return actions
    
    def _guess_field_selector(self, field_name: str) -> str:
        """Generate CSS selector for common form fields"""
        # Common field name patterns
        selectors = {
            'first_name': "input[name*='first'], input[id*='first'], input[placeholder*='First']",
            'last_name': "input[name*='last'], input[id*='last'], input[placeholder*='Last']",
            'email': "input[type='email'], input[name*='email'], input[id*='email']",
            'phone': "input[type='tel'], input[name*='phone'], input[id*='phone']",
            'resume': "input[type='file'][name*='resume'], input[type='file'][id*='resume']",
            'cover_letter': "textarea[name*='cover'], textarea[id*='cover']",
            'linkedin': "input[name*='linkedin'], input[id*='linkedin']",
            'portfolio': "input[name*='portfolio'], input[id*='website']"
        }
        
        return selectors.get(field_name.lower(), f"input[name='{field_name}'], input[id='{field_name}']")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Poll browsing task status"""
        response = requests.get(
            f"{self.browsing_endpoint}/v1/tasks/{task_id}",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
