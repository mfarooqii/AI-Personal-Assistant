# Aria Chrome Extension

AI assistant that helps you automate web tasks directly in your browser.

## Features

- **Auto-fill forms** - AI detects form fields and fills them for you
- **Check email** - Navigate to Gmail/Yahoo and extract unread emails
- **Search products** - Find items on Amazon with specific filters
- **Extract data** - Pull structured data from any webpage
- **Navigate websites** - AI clicks buttons, fills inputs, and follows links

## Installation (Development Mode)

1. **Make sure Aria backend is running:**
   ```bash
   cd backend
   source .venv/bin/activate
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Open Chrome and navigate to:**
   ```
   chrome://extensions/
   ```

3. **Enable "Developer mode"** (toggle in top-right corner)

4. **Click "Load unpacked"**

5. **Select the extension folder:**
   ```
   /path/to/AI-Personal-Assistant/extension
   ```

6. **Extension installed!** You should see the Aria icon in your toolbar

## Usage

### Method 1: Click the Extension Icon

1. Visit any website (e.g., gmail.com, amazon.com)
2. Click the Aria extension icon in your toolbar
3. Type what you want to do:
   - "Check my unread emails"
   - "Find wireless headphones under $100"
   - "Fill this form with my information"
   - "Extract all product prices"
4. Press Enter or click "Ask Aria"
5. Watch as AI automates the task!

### Method 2: Quick Actions

Click the extension icon and use pre-built shortcuts:
- 📧 **Check Email** - Navigate to inbox and show unread messages
- 📝 **Fill Form** - Auto-fill form fields with your info
- 🛒 **Search** - Search for products with filters
- 📊 **Extract** - Pull data from the current page

## How It Works

```
Chrome Browser
    ↓
Extension (content script + background worker)
    ↓ HTTP Request
Aria Backend (FastAPI at localhost:8000)
    ↓
AI Model (Ollama)
    ↓ Actions
Extension executes on page
    ↓
Results shown to user
```

## Architecture

- **`manifest.json`** - Extension configuration (Manifest V3)
- **`content.js`** - Runs on every webpage, interacts with DOM
- **`background.js`** - Service worker, coordinates with backend
- **`popup.html/js`** - UI when you click the extension icon
- **Backend API** - `/api/extension/task` endpoint processes requests

## Supported Actions

The AI can execute these actions on any webpage:

| Action | Description | Example |
|--------|-------------|---------|
| `click` | Click an element | Click "Sign In" button |
| `type` | Type text into input | Enter email address |
| `select` | Choose dropdown option | Select country |
| `scroll` | Scroll page up/down | Scroll to bottom |
| `navigate` | Go to URL | Open gmail.com |
| `wait` | Pause execution | Wait 2 seconds |
| `extract` | Get page data | Extract product list |

## Examples

### Check Gmail
1. Click extension icon
2. Type: "check my email"
3. AI navigates to gmail.com
4. If not logged in, prompts you to login
5. Extracts unread emails
6. Shows in popup or Aria dashboard

### Amazon Product Search
1. Visit amazon.com
2. Click extension
3. Type: "find noise-cancelling headphones under $150, 4+ stars, Sony brand"
4. AI:
   - Searches for "noise-cancelling headphones"
   - Applies price filter ($0-$150)
   - Filters by brand (Sony)
   - Filters by rating (4+ stars)
   - Extracts results
5. Shows matching products

### Fill Form
1. Open any form (job application, contact form, etc.)
2. Click extension
3. Type: "fill this form"
4. AI detects fields and fills with your saved info
5. You review and submit

## Icon Placeholders

**Note:** The extension currently uses SVG placeholders for icons. To add proper PNG icons:

1. Create or download 16x16, 48x48, and 128x128 PNG icons
2. Save them in `extension/icons/` as:
   - `icon16.png`
   - `icon48.png`
   - `icon128.png`

Or use ImageMagick to convert the SVG:
```bash
cd extension/icons
convert -background none icon.svg -resize 16x16 icon16.png
convert -background none icon.svg -resize 48x48 icon48.png
convert -background none icon.svg -resize 128x128 icon128.png
```

## Debugging

### View Extension Logs
1. Open Chrome DevTools (F12)
2. Go to "Console" tab
3. Select "Extension" from dropdown
4. See content script logs

### View Background Worker Logs
1. Go to `chrome://extensions/`
2. Find Aria extension
3. Click "service worker" link
4. DevTools opens with background script logs

### Common Issues

**"Extension not working on this page"**
- Some sites block content scripts (rare)
- Check console for errors

**"Cannot connect to backend"**
- Make sure Aria backend is running on `localhost:8000`
- Check CORS is enabled in backend

**"Task failed"**
- Check backend logs for errors
- AI might not understand the page structure
- Try being more specific in your request

## Next Steps

After testing locally:
1. **Iterate** - Improve prompts and actions
2. **Add features** - More task types, better extraction
3. **Publish** - Submit to Chrome Web Store (requires $5 fee + review)

## Publishing to Chrome Web Store

When ready for public release:
1. Create developer account ($5 one-time fee)
2. Add privacy policy
3. Add screenshots of extension in action
4. Submit for review (5-14 days)
5. Extension goes live!

## License

Part of the Aria AI Personal Assistant project.
