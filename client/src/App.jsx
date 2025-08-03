import { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RepoLink from './RepoLink.jsx';
import WorkSpace from './WorkSpace.jsx';
import ChatPage from './ChatPage.jsx';
import 'bootstrap/dist/css/bootstrap.min.css';
import "@fontsource/poppins";

const API_BASE_URL = 'http://127.0.0.1:8000';

// This component handles the initial flow of repo submission and workspace selection.
const MainFlow = () => {
  const [repoReceived, setRepoReceived] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    let intervalId = null;

    const checkWorkspacesReady = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/check-workspaces`);
        if (response.data.isReady) {
          clearInterval(intervalId);
          setIsProcessing(false);
          setRepoReceived(true);
        }
      } catch (error) {
        console.error("Error checking workspace status:", error);
      }
    };

    if (isProcessing) {
      intervalId = setInterval(checkWorkspacesReady, 3000);
    }

    return () => clearInterval(intervalId);
  }, [isProcessing]);

  return (
    <div style={{ fontFamily: "Poppins, sans-serif" }}>
      {!repoReceived && !isProcessing ? (
        <div className="min-vh-100 d-flex flex-column justify-content-center align-items-center text-center" style={{ backgroundColor: '#012a4a', color: 'white', padding: '2rem' }}>
          <img
            src="src/assets/logo-2.png"
            alt="RepoFlow logo"
            style={{ width: '160px', height: '160px', objectFit: 'cover' }}
          />

          <h1 className="fw-bold display-4 mb-2">RepoFlow</h1>

          <p className="mb-4 fs-6">
            Paste your GitHub Repository link and we'll analyze it for you!
          </p>

          <RepoLink onRepoSubmitted={() => setIsProcessing(true)} />
        </div>
      ) : isProcessing ? (
        <div className="d-flex align-items-center justify-content-center vh-100 text-light" style={{ backgroundColor: '#012a4a' }}>
          <div className="text-center">
            <div className="spinner-border text-info" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-3">The LLM is analyzing the repository and generating workspaces. This may take a moment...</p>
          </div>
        </div>
      ) : (
        <WorkSpace />
      )}
    </div>
  );
};

// Component to handle the chat page with RAG readiness check
const ChatPageWrapper = () => {
  const [isRagReady, setIsRagReady] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let intervalId = null;

    const checkRagReady = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/check-rag-ready`);
        console.log('RAG Status:', response.data); // Debug log
        
        if (response.data.isReady) {
          setIsRagReady(true);
          setIsChecking(false);
          if (intervalId) {
            clearInterval(intervalId);
          }
        }
      } catch (error) {
        console.error("Error checking RAG status:", error);
      }
    };

    // Check immediately
    checkRagReady();

    // Then check every 2 seconds if not ready
    if (!isRagReady) {
      intervalId = setInterval(checkRagReady, 2000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isRagReady]);

  if (isChecking && !isRagReady) {
    return (
      <div className="d-flex align-items-center justify-content-center vh-100 text-light" style={{ backgroundColor: '#012a4a' }}>
        <div className="text-center">
          <div className="spinner-border text-info" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Setting up the AI chat system...</p>
          <p className="text-muted">Please wait while we prepare your repository for analysis.</p>
        </div>
      </div>
    );
  }

  if (!isRagReady) {
    return (
      <div className="d-flex align-items-center justify-content-center vh-100 text-light" style={{ backgroundColor: '#012a4a' }}>
        <div className="text-center">
          <h3 className="text-warning">Chat Not Ready</h3>
          <p className="mt-3">The AI system is not ready yet.</p>
          <p className="text-muted">Please go back and select a workspace first.</p>
          <button 
            className="btn btn-primary mt-3"
            onClick={() => window.location.href = '/'}
          >
            Go Back to Home
          </button>
        </div>
      </div>
    );
  }

  return <ChatPage />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainFlow />} />
        <Route path="/chat" element={<ChatPageWrapper />} />
      </Routes>
    </Router>
  );
}

export default App;