// Configuration
const CONFIG = {
    
    PASSWORD_HASH: "059138de10dae5cb2228f71de9ab533bd3822959ab48a85efcc76ccfa8cab624",
    
    // Session configuration
    SESSION_NAME: "secureSession",
    SESSION_DURATION_MINUTES: 30,
    
    // Files list - Files in the "files" directory
    FILES: [],
    
    // File type mappings
    FILE_TYPES: {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'doc',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'ppt',
        'application/msword': 'doc',
        'application/vnd.ms-excel': 'xlsx',
        'application/vnd.ms-powerpoint': 'ppt',
        'image/jpeg': 'img',
        'image/png': 'img',
        'image/gif': 'img',
        'image/svg+xml': 'img',
        'application/zip': 'default',
        'text/plain': 'default'
    }
};

// Utility function to identify file type
function identifyFileType(file) {
    const type = file.type;
    return CONFIG.FILE_TYPES[type] || 'default';
}

// Utility function to format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}

// Function to handle file uploads
function handleFileUpload(file) {
    // Check file size
    if (file.size > CONFIG.UPLOAD.maxFileSize) {
        return {
            success: false,
            message: `File size exceeds the maximum allowed size (${formatFileSize(CONFIG.UPLOAD.maxFileSize)})`
        };
    }
    
    // Check file type
    if (!CONFIG.UPLOAD.allowedTypes.includes(file.type)) {
        return {
            success: false,
            message: 'File type not allowed'
        };
    }
    
    // In a real application, you would upload the file to your server here
    // and update the list.json file to persist the change
    const newFile = {
        name: file.name,
        filename: file.name.replace(/\s+/g, '-').toLowerCase(),
        type: identifyFileType(file),
        // Add timestamp to track new uploads
        uploadTime: new Date().getTime()
    };
    
    // Add the new file to the list
    CONFIG.FILES.push(newFile);
    
    // In a real server environment, we would save to list.json here
    // saveToFileList(newFile);
    
    return {
        success: true,
        file: newFile,
        message: `${file.name} has been uploaded successfully`
    };
}

// Function to guess MIME type from file extension
function getMimeTypeFromFilename(filename) {
    const extension = filename.toLowerCase().split('.').pop();
    
    const mimeTypes = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'doc': 'application/msword',
        'xls': 'application/vnd.ms-excel',
        'ppt': 'application/vnd.ms-powerpoint',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'svg': 'image/svg+xml',
        'zip': 'application/zip',
        'txt': 'text/plain'
    };
    
    return mimeTypes[extension] || 'application/octet-stream';
}

// Function to auto-discover files in the directory
function autoDiscoverFiles() {
    return new Promise((resolve, reject) => {
        console.log('Starting file discovery process...');
        
        // Try to load files using the Fetch API to scan the directory
        fetch('files/')
            .then(response => {
            if (!response.ok) {
                throw new Error('Failed to access files directory');
            }
            return response.text();
            })
            .then(html => {
            // Parse the directory listing HTML to extract file names
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const links = Array.from(doc.querySelectorAll('a'));
            
            // Filter out parent directory links and extract file information
            const files = links
                .filter(link => !link.href.endsWith('/') && !link.href.endsWith('..'))
                .map(link => {
                const fileName = link.textContent.trim();
                return {
                    name: fileName,
                    type: getMimeTypeFromFilename(fileName)
                };
                });
            
            console.log('Files discovered from directory listing:', files);
            resolve(files);
            })
            .catch(error => {
            console.error('Error discovering files:', error);
            
            // Fallback to known files from JSON file
            console.log('Using fallback file list from JSON since directory scanning failed');
            loadKnownFilesFromJSON()
                .then(knownFiles => {
                    resolve(knownFiles);
                })
                .catch(jsonError => {
                    console.error('Error loading files from JSON:', jsonError);
                    // Ultimate fallback to empty array
                    resolve([]);
                });
            });
    });
}

