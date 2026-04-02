/**
 * Aria Chrome Extension - Background Service Worker
 * Coordinates communication between content scripts and Aria backend
 */

const ARIA_BACKEND = 'http://localhost:8000';
let activeTab = null;
let currentTask = null;

console.log('🚀 Aria background service worker started');

/**
 * Handle extension icon click
 */
chrome.action.onClicked.addListener(async (tab) => {
  activeTab = tab;
  console.log('Extension clicked on tab:', tab.url);
  
  // Get page state from content script
  const state = await getPageState(tab.id);
  console.log('Page state:', state);
  
  // Open popup instead (handled by manifest)
});

/**
 * Listen for messages from content scripts and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('📨 Background received:', message);
  
  if (message.type === 'CONTENT_READY') {
    console.log('✅ Content script ready on:', message.url);
    sendResponse({ success: true });
  }
  
  else if (message.type === 'GET_PAGE_STATE') {
    handleGetPageState(sender.tab.id).then(sendResponse);
    return true; // Async
  }
  
  else if (message.type === 'EXECUTE_TASK') {
    handleExecuteTask(message.task, message.query).then(sendResponse);
    return true; // Async
  }
  
  else if (message.type === 'STOP_TASK') {
    currentTask = null;
    sendResponse({ success: true });
  }
});

/**
 * Get page state from active tab
 */
async function getPageState(tabId) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, { type: 'GET_PAGE_STATE' });
    return response.state;
  } catch (error) {
    console.error('Failed to get page state:', error);
    return null;
  }
}

/**
 * Execute AI task
 */
async function handleExecuteTask(task, query) {
  console.log('🎯 Executing task:', task, query);
  
  try {
    // Get current page state
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const pageState = await getPageState(tab.id);
    
    if (!pageState) {
      return { success: false, error: 'Failed to get page state' };
    }
    
    // Send to Aria backend for AI processing
    const response = await fetch(`${ARIA_BACKEND}/api/extension/task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task: task,
        query: query,
        page: pageState
      })
    });
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }
    
    const result = await response.json();
    console.log('🤖 AI response:', result);
    
    // Execute actions returned by AI
    if (result.actions && result.actions.length > 0) {
      for (const action of result.actions) {
        console.log('Executing action:', action);
        const actionResult = await chrome.tabs.sendMessage(tab.id, {
          type: 'EXECUTE_ACTION',
          action: action
        });
        console.log('Action result:', actionResult);
        
        // Wait between actions
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    return {
      success: true,
      message: result.message || 'Task completed',
      data: result.data
    };
    
  } catch (error) {
    console.error('Task execution failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Handle GET_PAGE_STATE from popup
 */
async function handleGetPageState(tabId) {
  const state = await getPageState(tabId);
  return { success: true, state };
}

// Keep service worker alive
chrome.runtime.onInstalled.addListener(() => {
  console.log('🎉 Aria extension installed');
});

chrome.runtime.onStartup.addListener(() => {
  console.log('🔄 Aria extension started');
});
