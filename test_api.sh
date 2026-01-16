#!/bin/bash

# Test script for JobScoutAI API
# Make sure to update API_ENDPOINT if it changes

API_ENDPOINT="https://l5uknlmwf3.execute-api.us-west-2.amazonaws.com/prod"

echo "🧪 Testing JobScoutAI API"
echo "=========================="
echo ""

# Test 1: Get Jobs (should be empty initially)
echo "1️⃣  Testing GET /jobs..."
curl -s -X GET "${API_ENDPOINT}/jobs?limit=5" | python3 -m json.tool
echo ""
echo ""

# Test 2: Search Jobs (requires Yutori API)
echo "2️⃣  Testing POST /jobs/search..."
echo "⚠️  Note: This will call Yutori API and may take a moment..."
curl -s -X POST "${API_ENDPOINT}/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "software engineer Python",
    "location": "San Francisco, CA",
    "max_results": 3
  }' | python3 -m json.tool
echo ""
echo ""

# Test 3: Upload Resume (base64 test)
echo "3️⃣  Testing POST /resume/upload..."
echo "Creating a test resume file..."
# Create a minimal PDF-like content (this is just for testing the upload)
TEST_CONTENT=$(echo "Test Resume Content" | base64)
curl -s -X POST "${API_ENDPOINT}/resume/upload" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_content\": \"${TEST_CONTENT}\",
    \"content_type\": \"application/pdf\"
  }" | python3 -m json.tool
echo ""
echo ""

echo "✅ Basic API tests complete!"
echo ""
echo "📋 Your API Endpoint: ${API_ENDPOINT}"
echo ""
echo "Next steps:"
echo "  1. Run a job search to populate the database"
echo "  2. Generate an application kit for a found job"
echo "  3. Fill out an application form"
echo ""
echo "For detailed testing, check the AWS Lambda logs:"
echo "  sam logs --stack-name jobscoutai --tail"