// Function to scan the files directory and add files automatically
function scanFilesDirectory() {
    console.log('Starting file directory scan...');
    
    // Store any user-uploaded files before we refresh the list
    const uploadedFiles = CONFIG.FILES.filter(file => file.uploadTime);
    console.log('User uploaded files:', uploadedFiles);
    
    // Skip scanning if we already have server files
    const hasServerFiles = CONFIG.FILES.some(file => file.fromServer === true);
    if (hasServerFiles) {
        console.log('Already have server files, skipping scan');
        if (isLoggedIn()) {
            populateFiles();
        }
        return;
    }
    
    // Try to auto-discover files first
    autoDiscoverFiles()
        .then(filesData => {
            console.log('Files loaded successfully:', filesData);
            
            if (!filesData || filesData.length === 0) {
                console.warn('No files found in the response');
                throw new Error('No files found in response');
            }
            
            // Process each file to add required properties
            const filesInDirectory = filesData.map(file => {
                // Create a display name by replacing underscores with spaces
                const displayName = file.name.replace(/_/g, ' ').replace(/\.\w+$/, '');
                
                // Use provided type or guess from filename
                const fileType = file.type || getMimeTypeFromFilename(file.name);
                
                // Create file object with proper properties
                const fileObj = {
                    name: displayName,
                    filename: file.name,
                    type: identifyFileType({ type: fileType }),
                    fromServer: true, // Mark as loaded from server
                    fileId: `server-${file.name}-${Date.now()}` // Add unique ID to prevent duplicates
                };
                
                console.log('Processed file:', fileObj);
                return fileObj;
            });
            
            console.log('All processed files:', filesInDirectory);
            
            // Combine server files with any user uploads from this session
            CONFIG.FILES = [...filesInDirectory, ...uploadedFiles];
            console.log('Final file list:', CONFIG.FILES);
            
            // If user is logged in, update the display immediately
            if (isLoggedIn()) {
                populateFiles();
            }
        })
        .catch(error => {
            console.error('Error auto-discovering files:', error);
            console.log('Keeping any previously uploaded files');
            
            // Keep any uploaded files if we have them
            if (uploadedFiles.length > 0) {
                CONFIG.FILES = uploadedFiles;
                
                if (isLoggedIn()) {
                    populateFiles();
                }
            } else {
                // Only use empty state if we have no files at all
                CONFIG.FILES = [];
                
                if (isLoggedIn()) {
                    populateFiles();
                    // Show message that no files are available
                    filesGrid.innerHTML = '<div class="no-files-message">No files available. Try adding some!</div>';
                }
            }
        });
}

// Function to load known files from JSON file
function loadKnownFilesFromJSON() {
    return new Promise((resolve, reject) => {
        console.log('Loading known files from JSON file...');
        
        // Fetch the JSON file containing the known files list
        fetch('files/files-list.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load files-list.json');
                }
                return response.json();
            })
            .then(filesData => {
                console.log('Successfully loaded files from JSON:', filesData);
                
                // Validate that the data is an array
                if (!Array.isArray(filesData)) {
                    throw new Error('JSON file does not contain a valid array of files');
                }
                
                // Validate each file object has required properties
                const validFiles = filesData.filter(file => {
                    return file && typeof file.name === 'string' && typeof file.type === 'string';
                });
                
                if (validFiles.length === 0) {
                    throw new Error('No valid file entries found in JSON');
                }
                
                console.log(`Loaded ${validFiles.length} valid files from JSON`);
                resolve(validFiles);
            })
            .catch(error => {
                console.error('Error loading files from JSON:', error);
                reject(error);
            });
    });
}

// DOM Elements
const loginContainer = document.getElementById('login-container');
const fileContainer = document.getElementById('file-container');
const loginForm = document.getElementById('login-form');
const passwordInput = document.getElementById('password');
const errorMessage = document.getElementById('error-message');
const filesGrid = document.getElementById('files-grid');
const logoutBtn = document.getElementById('logout-btn');
const refreshBtn = document.getElementById('refresh-btn');

// File type icons mapping
const FILE_ICONS = {
    pdf: 'fas fa-file-pdf',
    doc: 'fas fa-file-word',
    xlsx: 'fas fa-file-excel',
    ppt: 'fas fa-file-powerpoint',
    img: 'fas fa-file-image',
    default: 'fas fa-file'
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    if (isLoggedIn()) {
        showFileContainer();
    }
    
    // Add event listeners
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    refreshBtn.addEventListener('click', handleRefresh);
    passwordInput.addEventListener('input', hideErrorMessage);
    
    // Clear password field on page load
    passwordInput.value = '';
    
    // Scan files directory only once during initialization
    scanFilesDirectory();
    
    // Add mobile and touch device optimizations
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
        
        // Add active state for touch feedback on buttons
        const buttons = document.querySelectorAll('button, .download-btn');
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.classList.add('active-touch');
            });
            button.addEventListener('touchend', function() {
                this.classList.remove('active-touch');
            });
        });
    }
    
    // Detect orientation changes and adjust UI accordingly
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            adjustUIForOrientation();
        }, 100);
    });
    
    // Initial orientation check
    adjustUIForOrientation();
});

