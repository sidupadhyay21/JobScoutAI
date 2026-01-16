# Retool Configuration Guide for JobScoutAI

This guide walks you through setting up a Retool frontend for JobScoutAI.

## Step 1: Create REST API Resource

1. Go to **Resources** in Retool
2. Click **Create New** → **REST API**
3. Configure:
   - **Name**: `JobScoutAI API`
   - **Base URL**: `https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/prod`
   - **Headers**: Leave empty (no auth required for demo)

## Step 2: Create Retool App

### Page 1: Job Search

**Components:**

1. **Search Form**
   - Text Input: `queryInput` (placeholder: "e.g., software engineer Python")
   - Text Input: `locationInput` (placeholder: "e.g., San Francisco, CA")
   - Number Input: `maxResultsInput` (default: 20)
   - Button: "Search Jobs"

2. **Query: searchJobs**
```javascript
// POST /jobs/search
{
  method: 'POST',
  url: '/jobs/search',
  body: {
    query: queryInput.value,
    location: locationInput.value,
    max_results: maxResultsInput.value
  }
}
```

3. **Jobs Table**
   - Data source: `searchJobs.data.jobs`
   - Columns: title, company, location, url
   - Action buttons: "Generate Kit", "View Details"

### Page 2: Application Kits

**Components:**

1. **Job Selector**
   - Select component: `jobSelect`
   - Options from: `getJobs.data.jobs`
   - Display: `{{item.title}} at {{item.company}}`

2. **Query: getJobs**
```javascript
// GET /jobs
{
  method: 'GET',
  url: '/jobs',
  params: {
    limit: 50
  }
}
```

3. **Query: generateKit**
```javascript
// POST /kits/generate
{
  method: 'POST',
  url: '/kits/generate',
  body: {
    job_id: jobSelect.value
  }
}
```

4. **Kit Display**
   - Text component: Show cover letter
   - List component: Show resume bullets
   - Button: "Download Cover Letter"

### Page 3: Form Filling

**Components:**

1. **Job Selector** (same as Page 2)

2. **Form Data Inputs**
   - Text Input: `firstNameInput`
   - Text Input: `lastNameInput`
   - Text Input: `emailInput`
   - Text Input: `phoneInput`
   - Text Area: `coverLetterInput` (pre-filled from kit)

3. **Query: fillForm**
```javascript
// POST /forms/fill
{
  method: 'POST',
  url: '/forms/fill',
  body: {
    job_id: jobSelect.value,
    application_url: applicationUrlInput.value,
    form_data: {
      first_name: firstNameInput.value,
      last_name: lastNameInput.value,
      email: emailInput.value,
      phone: phoneInput.value,
      cover_letter: coverLetterInput.value
    }
  }
}
```

4. **Screenshot Gallery**
   - Image components to display: `fillForm.data.screenshot_urls`
   - Status text: `fillForm.data.message`

### Page 4: Resume Manager

**Components:**

1. **File Upload**
   - File input: `resumeUpload`
   - Accepted: PDF only

2. **Query: uploadResume**
```javascript
// POST /resume/upload
{
  method: 'POST',
  url: '/resume/upload',
  body: {
    file_content: btoa(resumeUpload.files[0]),  // Base64 encode
    content_type: 'application/pdf'
  }
}
```

3. **Success Message**
   - Text: Show S3 key and presigned URL

## Step 3: Styling

Use Retool's built-in themes or customize:

- Primary color: `#4F46E5` (Indigo)
- Success color: `#10B981` (Green)
- Card backgrounds: `#FFFFFF`
- Spacing: 16px padding

## Step 4: Testing

1. Test job search with query "software engineer"
2. Select a job and generate kit
3. Fill form with test data (don't submit to real companies!)
4. Verify screenshots appear correctly

## Advanced Features

### Add Status Badges

```javascript
// In jobs table, add custom column
{{item.status === 'found' ? '🔍 Found' : 
  item.status === 'kit_generated' ? '✅ Kit Ready' : 
  item.status === 'ready_to_submit' ? '📝 Ready' : '❓'}}
```

### Add Filters

```javascript
// In getJobs query, add status filter
{
  params: {
    limit: 50,
    status: statusFilter.value  // Add a select component
  }
}
```

### Auto-refresh

Set queries to auto-refresh every 30 seconds for real-time updates.

## Troubleshooting

### CORS Errors
- Check API Gateway CORS settings in template.yaml
- Ensure allowed origins include Retool domain

### Authentication
- For demo, no auth is needed
- For production, add API key to headers:
  ```javascript
  headers: {
    'X-API-Key': '{{appSettings.apiKey}}'
  }
  ```

### Rate Limiting
- Add delays between requests if hitting Lambda concurrency limits
- Consider adding loading states for better UX

---

**Need help?** Check Retool docs at https://docs.retool.com
