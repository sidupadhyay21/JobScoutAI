// State management
const appState = {
    resumeS3Key: null,
    resumeFilename: null,
    selectedFile: null,
    selectedJob: null,
    searchResults: [],
    currentKit: null,
    lastSearchResponse: null
};

// DOM Elements
const elements = {
    resumeUpload: document.getElementById('resume-upload'),
    uploadButton: document.getElementById('upload-button'),
    uploadStatus: document.getElementById('upload-status'),
    uploadArea: document.getElementById('upload-area'),
    
    jobQuery: document.getElementById('job-query'),
    location: document.getElementById('location'),
    maxResults: document.getElementById('max-results'),
    searchButton: document.getElementById('search-button'),
    
    resultsSection: document.getElementById('results-section'),
    resultsCount: document.getElementById('results-count'),
    jobsContainer: document.getElementById('jobs-container'),
    
    kitSection: document.getElementById('kit-section'),
    selectedJobInfo: document.getElementById('selected-job-info'),
    userContext: document.getElementById('user-context'),
    generateKitButton: document.getElementById('generate-kit-button'),
    
    kitDisplaySection: document.getElementById('kit-display-section'),
    coverLetterDisplay: document.getElementById('cover-letter-display'),
    resumeBulletsDisplay: document.getElementById('resume-bullets-display'),
    downloadCoverLetter: document.getElementById('download-cover-letter'),
    
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingText: document.getElementById('loading-text')
};

// Utility Functions
function showLoading(message = 'Processing...') {
    elements.loadingText.textContent = message;
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

function showStatus(message, type = 'info') {
    elements.uploadStatus.textContent = message;
    elements.uploadStatus.className = `status-message ${type}`;
    elements.uploadStatus.style.display = 'block';
}

async function apiCall(endpoint, method = 'GET', body = null) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || data.message || 'API request failed');
    }
    
    return data;
}

// File Upload Handling
elements.resumeUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        handleFileSelect(file);
    }
});

// Drag and drop
elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.add('dragover');
});

elements.uploadArea.addEventListener('dragleave', () => {
    elements.uploadArea.classList.remove('dragover');
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type === 'application/pdf') {
        handleFileSelect(file);
    } else {
        showStatus('Please upload a PDF file', 'error');
    }
});

function handleFileSelect(file) {
    if (file.size > 5 * 1024 * 1024) {
        showStatus('File size must be less than 5MB', 'error');
        return;
    }
    
    appState.selectedFile = file;
    elements.uploadArea.querySelector('p').textContent = `Selected: ${file.name}`;
    elements.uploadButton.style.display = 'block';
    showStatus(`Ready to upload: ${file.name}`, 'info');
}

// Upload Resume
elements.uploadButton.addEventListener('click', async () => {
    if (!appState.selectedFile) return;
    
    elements.uploadButton.disabled = true;
    elements.uploadButton.textContent = 'Uploading...';
    showLoading('Uploading resume...');
    
    try {
        const reader = new FileReader();
        reader.onload = async (e) => {
            const base64 = e.target.result.split(',')[1];
            
            console.log('Uploading file:', appState.selectedFile.name, 'Size:', Math.round(base64.length / 1024), 'KB');
            
            const response = await apiCall(
                API_CONFIG.ENDPOINTS.UPLOAD_RESUME,
                'POST',
                {
                    filename: appState.selectedFile.name,
                    content: base64
                }
            );
            
            appState.resumeS3Key = response.s3_key;
            appState.resumeFilename = response.filename || appState.selectedFile.name;
            
            console.log('Upload successful:', response);
            showStatus(`✅ Resume uploaded successfully: ${appState.resumeFilename}`, 'success');
            elements.uploadButton.textContent = '✅ Uploaded';
            
            hideLoading();
        };
        
        reader.onerror = (error) => {
            console.error('FileReader error:', error);
            hideLoading();
            showStatus('❌ Failed to read file', 'error');
            elements.uploadButton.disabled = false;
            elements.uploadButton.textContent = 'Upload Resume';
        };
        
        reader.readAsDataURL(appState.selectedFile);
        
    } catch (error) {
        console.error('Upload error:', error);
        hideLoading();
        showStatus(`❌ Upload failed: ${error.message}`, 'error');
        elements.uploadButton.disabled = false;
        elements.uploadButton.textContent = 'Upload Resume';
    }
});

// Search Jobs
elements.searchButton.addEventListener('click', async () => {
    const query = elements.jobQuery.value.trim();
    const location = elements.location.value.trim();
    const maxResults = parseInt(elements.maxResults.value);
    
    if (!query) {
        alert('Please enter a job search query');
        return;
    }
    
    showLoading('Creating search task...');
    
    try {
        // Create async search task
        const response = await apiCall(
            API_CONFIG.ENDPOINTS.SEARCH_JOBS,
            'POST',
            {
                query,
                location,
                max_results: maxResults
            }
        );
        
        const taskId = response.task_id;
        console.log('Search task created:', taskId);
        
        // Start polling for results
        await pollTaskStatus(taskId, query, location);
        
    } catch (error) {
        hideLoading();
        alert(`Search failed: ${error.message}`);
    }
});

