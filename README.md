# JobScoutAI 🎯

An intelligent Job Application Agent that automates job searching, generates tailored application materials, and fills out application forms using Yutori AI APIs and AWS infrastructure.

> **Demo Project**: Single-user system for personal job application automation

## ✨ Features

- **🔍 Smart Job Search**: Find relevant job postings using Yutori's Research API
- **📝 Tailored Application Kits**: Auto-generate customized cover letters and resume bullets
- **🤖 Form Auto-Fill**: Use browser automation to pre-fill application forms (stops before submit)
- **☁️ Cloud-Native**: Serverless AWS infrastructure (Lambda + DynamoDB + S3)

## 🏗 Architecture

```
API Gateway → Lambda Functions → Yutori APIs
                ↓
            DynamoDB (Jobs, Kits, Tasks)
                ↓
            S3 (Resumes, Cover Letters, Screenshots)
```

**6 Lambda Functions:**
1. `search_jobs` - POST /jobs/search - Find job postings via Yutori Research API
2. `generate_kit` - POST /kits/generate - Create cover letters and resume bullets
3. `fill_form` - POST /forms/fill - Automate form filling via Yutori Browsing API
4. `get_jobs` - GET /jobs - List saved jobs with filters
5. `get_kits` - GET /kits - List application kits with S3 presigned URLs
6. `upload_resume` - POST /resume/upload - Upload base64-encoded PDF resumes to S3

## 🚀 Setup & Deployment

### Prerequisites

- AWS CLI configured with credentials (`aws configure`)
- AWS SAM CLI installed (`brew install aws-sam-cli`)
- Python 3.11+
- Yutori API key from [yutori.com](https://yutori.com)

### Quick Start

1. **Configure AWS credentials**:
   ```bash
   aws configure
   # Enter your AWS Access Key ID and Secret Access Key
   # Region: us-west-2 (or your preferred region)
   ```

2. **Deploy to AWS**:
   ```bash
   sam build
   sam deploy --guided
   ```

   During deployment, you'll be prompted for:
   - **Stack Name**: `jobscoutai` (or your choice)
   - **AWS Region**: `us-west-2`
   - **YutoriApiKey**: Your Yutori API key
   - **Confirm changes**: `y`
   - **Allow IAM role creation**: `y`
   - **Function has no authentication**: `y` (6 times - this is for demo)
   - **Save to config**: `y`

3. **Get your API endpoint**:
   ```bash
   aws cloudformation describe-stacks --stack-name jobscoutai \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
     --output text
   ```

### Test Your Deployment

```bash
# Test endpoint (replace with your actual endpoint)
export API_URL="https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/prod"

# List jobs (should return empty initially)
curl -X GET "${API_URL}/jobs?limit=5"

# Search for jobs (calls Yutori API)
curl -X POST "${API_URL}/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"software engineer","location":"San Francisco","max_results":5}'
```

### Monitor & Debug

```bash
# View Lambda logs
sam logs --stack-name jobscoutai --tail

# View specific function logs
sam logs -n SearchJobsFunction --stack-name jobscoutai --tail

# Check DynamoDB tables
aws dynamodb scan --table-name JobScoutAI-Jobs --limit 5
```

### Redeploy After Changes

```bash
sam build && sam deploy
```

### Cleanup (Delete Everything)

```bash
# Empty S3 bucket first
aws s3 rm s3://$(aws cloudformation describe-stacks --stack-name jobscoutai \
  --query 'Stacks[0].Outputs[?OutputKey==`ArtifactsBucketName`].OutputValue' \
  --output text) --recursive

# Delete stack
sam delete --stack-name jobscoutai
```

## 🐛 Troubleshooting

### Lambda Import Errors
If you see `No module named 'shared'` errors, the shared modules didn't copy correctly. Run:
```bash
for dir in src/lambdas/*/; do cp -r src/shared "$dir"; done
sam build && sam deploy
```

### Yutori API Errors
- Verify your API key is correct
- Check Lambda logs: `sam logs -n SearchJobsFunction --tail`
- The API uses `https://api.yutori.com` endpoints

### DynamoDB Access Errors
- Ensure Lambda execution roles have DynamoDB permissions (auto-created by SAM)
- Verify table names match environment variables

### No Changes to Deploy
SAM caches builds. If code didn't change but needs redeployment:
```bash
rm -rf .aws-sam
sam build && sam deploy
```

## 📚 Development

### Local Testing

```bash
# Test Lambda function locally
sam local invoke SearchJobsFunction --event test_event.json

# Start local API
sam local start-api
# Then: curl http://localhost:3000/jobs
```

### Project Structure

```
JobScoutAI/
├── frontend/                # Web UI (HTML/CSS/JS)
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── config.js
│   └── README.md
├── src/
│   ├── shared/              # Shared utilities (copied to each Lambda)
│   │   ├── models.py        # Pydantic data models
│   │   ├── dynamodb_utils.py
│   │   ├── s3_utils.py
│   │   └── yutori_client.py
│   └── lambdas/
│       ├── search_jobs/     # Each Lambda has handler.py + requirements.txt
│       ├── generate_kit/    # Plus a copy of shared/ folder
│       ├── fill_form/
│       ├── get_jobs/
│       ├── get_kits/
│       └── upload_resume/
├── template.yaml            # SAM infrastructure definition
├── samconfig.toml          # SAM deployment config (auto-generated)
├── requirements.txt        # Dev dependencies
├── deploy.sh              # Deployment helper script
├── test_api.sh           # API testing script
└── README.md
```

### Adding New Endpoints

1. Create new Lambda function in `src/lambdas/your_function/`
2. Add handler.py and requirements.txt
3. Copy shared utilities: `cp -r src/shared src/lambdas/your_function/`
4. Add function definition in `template.yaml`
5. Build and deploy: `sam build && sam deploy`

**Quick Setup:**
1. Import REST API resource with your API Gateway endpoint
2. Create UI components (tables, forms, buttons)
3. Connect components to API calls
4. Enable CORS in API Gateway if needed

## 📊 API Reference

### Search Jobs
```http
POST /jobs/search
Content-Type: application/json

{
  "query": "software engineer",
  "location": "San Francisco",
  "max_results": 10
}
```

### Generate Application Kit
```http
POST /kits/generate
Content-Type: application/json

{
  "job_id": "job-123",
  "resume_s3_key": "resumes/resume.pdf",
  "user_context": "I have 5 years of Python experience..."
}
```

### Fill Form
```http
POST /forms/fill
Content-Type: application/json

{
  "job_id": "job-123",
  "application_url": "https://company.com/apply",
  "kit_id": "kit-456"
}
```

### Get Jobs
```http
GET /jobs?status=saved&limit=20&offset=0
```

### Get Application Kits
```http
GET /kits?job_id=job-123
```

### Upload Resume
```http
POST /resume/upload
Content-Type: application/json

{
  "filename": "resume.pdf",
  "content": "<base64_encoded_pdf_content>"
}
```

---

**Your Current API Endpoint:** 
```
https://l5uknlmwf3.execute-api.us-west-2.amazonaws.com/prod
```

**Resources:**
- [Yutori Documentation](https://docs.yutori.com/)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Retool Setup Guide](RETOOL_SETUP.md)

**Built with Yutori AI + AWS**
