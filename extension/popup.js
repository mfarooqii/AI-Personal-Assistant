/**
 * Aria Extension - Popup UI Logic
 */

const queryInput = document.getElementById('queryInput');
const sendBtn = document.getElementById('sendBtn');
const status = document.getElementById('status');
const pageTitle = document.getElementById('pageTitle');
const pageUrl = document.getElementById('pageUrl');

let currentTab = null;

// Load current tab info
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  currentTab = tabs[0];
  pageTitle.textContent = currentTab.title;
  pageUrl.textContent = new URL(currentTab.url).hostname;
});

// Handle quick action buttons
document.querySelectorAll('.action-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const task = btn.getAttribute('data-task');
    queryInput.value = task;
    handleSend();
  });
});

// Handle send button
sendBtn.addEventListener('click', handleSend);

// Handle Enter key
queryInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    handleSend();
  }
});

/**
 * Send task to AI
 */
async function handleSend() {
  const query = queryInput.value.trim();
  if (!query) return;
  
  showStatus('loading', 'Thinking...');
  sendBtn.disabled = true;
  
  try {
    // Send message to background script
    const response = await chrome.runtime.sendMessage({
      type: 'EXECUTE_TASK',
      task: 'auto', // Let AI determine the task type
      query: query
    });
    
    if (response.success) {
      showStatus('success', response.message || 'Task completed successfully!');
      queryInput.value = '';
    } else {
      showStatus('error', response.error || 'Task failed');
    }
  } catch (error) {
    console.error('Error:', error);
    showStatus('error', `Error: ${error.message}`);
  } finally {
    sendBtn.disabled = false;
  }
}

/**
 * Show status message
 */
function showStatus(type, message) {
  status.style.display = 'block';
  status.className = `status ${type}`;
  
  if (type === 'loading') {
    status.innerHTML = `<span class="spinner"></span>${message}`;
  } else {
    status.textContent = message;
  }
}

// Focus input on popup open
queryInput.focus();