// Adjust UI elements based on screen orientation
function adjustUIForOrientation() {
    const isLandscape = window.innerWidth > window.innerHeight;
    
    if (isLandscape && window.innerHeight < 500) {
        // Compact mode for landscape on small devices
        document.body.classList.add('landscape-compact');
    } else {
        document.body.classList.remove('landscape-compact');
    }
}

// Improve scrolling performance on mobile
let ticking = false;
window.addEventListener('scroll', function() {
    if (!ticking) {
        window.requestAnimationFrame(function() {
            // Optimize animations during scroll
            ticking = false;
        });
        ticking = true;
    }
});

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const enteredPassword = passwordInput.value.trim();
    
    try {
        // Verify password with secure hash using SHA-256
        const isValid = await SecurityUtils.verifyPassword(
            enteredPassword, 
            CONFIG.PASSWORD_HASH
        );
        
        if (isValid) {
            // Set secure session with expiration
            const sessionObj = {
                loggedIn: true,
                timestamp: new Date().getTime(),
                expires: new Date().getTime() + (CONFIG.SESSION_DURATION_MINUTES * 60 * 1000)
            };
            sessionStorage.setItem(CONFIG.SESSION_NAME, JSON.stringify(sessionObj));
            
            // Clear password field
            passwordInput.value = '';
            
            // Show file container without rescanning files
            showFileContainer();
            
            // Hide error message if visible
            hideErrorMessage();
            
            // Log access for security auditing
            console.log(`Secure access granted: ${new Date().toISOString()}`);
        } else {
            showErrorMessage('Incorrect password. Please try again.');
            passwordInput.value = '';
            passwordInput.focus();
        }
    } catch (error) {
        console.error('Login error:', error);
        showErrorMessage('An error occurred during login. Please try again.');
    }
}

// Handle logout
function handleLogout() {
    // Remove secure session
    sessionStorage.removeItem(CONFIG.SESSION_NAME);
    
    // Clear all file data from memory for security
    CONFIG.FILES = [];
    
    // Show login container
    showLoginContainer();
    passwordInput.focus();
    
    // Log logout for security auditing
    console.log(`Secure logout: ${new Date().toISOString()}`);
}

// Handle refresh
function handleRefresh() {
    // Add a visual feedback by animating the refresh icon
    const refreshIcon = refreshBtn.querySelector('i');
    refreshIcon.classList.add('fa-spin');
    
    // Reset the files array to force a rescan
    CONFIG.FILES = CONFIG.FILES.filter(file => file.uploadTime); // Keep only user uploaded files
    
    // Rescan the files directory
    scanFilesDirectory();
    
    // Show a short loading animation then stop the spin
    setTimeout(() => {
        refreshIcon.classList.remove('fa-spin');
        
        // Optional: Show a temporary success message
        const messageElement = document.createElement('div');
        messageElement.textContent = 'Files refreshed successfully!';
        messageElement.className = 'refresh-success-message';
        document.querySelector('.welcome-section').appendChild(messageElement);
        
        // Remove the message after 2 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 2000);
    }, 1000);
    
    // Log refresh for auditing
    console.log(`Files refreshed: ${new Date().toISOString()}`);
}

// Check if user is logged in with secure session
function isLoggedIn() {
    const sessionData = sessionStorage.getItem(CONFIG.SESSION_NAME);
    
    if (!sessionData) {
        return false;
    }
    
    try {
        const session = JSON.parse(sessionData);
        const now = new Date().getTime();
        
        // Check if session has expired
        if (session.expires <= now) {
            // Clean up expired session
            sessionStorage.removeItem(CONFIG.SESSION_NAME);
            return false;
        }
        
        return session.loggedIn === true;
    } catch (error) {
        console.error('Session verification error:', error);
        return false;
    }
}

// Show login container
function showLoginContainer() {
    showLoginContainerSmooth();
}

// Show file container
function showFileContainer() {
    showFileContainerSmooth();
}

