// API Configuration
const API_CONFIG = {
    // Your AWS API Gateway endpoint
    BASE_URL: 'https://l5uknlmwf3.execute-api.us-west-2.amazonaws.com/prod',
    
    // API Endpoints
    ENDPOINTS: {
        UPLOAD_RESUME: '/resume/upload',
        SEARCH_JOBS: '/jobs/search',
        GET_TASK: '/tasks',  // /tasks/{task_id}
        GENERATE_KIT: '/kits/generate',
        GET_JOBS: '/jobs',
        GET_KITS: '/kits',
        FILL_FORM: '/forms/fill'
    },
    
    // Polling configuration
    POLLING: {
        INTERVAL: 3000,  // Poll every 3 seconds
        MAX_ATTEMPTS: 200  // Max 10 minutes (200 * 3s = 600s)
    }
};
