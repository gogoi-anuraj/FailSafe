// import { StrictMode } from 'react'
// import { createRoot } from 'react-dom/client'
// import './index.css'
// import App from './App.jsx'

// createRoot(document.getElementById('root')).render(
//   <StrictMode>
//     <App />
//   </StrictMode>,
// )

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// ErrorBoundary catches silent white screen crashes and shows
// the actual error message. Remove this in production.
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }
  static getDerivedStateFromError(error) {
    return { error }
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          background: '#0D0D0D', color: '#F4F5F7',
          padding: '2rem', fontFamily: 'monospace',
          minHeight: '100vh'
        }}>
          <h2 style={{ color: '#EF4444' }}>App crashed — check this error:</h2>
          <pre style={{ color: '#fbbf24', marginTop: '1rem', whiteSpace: 'pre-wrap' }}>
            {this.state.error.toString()}
            {'\n\n'}
            {this.state.error.stack}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
)
