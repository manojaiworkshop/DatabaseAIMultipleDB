// ===========================
// Configuration
// ===========================
let API_BASE_URL = localStorage.getItem('license_api_url') || 'http://localhost:5000';

// ===========================
// Utility Functions
// ===========================

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

// Generate random deployment ID
function generateDeploymentId() {
    const date = new Date();
    const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
    const randomStr = Math.random().toString(36).substring(2, 10).toUpperCase();
    return `deploy-${dateStr}-${randomStr}`;
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!', 'success');
    }
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Calculate days remaining
function getDaysRemaining(expiryDate) {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
}

// ===========================
// API Functions
// ===========================

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Generate License
async function generateLicense(email, deploymentId, licenseType, adminKey) {
    return apiRequest('/license/generate', {
        method: 'POST',
        body: JSON.stringify({
            deployment_id: deploymentId,
            license_type: licenseType,
            admin_key: adminKey,
            email: email
        })
    });
}

// Validate License
async function validateLicense(licenseKey) {
    return apiRequest('/license/validate', {
        method: 'POST',
        body: JSON.stringify({
            license_key: licenseKey
        })
    });
}

// Renew License
async function renewLicense(currentLicenseKey, adminKey) {
    return apiRequest('/license/renew', {
        method: 'POST',
        body: JSON.stringify({
            current_license_key: currentLicenseKey,
            admin_key: adminKey
        })
    });
}

// ===========================
// Tab Navigation
// ===========================
function setupTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // Remove active class from all buttons and tabs
            navButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));

            // Add active class to clicked button and corresponding tab
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// ===========================
// Generate License Form
// ===========================
function setupGenerateForm() {
    const form = document.getElementById('generateForm');
    const resultDiv = document.getElementById('gen-result');
    const submitBtn = document.getElementById('gen-submit-btn');
    const randomIdBtn = document.getElementById('gen-random-id');

    // Generate random deployment ID
    randomIdBtn.addEventListener('click', () => {
        document.getElementById('gen-deployment-id').value = generateDeploymentId();
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('gen-email').value.trim();
        const deploymentId = document.getElementById('gen-deployment-id').value.trim();
        const licenseType = document.querySelector('input[name="license-type"]:checked').value;
        const adminKey = document.getElementById('gen-admin-key').value.trim();

        // Validate inputs
        if (!email || !deploymentId || !adminKey) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        // Disable button and show loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner"></div> Generating...';
        resultDiv.classList.add('hidden');

        try {
            const data = await generateLicense(email, deploymentId, licenseType, adminKey);
            displayGenerateResult(data);
            showToast('License generated successfully!', 'success');
        } catch (error) {
            displayError(resultDiv, error.message);
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-magic"></i> Generate License';
        }
    });
}

