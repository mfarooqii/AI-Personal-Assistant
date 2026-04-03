import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { initFrontendLogger } from './utils/frontendLogger'

// Capture browser errors and ship them to /api/logs/frontend
initFrontendLogger()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
