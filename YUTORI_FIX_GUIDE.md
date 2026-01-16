# Fixing Yutori Integration - Quick Guide

## ✅ What's Already Done

1. **Endpoint Fixed**: Using correct `https://api.yutori.com`
2. **Authentication**: Using `X-API-Key` header (correct method)
3. **Shared Code Synced**: All Lambda functions have the updated yutori_client.py

## 🔧 What You Need To Do

### Step 1: Verify Your Yutori API Key

Your API key was entered during `sam deploy --guided`. To check if it's working:

```bash
# Get your current API key from Lambda environment
aws lambda get-function-configuration \
  --function-name jobscoutai-SearchJobsFunction-* \
  --query 'Environment.Variables.YUTORI_API_KEY' \
  --output text
```

**Test the API key manually:**
```bash
# Replace YOUR_API_KEY with your actual key
curl -X POST https://api.yutori.com/v1/research/tasks \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find software engineering jobs in San Francisco",
    "user_location": "San Francisco, CA, US"
  }'
```

If you get a `task_id` back, your key is valid! ✅

### Step 2: Rebuild and Deploy

```bash
# From project root
sam build
sam deploy
```

This will deploy the fixed Yutori integration to AWS.

### Step 3: Test Job Search

Once deployed, try searching in your frontend:
1. Go to http://localhost:8000
2. Enter "software engineer" 
3. Location: "San Francisco"
4. Click "Search Jobs"

### Step 4: Monitor Logs (if issues occur)

```bash
# Watch logs in real-time
sam logs -n SearchJobsFunction --stack-name jobscoutai --tail

# Or check CloudWatch
aws logs tail /aws/lambda/jobscoutai-SearchJobsFunction-* --follow
```

## 🐛 Common Issues & Fixes

### Issue: "Invalid API Key"
**Solution:** Update your Yutori API key:
```bash
sam deploy --parameter-overrides YutoriApiKey=your-new-api-key
```

### Issue: "Task timeout"
The Yutori Research API can take 10-60 seconds. Your Lambda timeout is set to 300s (5 min), which should be enough.

**Check current timeout:**
```bash
aws lambda get-function-configuration \
  --function-name jobscoutai-SearchJobsFunction-* \
  --query 'Timeout'
```

### Issue: Still getting old endpoint errors
**Solution:** Make sure you rebuilt and deployed:
```bash
./sync_shared.sh
sam build
sam deploy
```

## 📊 Expected Behavior

When job search works correctly:

1. **Frontend**: Shows loading spinner (10-60 seconds)
2. **Lambda logs**: 
   ```
   Searching for: software engineer in San Francisco
   Yutori response: {...}
   ```
3. **Frontend**: Displays job cards with real job data
4. **DynamoDB**: Jobs saved to `JobScoutAI-Jobs` table

## 🎯 Next Steps After Fix

Once Yutori is working:
1. ✅ Upload resume → ✅ Search jobs → ✅ Generate application kit
2. Test the full workflow end-to-end
3. Try different job searches
4. Generate application kits for selected jobs

## 🔑 Get Your Yutori API Key

If you need a new API key:
1. Go to https://yutori.com
2. Sign up or log in
3. Navigate to API settings
4. Copy your API key
5. Redeploy with new key:
   ```bash
   sam deploy --parameter-overrides YutoriApiKey=YOUR_NEW_KEY
   ```