function displayGenerateResult(data) {
    const resultDiv = document.getElementById('gen-result');
    
    const licenseTypeLabels = {
        trial: 'Trial License',
        standard: 'Standard License',
        enterprise: 'Enterprise License'
    };

    resultDiv.className = 'result success';
    resultDiv.innerHTML = `
        <div class="result-header">
            <i class="fas fa-check-circle"></i>
            <span>License Generated Successfully!</span>
        </div>
        <div class="result-content">
            <div class="result-item">
                <span class="result-label">License Type:</span>
                <span class="result-value">${licenseTypeLabels[data.license_type] || data.license_type}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Deployment ID:</span>
                <span class="result-value">${data.deployment_id}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Valid For:</span>
                <span class="result-value">${data.days_valid} days</span>
            </div>
            <div class="result-item">
                <span class="result-label">Issue Date:</span>
                <span class="result-value">${formatDate(data.issue_date)}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Expiry Date:</span>
                <span class="result-value">${formatDate(data.expiry_date)}</span>
            </div>
            <div style="margin-top: 1rem;">
                <label style="font-weight: 600; margin-bottom: 0.5rem; display: block;">
                    <i class="fas fa-key"></i> Your License Key:
                </label>
                <div class="license-key-display">
                    ${data.license_key}
                    <button class="copy-btn" onclick="copyToClipboard('${data.license_key}')">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultDiv.classList.remove('hidden');
}

// ===========================
// Validate License Form
// ===========================
function setupValidateForm() {
    const form = document.getElementById('validateForm');
    const resultDiv = document.getElementById('val-result');
    const submitBtn = document.getElementById('val-submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const licenseKey = document.getElementById('val-license-key').value.trim();

        if (!licenseKey) {
            showToast('Please enter a license key', 'error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner"></div> Validating...';
        resultDiv.classList.add('hidden');

        try {
            const data = await validateLicense(licenseKey);
            displayValidateResult(data);
            
            if (data.valid) {
                showToast('License is valid!', 'success');
            } else {
                showToast('License is invalid or expired', 'error');
            }
        } catch (error) {
            displayError(resultDiv, error.message);
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-check"></i> Validate License';
        }
    });
}

function displayValidateResult(data) {
    const resultDiv = document.getElementById('val-result');
    
    if (data.error) {
        displayError(resultDiv, data.error);
        return;
    }

    const isValid = data.valid && !data.expired;
    const statusBadge = isValid 
        ? '<span class="status-badge valid"><i class="fas fa-check-circle"></i> Valid</span>'
        : '<span class="status-badge expired"><i class="fas fa-times-circle"></i> Expired</span>';

    resultDiv.className = `result ${isValid ? 'success' : 'error'}`;
    resultDiv.innerHTML = `
        <div class="result-header">
            <i class="fas ${isValid ? 'fa-shield-alt' : 'fa-exclamation-triangle'}"></i>
            <span>License ${isValid ? 'Validation Result' : 'Invalid'}</span>
        </div>
        <div class="result-content">
            <div class="result-item">
                <span class="result-label">Status:</span>
                <span class="result-value">${statusBadge}</span>
            </div>
            <div class="result-item">
                <span class="result-label">License Type:</span>
                <span class="result-value">${data.license_type || 'N/A'}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Deployment ID:</span>
                <span class="result-value">${data.deployment_id || 'N/A'}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Issue Date:</span>
                <span class="result-value">${data.issue_date ? formatDate(data.issue_date) : 'N/A'}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Expiry Date:</span>
                <span class="result-value">${data.expiry_date ? formatDate(data.expiry_date) : 'N/A'}</span>
            </div>
            ${isValid ? `
            <div class="result-item">
                <span class="result-label">Days Remaining:</span>
                <span class="result-value" style="color: var(--success-color); font-weight: 700;">
                    ${data.days_remaining} days
                </span>
            </div>
            ` : ''}
        </div>
    `;
    
    resultDiv.classList.remove('hidden');
}

// ===========================
// Renew License Form
// ===========================
function setupRenewForm() {
    const form = document.getElementById('renewForm');
    const resultDiv = document.getElementById('renew-result');
    const submitBtn = document.getElementById('renew-submit-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const currentLicenseKey = document.getElementById('renew-license-key').value.trim();
        const adminKey = document.getElementById('renew-admin-key').value.trim();

        if (!currentLicenseKey || !adminKey) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner"></div> Renewing...';
        resultDiv.classList.add('hidden');

        try {
            const data = await renewLicense(currentLicenseKey, adminKey);
            displayRenewResult(data);
            showToast('License renewed successfully!', 'success');
        } catch (error) {
            displayError(resultDiv, error.message);
            showToast(error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Renew License';
        }
    });
}

function displayRenewResult(data) {
    const resultDiv = document.getElementById('renew-result');
    
    const licenseTypeLabels = {
        trial: 'Trial License',
        standard: 'Standard License',
        enterprise: 'Enterprise License'
    };

    resultDiv.className = 'result success';
    resultDiv.innerHTML = `
        <div class="result-header">
            <i class="fas fa-check-circle"></i>
            <span>License Renewed Successfully!</span>
        </div>
        <div class="result-content">
            <div class="result-item">
                <span class="result-label">License Type:</span>
                <span class="result-value">${licenseTypeLabels[data.license_type] || data.license_type}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Deployment ID:</span>
                <span class="result-value">${data.deployment_id}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Valid For:</span>
                <span class="result-value">${data.days_valid} days</span>
            </div>
            <div class="result-item">
                <span class="result-label">New Issue Date:</span>
                <span class="result-value">${formatDate(data.issue_date)}</span>
            </div>
            <div class="result-item">
                <span class="result-label">New Expiry Date:</span>
                <span class="result-value">${formatDate(data.expiry_date)}</span>
            </div>
            <div style="margin-top: 1rem;">
                <label style="font-weight: 600; margin-bottom: 0.5rem; display: block;">
                    <i class="fas fa-key"></i> Your New License Key:
                </label>
                <div class="license-key-display">
                    ${data.license_key}
                    <button class="copy-btn" onclick="copyToClipboard('${data.license_key}')">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultDiv.classList.remove('hidden');
}

// ===========================
// Error Display
// ===========================
function displayError(resultDiv, errorMessage) {
    resultDiv.className = 'result error';
    resultDiv.innerHTML = `
        <div class="result-header">
            <i class="fas fa-exclamation-circle"></i>
            <span>Error</span>
        </div>
        <div class="result-content">
            <p style="color: var(--danger-color);">${errorMessage}</p>
            <p style="color: var(--text-secondary); margin-top: 1rem; font-size: 0.9rem;">
                Please check your inputs and try again. Make sure the license server is running.
            </p>
        </div>
    `;
    resultDiv.classList.remove('hidden');
}

// ===========================
// Settings Modal
// ===========================
function setupSettingsModal() {
    const modal = document.getElementById('settings-modal');
    const openBtn = document.getElementById('open-settings');
    const closeBtn = modal.querySelector('.modal-close');
    const saveBtn = document.getElementById('save-settings');
    const apiUrlInput = document.getElementById('api-url');

    // Load saved URL
    apiUrlInput.value = API_BASE_URL;

    // Open modal
    openBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });

    // Close modal
    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    // Save settings
    saveBtn.addEventListener('click', () => {
        const newUrl = apiUrlInput.value.trim();
        if (newUrl) {
            API_BASE_URL = newUrl;
            localStorage.setItem('license_api_url', newUrl);
            showToast('Settings saved successfully!', 'success');
            modal.classList.remove('active');
        } else {
            showToast('Please enter a valid URL', 'error');
        }
    });
}

// ===========================
// Initialize Application
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    setupTabNavigation();
    setupGenerateForm();
    setupValidateForm();
    setupRenewForm();
    setupSettingsModal();

    // Auto-generate deployment ID on page load
    document.getElementById('gen-deployment-id').value = generateDeploymentId();
    
    console.log('PGAIView License Portal initialized');
    console.log('API Base URL:', API_BASE_URL);
});

// Make copyToClipboard available globally
window.copyToClipboard = copyToClipboard;