// Show error message
function showErrorMessage(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// Hide error message
function hideErrorMessage() {
    errorMessage.classList.remove('show');
}

// Create file card HTML
function createFileCard(file) {
    const iconClass = FILE_ICONS[file.type] || FILE_ICONS.default;
    const filePath = `files/${encodeURIComponent(file.filename)}`;
    
    return `
        <div class="file-card">
            <i class="${iconClass} file-icon ${file.type}"></i>
            <div class="file-name">${file.name}</div>
            <a href="${filePath}" class="download-btn" download="${file.filename}" target="_blank">
                <i class="fas fa-download"></i>
                Download
            </a>
        </div>
    `;
}

// Show loading indicator
function showLoadingIndicator() {
    filesGrid.innerHTML = `
        <div class="loading-indicator">
            <i class="fas fa-sync-alt"></i>
            <div>Scanning for files...</div>
        </div>
    `;
}

// Populate files grid
function populateFiles() {
    // Show loading indicator initially
    showLoadingIndicator();
    
    // Short timeout to allow loading indicator to be seen
    setTimeout(() => {
        filesGrid.innerHTML = '';
        
        // Handle case with no files
        if (CONFIG.FILES.length === 0) {
            filesGrid.innerHTML = `
                <div class="no-files-message">
                    <i class="fas fa-folder-open"></i>
                    <p>No files found in your secure storage.</p>
                    <p>Add files to the "files" folder or use the upload button.</p>
                </div>
            `;
            return;
        }
        
        // Remove any duplicate files by filename
        const uniqueFiles = [];
        const filenameSeen = {};
        
        CONFIG.FILES.forEach(file => {
            if (!filenameSeen[file.filename]) {
                filenameSeen[file.filename] = true;
                uniqueFiles.push(file);
            }
        });
        
        // Update the FILES array with unique files only
        CONFIG.FILES = uniqueFiles;
        
        // Add files with a slight delay for animation
        CONFIG.FILES.forEach((file, index) => {
            setTimeout(() => {
                const fileCardHTML = createFileCard(file);
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = fileCardHTML;
                const fileCardElement = tempDiv.firstElementChild;
                
                filesGrid.appendChild(fileCardElement);
                
                // Add fade-in animation
                setTimeout(() => {
                    fileCardElement.classList.add('file-card-visible');
                }, 50);
            }, index * 100); // Stagger the appearance of cards
        });
        
        // Add click analytics (optional)
        setTimeout(() => {
            addDownloadTracking();
        }, CONFIG.FILES.length * 100 + 100);
    }, 800); // Short delay to show loading indicator
}

// Add download tracking (optional - for analytics)
function addDownloadTracking() {
    const downloadButtons = document.querySelectorAll('.download-btn');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const fileName = this.getAttribute('download');
            console.log(`File download initiated: ${fileName}`);
            
            // You can add analytics tracking here if needed
            // For example: gtag('event', 'download', { file_name: fileName });
        });
    });
}

// Security: Clear session on page unload (optional)
window.addEventListener('beforeunload', function() {
    // Uncomment the line below if you want to clear session on page close
    // sessionStorage.removeItem('isLoggedIn');
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // ESC to logout when viewing files
    if (event.key === 'Escape' && !fileContainer.classList.contains('hidden')) {
        handleLogout();
    }
    
    // Enter to submit login when focused on password field
    if (event.key === 'Enter' && document.activeElement === passwordInput) {
        loginForm.dispatchEvent(new Event('submit'));
    }
});

// Simple animation helper
function animateElement(element, animationClass, duration = 600) {
    element.classList.add(animationClass);
    setTimeout(() => {
        element.classList.remove(animationClass);
    }, duration);
}

// Add smooth transitions when switching views
function smoothTransition(hideElement, showElement, callback) {
    hideElement.style.opacity = '0';
    hideElement.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        hideElement.classList.add('hidden');
        showElement.classList.remove('hidden');
        
        showElement.style.opacity = '0';
        showElement.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            showElement.style.opacity = '1';
            showElement.style.transform = 'translateY(0)';
            if (callback) callback();
        }, 50);
    }, 300);
}

// Show login container with smooth animation
function showLoginContainerSmooth() {
    smoothTransition(fileContainer, loginContainer);
}

// Show file container with smooth animation
function showFileContainerSmooth() {
    smoothTransition(loginContainer, fileContainer, populateFiles);
}
