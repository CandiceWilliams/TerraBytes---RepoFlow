import { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RepoLink from './RepoLink.jsx';
import WorkSpace from './WorkSpace.jsx';
import ChatPage from './ChatPage.jsx';
import 'bootstrap/dist/css/bootstrap.min.css';
import "@fontsource/poppins";

const API_BASE_URL = 'http://127.0.0.1:8000'; // Replace with your FastAPI backend URL

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
        <div className="min-vh-100 d-flex flex-column justify-content-center align-items-center text-center" style={{ backgroundColor: '#04374f', color: 'white', padding: '2rem' }}>
          <img
            src="src/assets/logo-2.png"
            alt="RepoFlow logo"
            className="rounded-circle mb-4"
            style={{ width: '160px', height: '160px', objectFit: 'cover' }}
          />

          <h1 className="fw-bold display-4 mb-2">RepoFlow</h1>

          <p className="mb-4 fs-6">
            Paste your GitHub Repository link and we’ll analyze it for you!
          </p>

          <RepoLink onRepoSubmitted={() => setIsProcessing(true)} />
        </div>
      ) : isProcessing ? (
        <div className="d-flex align-items-center justify-content-center vh-100 bg-dark text-light">
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

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainFlow />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;