async function pollTaskStatus(taskId, query, location) {
    let attempts = 0;
    const maxAttempts = API_CONFIG.POLLING.MAX_ATTEMPTS;
    const interval = API_CONFIG.POLLING.INTERVAL;
    
    const poll = async () => {
        try {
            attempts++;
            
            // Update loading message with progress
            const elapsed = Math.floor((attempts * interval) / 1000);
            const loadingMessage = `Searching for ${query}... ${elapsed}s elapsed`;
            
            // Update the loading overlay text directly
            if (elements.loadingText) {
                elements.loadingText.textContent = loadingMessage;
            }
            
            console.log(`Polling attempt ${attempts}/${maxAttempts} for task ${taskId}`);
            
            // Check task status
            const taskResponse = await fetch(
                `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GET_TASK}/${taskId}`,
                {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            if (!taskResponse.ok) {
                throw new Error(`Failed to check task status: ${taskResponse.status}`);
            }
            
            const taskData = await taskResponse.json();
            
            console.log(`Task ${taskId} status:`, taskData.status, taskData);
            
            if (taskData.status === 'completed') {
                // Task completed - display results
                if (taskData.result && taskData.result.jobs) {
                    appState.searchResults = taskData.result.jobs;
                    appState.lastSearchResponse = {
                        jobs: taskData.result.jobs,
                        count: taskData.result.count
                    };
                    displayJobResults();
                    hideLoading();
                } else {
                    hideLoading();
                    alert('Search completed but no results found');
                }
                return;
            } else if (taskData.status === 'failed') {
                // Task failed
                hideLoading();
                alert(`Search failed: ${taskData.error_message || 'Unknown error'}`);
                return;
            } else if (taskData.status === 'processing' || taskData.status === 'pending') {
                // Still processing - continue polling
                if (attempts < maxAttempts) {
                    setTimeout(poll, interval);
                } else {
                    // Timeout
                    hideLoading();
                    alert(`Search is taking longer than expected (${elapsed}s). The task may still be processing. Task ID: ${taskId}`);
                }
            }
        } catch (error) {
            console.error('Polling error:', error);
            // Continue polling despite errors unless we've exceeded max attempts
            if (attempts < maxAttempts) {
                setTimeout(poll, interval);
            } else {
                hideLoading();
                alert(`Failed to check search status after ${attempts} attempts: ${error.message}`);
            }
        }
    };
    
    // Start polling
    poll();
}

function displayJobResults() {
    if (appState.searchResults.length === 0) {
        elements.resultsCount.textContent = 'No jobs found. Try different search criteria.';
        elements.jobsContainer.innerHTML = '';
        elements.resultsSection.style.display = 'block';
        return;
    }
    
    // Check if mock data
    const isMock = appState.lastSearchResponse?.mock === true;
    const mockNotice = isMock ? ' (Demo data - Yutori integration in progress)' : '';
    
    elements.resultsCount.textContent = `Found ${appState.searchResults.length} jobs${mockNotice}`;
    elements.jobsContainer.innerHTML = '';
    
    appState.searchResults.forEach((job) => {
        const jobCard = createJobCard(job);
        elements.jobsContainer.appendChild(jobCard);
    });
    
    elements.resultsSection.style.display = 'block';
}

function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.dataset.jobId = job.job_id;
    
    card.innerHTML = `
        <h3>${job.title || 'Untitled Position'}</h3>
        <div class="job-company">${job.company || 'Unknown Company'}</div>
        <div class="job-location">📍 ${job.location || 'Location not specified'}</div>
        <div class="job-meta">
            ${job.posted_date ? `<span>📅 Posted: ${job.posted_date}</span>` : ''}
            ${job.salary_range ? `<span>💰 ${job.salary_range}</span>` : ''}
        </div>
        ${job.url ? `<div class="job-link"><a href="${job.url}" target="_blank">View Job Posting →</a></div>` : ''}
    `;
    
    card.addEventListener('click', () => selectJob(job, card));
    
    return card;
}

function selectJob(job, cardElement) {
    // Remove previous selection
    document.querySelectorAll('.job-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Add selection
    cardElement.classList.add('selected');
    appState.selectedJob = job;
    
    // Show kit generation section
    elements.selectedJobInfo.innerHTML = `
        <h4>${job.title}</h4>
        <p>${job.company} • ${job.location}</p>
    `;
    elements.kitSection.style.display = 'block';
    
    // Scroll to kit section
    elements.kitSection.scrollIntoView({ behavior: 'smooth' });
}

// Generate Kit
elements.generateKitButton.addEventListener('click', async () => {
    if (!appState.selectedJob) {
        alert('Please select a job first');
        return;
    }
    
    if (!appState.resumeS3Key) {
        alert('Please upload your resume first');
        return;
    }
    
    showLoading('Generating application kit...');
    
    try {
        const response = await apiCall(
            API_CONFIG.ENDPOINTS.GENERATE_KIT,
            'POST',
            {
                job_id: appState.selectedJob.job_id,
                resume_s3_key: appState.resumeS3Key,
                user_context: elements.userContext.value
            }
        );
        
        appState.currentKit = response;
        displayKit(response);
        hideLoading();
        
        // Scroll to kit display
        elements.kitDisplaySection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        hideLoading();
        alert(`Kit generation failed: ${error.message}`);
    }
});

function displayKit(kit) {
    elements.coverLetterDisplay.value = kit.cover_letter || 'No cover letter generated';
    
    if (kit.resume_bullets && kit.resume_bullets.length > 0) {
        elements.resumeBulletsDisplay.value = kit.resume_bullets.join('\n\n');
    } else {
        elements.resumeBulletsDisplay.value = 'No resume bullets generated';
    }
    
    elements.kitDisplaySection.style.display = 'block';
}

// Download Cover Letter
elements.downloadCoverLetter.addEventListener('click', () => {
    const content = elements.coverLetterDisplay.value;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cover_letter_${appState.selectedJob?.company || 'job'}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Initialize
console.log('JobScoutAI Frontend initialized');
console.log('API Base URL:', API_CONFIG.BASE_URL);
