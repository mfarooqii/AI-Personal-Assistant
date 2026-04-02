/**
 * Aria Chrome Extension - Content Script
 * Runs on every webpage and enables AI to interact with the DOM
 */

console.log('🤖 Aria extension loaded');

// Connection to background service worker
let port = null;

// Current task state
let currentTask = null;
let isExecuting = false;

/**
 * Extract page DOM structure for AI analysis
 */
function extractPageState() {
  const state = {
    url: window.location.href,
    title: document.title,
    html: document.documentElement.outerHTML.substring(0, 50000), // First 50KB
    forms: extractForms(),
    inputs: extractInputs(),
    buttons: extractButtons(),
    links: extractLinks(),
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
      scrollY: window.scrollY
    }
  };
  return state;
}

/**
 * Extract all forms on the page
 */
function extractForms() {
  const forms = [];
  document.querySelectorAll('form').forEach((form, idx) => {
    forms.push({
      id: form.id || `form_${idx}`,
      action: form.action,
      method: form.method,
      fields: Array.from(form.elements).map((el, i) => ({
        type: el.type,
        name: el.name || `field_${i}`,
        id: el.id,
        placeholder: el.placeholder,
        value: el.value,
        required: el.required,
        selector: getSelector(el)
      }))
    });
  });
  return forms;
}

/**
 * Extract all input fields
 */
function extractInputs() {
  const inputs = [];
  document.querySelectorAll('input, textarea').forEach((el, idx) => {
    inputs.push({
      index: idx,
      type: el.type,
      name: el.name,
      id: el.id,
      placeholder: el.placeholder,
      value: el.value,
      selector: getSelector(el),
      visible: isVisible(el),
      label: getLabel(el)
    });
  });
  return inputs.filter(i => i.visible).slice(0, 50); // Max 50 inputs
}

/**
 * Extract all buttons
 */
function extractButtons() {
  const buttons = [];
  document.querySelectorAll('button, input[type="button"], input[type="submit"], a[role="button"]').forEach((el, idx) => {
    buttons.push({
      index: idx,
      text: el.textContent.trim() || el.value || el.getAttribute('aria-label') || '',
      type: el.type,
      selector: getSelector(el),
      visible: isVisible(el)
    });
  });
  return buttons.filter(b => b.visible && b.text).slice(0, 50);
}

/**
 * Extract clickable links
 */
function extractLinks() {
  const links = [];
  document.querySelectorAll('a[href]').forEach((el, idx) => {
    const text = el.textContent.trim();
    if (text && isVisible(el)) {
      links.push({
        index: idx,
        text: text.substring(0, 100),
        href: el.href,
        selector: getSelector(el)
      });
    }
  });
  return links.slice(0, 50);
}

/**
 * Get CSS selector for an element
 */
function getSelector(el) {
  if (el.id) return `#${el.id}`;
  if (el.name) return `[name="${el.name}"]`;
  
  // Build path
  const path = [];
  let current = el;
  while (current && current !== document.body) {
    let selector = current.tagName.toLowerCase();
    if (current.className) {
      selector += '.' + current.className.split(' ').join('.');
    }
    path.unshift(selector);
    current = current.parentElement;
    if (path.length > 5) break; // Max depth
  }
  return path.join(' > ');
}

/**
 * Check if element is visible
 */
function isVisible(el) {
  const style = window.getComputedStyle(el);
  return style.display !== 'none' && 
         style.visibility !== 'hidden' && 
         style.opacity !== '0' &&
         el.offsetParent !== null;
}

/**
 * Get label text for form input
 */
function getLabel(input) {
  // Check for associated label
  if (input.id) {
    const label = document.querySelector(`label[for="${input.id}"]`);
    if (label) return label.textContent.trim();
  }
  
  // Check for parent label
  const parentLabel = input.closest('label');
  if (parentLabel) return parentLabel.textContent.trim();
  
  // Check for placeholder
  if (input.placeholder) return input.placeholder;
  
  // Check aria-label
  if (input.getAttribute('aria-label')) return input.getAttribute('aria-label');
  
  return '';
}

/**
 * Execute AI action on the page
 */
async function executeAction(action) {
  console.log('🎯 Executing action:', action);
  
  try {
    switch (action.type) {
      case 'click':
        return clickElement(action.selector || action.target);
      
      case 'type':
        return typeText(action.selector || action.target, action.text);
      
      case 'select':
        return selectOption(action.selector || action.target, action.value);
      
      case 'scroll':
        return scrollPage(action.direction, action.amount);
      
      case 'navigate':
        window.location.href = action.url;
        return { success: true, message: `Navigating to ${action.url}` };
      
      case 'wait':
        await new Promise(resolve => setTimeout(resolve, action.ms || 1000));
        return { success: true, message: `Waited ${action.ms}ms` };
      
      case 'extract':
        return { success: true, data: extractPageState() };
      
      default:
        return { success: false, error: 'Unknown action type' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Click an element
 */
function clickElement(selector) {
  const el = document.querySelector(selector);
  if (!el) return { success: false, error: `Element not found: ${selector}` };
  
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => {
    el.click();
  }, 300);
  
  return { success: true, message: `Clicked ${selector}` };
}

/**
 * Type text into an input
 */
function typeText(selector, text) {
  const el = document.querySelector(selector);
  if (!el) return { success: false, error: `Element not found: ${selector}` };
  
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  el.focus();
  
  // Simulate typing
  el.value = text;
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
  
  return { success: true, message: `Typed "${text}" into ${selector}` };
}

/**
 * Select an option from dropdown
 */
function selectOption(selector, value) {
  const el = document.querySelector(selector);
  if (!el) return { success: false, error: `Element not found: ${selector}` };
  
  el.value = value;
  el.dispatchEvent(new Event('change', { bubbles: true }));
  
  return { success: true, message: `Selected "${value}" in ${selector}` };
}

/**
 * Scroll the page
 */
function scrollPage(direction, amount = 500) {
  const delta = direction === 'down' ? amount : -amount;
  window.scrollBy({ top: delta, behavior: 'smooth' });
  return { success: true, message: `Scrolled ${direction}` };
}

/**
 * Listen for messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('📩 Received message:', message);
  
  if (message.type === 'GET_PAGE_STATE') {
    sendResponse({ state: extractPageState() });
  } else if (message.type === 'EXECUTE_ACTION') {
    executeAction(message.action).then(result => {
      sendResponse(result);
    });
    return true; // Async response
  } else if (message.type === 'START_TASK') {
    currentTask = message.task;
    isExecuting = true;
    sendResponse({ success: true, message: 'Task started' });
  } else if (message.type === 'STOP_TASK') {
    currentTask = null;
    isExecuting = false;
    sendResponse({ success: true, message: 'Task stopped' });
  }
});

// Notify background script that content script is ready
chrome.runtime.sendMessage({ type: 'CONTENT_READY', url: window.location.href });
