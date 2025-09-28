const API_BASE_URL = 'http://127.0.0.1:8000/api/';

const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('audio_file');
const submitBtn = document.getElementById('submitBtn');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const statusMessage = document.getElementById('statusMessage');
const resultsSection = document.getElementById('resultsSection');
const summaryResult = document.getElementById('summaryResult');
const todoListResult = document.getElementById('todoListResult');
const transcriptResult = document.getElementById('transcriptResult');
const meetingTitle = document.getElementById('meetingTitle');

// --- CRITICAL FIX: Ensure the results section starts hidden by style ---
resultsSection.style.display = 'none';

const POLL_INTERVAL_MS = 3000; // Check every 3 seconds

function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-box status-${type}`;
    statusMessage.classList.remove('hidden');
    // CRITICAL: We DO NOT hide the results section here. We only manage the status box.
}

function resetUI() {
    statusMessage.classList.add('hidden');
    resultsSection.classList.add('hidden');
    resultsSection.style.display = 'none'; // Ensure hidden state is strict
    submitBtn.disabled = true;
    fileNameDisplay.textContent = 'Click or drag file here';
    fileInput.value = '';
}

// --- Event Listeners ---

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        fileNameDisplay.textContent = fileInput.files[0].name;
        submitBtn.disabled = false;
    } else {
        resetUI();
    }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInput.files.length) return;

    submitBtn.textContent = 'Uploading...';
    submitBtn.disabled = true;
    showStatus('Uploading file and starting background job...', 'pending');

    const formData = new FormData();
    formData.append('audio_file', fileInput.files[0]);

    try {
        // 1. START THE JOB (sends file, receives Job ID immediately)
        const startResponse = await fetch(API_BASE_URL + 'start-summary-job/', {
            method: 'POST',
            body: formData,
        });

        if (startResponse.status === 202) {
            const data = await startResponse.json();
            const jobId = data.job_id;
            
            // 2. Begin Polling
            showStatus(`Job started (ID: ${jobId}). Processing audio...`, 'pending');
            pollJobStatus(jobId);
        } else {
            const errorData = await startResponse.json();
            throw new Error(errorData.message || 'Failed to start job.');
        }

    } catch (error) {
        console.error('Initial submission error:', error);
        showStatus(`Error: ${error.message}. Please try again.`, 'failed');
        submitBtn.textContent = 'Summarize Meeting';
        resetUI();
    }
});

// --- Polling Logic ---

async function pollJobStatus(jobId) {
    const statusCheckUrl = API_BASE_URL + `check-job-status/${jobId}/`;

    const interval = setInterval(async () => {
        try {
            const response = await fetch(statusCheckUrl);
            const data = await response.json();

            // Update status message with current job phase
            if (data.status === 'RUNNING') {
                showStatus(`Job ID ${jobId} Running: ${data.message || 'Processing in background...'}`, 'pending');
                return;
            }

            // --- STOP POLLING & HANDLE RESULT ---
            clearInterval(interval); 
            submitBtn.textContent = 'Summarize Meeting'; // Reset button text

            if (data.status === 'COMPLETE') {
                displayResults(data);
                showStatus('Success! Analysis complete.', 'complete');
            } else if (data.status === 'FAILED') {
                showStatus(`Job FAILED: ${data.message}`, 'failed');
                resetUI(); 
            }

        } catch (error) {
            clearInterval(interval);
            console.error('Polling error:', error);
            showStatus('Critical Error during polling. Check console.', 'failed');
            submitBtn.textContent = 'Summarize Meeting';
            resetUI();
        }
    }, POLL_INTERVAL_MS);
}

function displayResults(data) {
    meetingTitle.textContent = data.title || 'Meeting';
    summaryResult.textContent = data.summary;
    todoListResult.textContent = data.todo_list;
    transcriptResult.textContent = data.transcript;

    resultsSection.classList.remove('hidden'); 
    resultsSection.style.display = 'block'; 
    
    statusMessage.classList.add('hidden');
    
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}