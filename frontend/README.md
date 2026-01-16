# JobScoutAI Frontend

A simple, single-page web application for JobScoutAI - no external tools required!

## 🚀 Quick Start

### Option 1: Python HTTP Server (Recommended)

```bash
# Navigate to frontend directory
cd frontend

# Start server (Python 3)
python3 -m http.server 8000

# Or use Python 2
python -m SimpleHTTPServer 8000
```

Then open: http://localhost:8000

### Option 2: Node.js HTTP Server

```bash
# Install http-server globally (one time)
npm install -g http-server

# Start server
cd frontend
http-server -p 8000
```

### Option 3: VS Code Live Server

1. Install "Live Server" extension in VS Code
2. Right-click on `index.html`
3. Select "Open with Live Server"

## 📁 File Structure

```
frontend/
├── index.html      # Main HTML page
├── styles.css      # All styling
├── app.js          # JavaScript logic & API calls
├── config.js       # API endpoint configuration
└── README.md       # This file
```

## 🔧 Configuration

Edit `config.js` to change your API endpoint:

```javascript
const API_CONFIG = {
    BASE_URL: 'https://YOUR_API_ID.execute-api.us-west-2.amazonaws.com/prod'
};
```

## ✨ Features

1. **Resume Upload** 📄
   - Drag & drop PDF files
   - Max 5MB file size
   - Base64 encoding for S3 upload

2. **Job Search** 🔍
   - Search by keywords and location
   - Configurable result limits
   - Displays job cards with details

3. **Application Kit Generator** 📝
   - Select job from search results
   - Add your experience context
   - Generates tailored cover letters
   - Creates resume bullets

4. **Download & Save** 💾
   - Download cover letters as .txt
   - Copy resume bullets

## 🎨 Customization

### Change Colors

Edit `styles.css`:

```css
/* Primary color (currently purple) */
.btn-primary {
    background: #4F46E5;  /* Change this */
}

/* Success color (currently green) */
.btn-success {
    background: #10B981;  /* Change this */
}
```

### Change API Timeout

Edit `app.js` and add timeout to fetch calls:

```javascript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds

fetch(url, {
    ...options,
    signal: controller.signal
});
```

## 🐛 Troubleshooting

### CORS Errors

If you see CORS errors in browser console:

1. Check your API Gateway CORS settings (should be enabled in template.yaml)
2. Verify you're using the correct API endpoint
3. Try using `python3 -m http.server` instead of opening HTML directly

### API Not Responding

1. Check API endpoint in `config.js`
2. Test API with curl:
   ```bash
   curl https://YOUR_API.execute-api.us-west-2.amazonaws.com/prod/jobs?limit=1
   ```
3. Check CloudWatch logs for Lambda errors

### Resume Upload Fails

1. Ensure file is PDF and under 5MB
2. Check browser console for errors
3. Verify S3 bucket permissions in AWS

## 🚀 Deployment Options

### Deploy to S3 Static Website

```bash
# Create S3 bucket
aws s3 mb s3://jobscoutai-frontend

# Enable static website hosting
aws s3 website s3://jobscoutai-frontend --index-document index.html

# Upload files
aws s3 sync frontend/ s3://jobscoutai-frontend --acl public-read

# Access at: http://jobscoutai-frontend.s3-website-us-west-2.amazonaws.com
```

### Deploy to GitHub Pages

1. Create GitHub repo
2. Push frontend folder
3. Enable GitHub Pages in repo settings
4. Access at: `https://yourusername.github.io/jobscoutai`

### Deploy to Netlify (Free)

1. Create account at netlify.com
2. Drag & drop `frontend` folder
3. Auto-deploys with custom domain
4. Access at: `https://jobscoutai.netlify.app`

## 📱 Mobile Support

The frontend is fully responsive and works on:
- ✅ Desktop browsers (Chrome, Firefox, Safari, Edge)
- ✅ Mobile browsers (iOS Safari, Chrome Android)
- ✅ Tablets

## 🔐 Security Notes

- No authentication implemented (demo only)
- API endpoint is public
- Don't store sensitive data in frontend
- For production: Add API keys, authentication, rate limiting

## 📝 License

Same as main project (MIT)
