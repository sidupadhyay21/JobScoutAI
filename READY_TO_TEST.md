# ✅ Yutori Integration Status - READY TO TEST

## Current Status: **DEPLOYED & READY** 🎉

All the Yutori integration fixes are now **deployed to AWS**. Here's what's ready:

### ✅ What's Fixed:
- ✅ Correct endpoint: `https://api.yutori.com`
- ✅ Proper authentication: `X-API-Key` header
- ✅ Code synced to all 6 Lambda functions
- ✅ Deployed to AWS (stack up to date)

### 📋 What You Need To Do:

## Step 1: Test in Your Frontend

1. **Open your browser**: http://localhost:8000
2. **Upload a resume** (if not already done)
3. **Search for jobs**:
   - Query: "software engineer"
   - Location: "San Francisco"
   - Max results: 5
4. **Click "Search Jobs"**
5. **Wait 10-60 seconds** (Yutori Research API needs time to process)

**Expected behavior:**
- Loading spinner appears
- After 10-60 seconds, job cards should appear
- If it takes longer, the Lambda might timeout (API Gateway has 30s limit)

## Step 2: If Search Times Out

The API Gateway has a **30-second timeout**, but Yutori can take longer. You have two options:

### Option A: Check Lambda Logs (Recommended)

Even if API Gateway times out, the Lambda keeps running and saves jobs to DynamoDB:

```bash
# Check if jobs were found and saved
aws dynamodb scan --table-name JobScoutAI-Jobs --limit 5
```

If you see jobs in DynamoDB, it worked! Just refresh your frontend and click "Get Jobs" button (if you add one).

### Option B: Increase API Gateway Timeout

This requires updating the template.yaml, but API Gateway max is only 29 seconds anyway. Better to handle async.

## Step 3: Make It Work Better (Async Pattern)

The current implementation is **synchronous** (waits for Yutori). For production, you'd want **async**:

1. Search endpoint returns immediately with `task_id`
2. Frontend polls a "get task status" endpoint
3. When ready, fetch results

But for testing, let's verify it works first!

## 🧪 Testing Commands

### Test 1: Direct API Call (with long timeout)
```bash
# This will wait up to 5 minutes
curl -X POST 'https://l5uknlmwf3.execute-api.us-west-2.amazonaws.com/prod/jobs/search' \
  -H "Content-Type: application/json" \
  -d '{"query":"software engineer","location":"San Francisco","max_results":2}' \
  --max-time 300
```

### Test 2: Check Lambda Logs
```bash
# Watch logs in real-time
aws logs tail /aws/lambda/jobscoutai-SearchJobsFunction-NdmCMB7PbDg6 --follow
```

### Test 3: Check DynamoDB
```bash
# See if jobs were saved
aws dynamodb scan --table-name JobScoutAI-Jobs --limit 5 --output table
```

### Test 4: Check Yutori API Key
```bash
# Get the API key from Lambda environment
aws lambda get-function-configuration \
  --function-name jobscoutai-SearchJobsFunction-NdmCMB7PbDg6 \
  --query 'Environment.Variables.YUTORI_API_KEY'
```

## 🔍 Debugging Guide

### Issue: "Endpoint request timed out"
**Cause:** API Gateway 30s limit, but Lambda keeps running  
**Solution:** Check DynamoDB for results, or make it async (see below)

### Issue: "Invalid API Key" in logs
**Cause:** Yutori API key is wrong or expired  
**Solution:** Update with correct key:
```bash
sam deploy --parameter-overrides YutoriApiKey=YOUR_NEW_KEY
```

### Issue: "Failed to resolve api.yutori.ai"
**Cause:** Old code still deployed  
**Solution:** Already fixed! You're on api.yutori.com now

### Issue: No results returned
**Cause:** Yutori might be slow or rate-limited  
**Solution:** Check logs, verify API key works with direct curl test

## 🚀 Quick Async Implementation (Optional)

If you want to fix the timeout issue properly, we can:

1. Make search endpoint return immediately with `task_id`
2. Add a new endpoint: `GET /jobs/tasks/{task_id}` to check status
3. Update frontend to poll for results

Let me know if you want me to implement this!

## 📊 Current Architecture

```
Frontend (browser)
    ↓ POST /jobs/search
API Gateway (30s timeout) → Lambda (300s timeout)
    ↓
Yutori Research API (10-60s to complete)
    ↓
DynamoDB (saves jobs)
```

**Problem:** API Gateway times out before Yutori finishes  
**Workaround:** Check DynamoDB directly for results

## ✅ Verification Checklist

- [ ] Frontend can upload resume ✅ (already working)
- [ ] Frontend can trigger job search ✅ (already working)
- [ ] Search request reaches Lambda ✅ (deployed)
- [ ] Lambda calls Yutori API ✅ (code is correct)
- [ ] Yutori API key is valid ❓ (need to verify)
- [ ] Results saved to DynamoDB ❓ (check after search)
- [ ] Frontend shows results ❓ (depends on timeout)

## 🎯 Next Steps

1. **Test in your browser** (http://localhost:8000)
2. **Try a search** (wait 30+ seconds)
3. **Check DynamoDB** for saved jobs
4. **Let me know** if you see errors in browser console

The integration is **ready**! The only question is whether your Yutori API key is valid and if we need to handle the async pattern better.

**Want me to help verify your API key or implement the async pattern?**
