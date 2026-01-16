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
    fillFormButton: document.getElementById('fill-form-button'),
    
    customUrlSection: document.getElementById('custom-url-section'),
    customUrl: document.getElementById('custom-url'),
    fillCustomUrlButton: document.getElementById('fill-custom-url-button'),
    
    formFillSection: document.getElementById('form-fill-section'),
    formFillStatus: document.getElementById('form-fill-status'),
    formFillResult: document.getElementById('form-fill-result'),
    screenshotContainer: document.getElementById('screenshot-container'),
    filledFieldsContainer: document.getElementById('filled-fields-container'),
    
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

// Fill Application Form with TinyFish
elements.fillFormButton.addEventListener('click', async () => {
    if (!appState.selectedJob) {
        alert('Please select a job first');
        return;
    }
    
    if (!appState.currentKit) {
        alert('Please generate an application kit first');
        return;
    }
    
    await fillFormWithTinyFish(appState.selectedJob.url, appState.selectedJob.job_id);
});

// Fill Custom URL Form
elements.fillCustomUrlButton.addEventListener('click', async () => {
    const customUrl = elements.customUrl.value.trim();
    
    if (!customUrl) {
        alert('Please enter a URL');
        return;
    }
    
    if (!customUrl.startsWith('http://') && !customUrl.startsWith('https://')) {
        alert('Please enter a valid URL (starting with http:// or https://)');
        return;
    }
    
    await fillFormWithTinyFish(customUrl, 'custom');
});

async function fillFormWithTinyFish(applicationUrl, jobId) {
    showLoading('Starting form filling with TinyFish...');
    
    try {
        // Prepare application data from current state
        const applicationData = {
            full_name: 'John Doe',  // TODO: Get from user profile
            email: 'john@example.com',  // TODO: Get from user profile
            phone: '+1234567890',  // TODO: Get from user profile
            resume_url: appState.resumeS3Key ? `https://s3.amazonaws.com/bucket/${appState.resumeS3Key}` : '',
            cover_letter: elements.coverLetterDisplay.value || 'Cover letter not generated yet',
            linkedin: '',  // TODO: Add input field
            portfolio: '',  // TODO: Add input field
            years_experience: '5'  // TODO: Add input field
        };
        
        const response = await apiCall(
            API_CONFIG.ENDPOINTS.FILL_FORM,
            'POST',
            {
                job_id: jobId,
                application_url: applicationUrl,
                application_data: applicationData
            }
        );
        
        // Start polling for form fill completion
        const taskId = response.task_id;
        showLoading(`Filling form... Task ID: ${taskId}`);
        
        await pollFormFillTask(taskId);
        
    } catch (error) {
        hideLoading();
        alert(`Form filling failed: ${error.message}`);
    }
}

async function pollFormFillTask(taskId) {
    let attempts = 0;
    const startTime = Date.now();
    
    const pollInterval = setInterval(async () => {
        attempts++;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        
        elements.loadingText.textContent = `Filling form with TinyFish... ${elapsed}s elapsed`;
        console.log(`[Form Fill Poll ${attempts}] Checking task ${taskId}...`);
        
        try {
            const taskResponse = await fetch(
                `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.GET_TASK}/${taskId}`
            );
            
            if (!taskResponse.ok) {
                throw new Error(`Failed to check task status: ${taskResponse.status}`);
            }
            
            const task = await taskResponse.json();
            console.log(`[Form Fill Poll ${attempts}] Task status:`, task.status);
            
            if (task.status === 'completed') {
                clearInterval(pollInterval);
                hideLoading();
                displayFormFillResult(task.result);
                elements.formFillSection.scrollIntoView({ behavior: 'smooth' });
            } else if (task.status === 'failed') {
                clearInterval(pollInterval);
                hideLoading();
                alert(`Form filling failed: ${task.error_message || 'Unknown error'}`);
            } else if (attempts >= API_CONFIG.POLLING.MAX_ATTEMPTS) {
                clearInterval(pollInterval);
                hideLoading();
                alert(`Form filling timed out after ${elapsed} seconds. Task ID: ${taskId}`);
            }
            
        } catch (error) {
            console.error(`[Form Fill Poll ${attempts}] Error:`, error);
            // Continue polling despite errors
        }
        
    }, API_CONFIG.POLLING.INTERVAL);
}

function displayFormFillResult(result) {
    console.log('[Form Fill] Result received:', result);
    
    elements.formFillStatus.textContent = '✅ Form filled successfully!';
    elements.formFillStatus.className = 'status-message success';
    elements.formFillStatus.style.display = 'block';
    
    // Display screenshot if available
    if (result.screenshot_url) {
        console.log('[Form Fill] Screenshot URL:', result.screenshot_url);
        elements.screenshotContainer.innerHTML = `
            <div class="screenshot">
                <h4>Form Screenshot</h4>
                <img src="${result.screenshot_url}" alt="Filled form screenshot" style="max-width: 100%; border-radius: 8px; margin-top: 10px;">
            </div>
        `;
    } else {
        console.log('[Form Fill] No screenshot_url in result');
        elements.screenshotContainer.innerHTML = `
            <div class="screenshot">
                <p style="color: #94a3b8;">No screenshot available</p>
            </div>
        `;
    }
    
    // Display filled fields
    if (result.filled_fields && Object.keys(result.filled_fields).length > 0) {
        console.log('[Form Fill] Filled fields:', result.filled_fields);
        const fieldsHtml = Object.entries(result.filled_fields)
            .map(([key, value]) => `<li><strong>${key}:</strong> ${value}</li>`)
            .join('');
        
        elements.filledFieldsContainer.innerHTML = `
            <div class="filled-fields">
                <h4>Filled Fields</h4>
                <ul>${fieldsHtml}</ul>
            </div>
        `;
    } else {
        console.log('[Form Fill] No filled_fields in result');
        elements.filledFieldsContainer.innerHTML = `
            <div class="filled-fields">
                <h4>Response Data</h4>
                <pre style="background: #1e293b; padding: 15px; border-radius: 8px; overflow-x: auto;">${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
    }
    
    elements.formFillResult.style.display = 'block';
    elements.formFillSection.style.display = 'block';
}

// Initialize
console.log('JobScoutAI Frontend initialized');
console.log('API Base URL:', API_CONFIG.BASE_URL);
