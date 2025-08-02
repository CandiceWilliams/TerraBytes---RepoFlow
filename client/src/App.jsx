import { useState, useEffect } from 'react'
import axios from 'axios';
import RepoLink from './RepoLink.jsx';
import WorkSpace from './WorkSpace.jsx';


const API_BASE_URL = 'http://127.0.0.1:8000'; // Replace with your FastAPI backend URL


function App() {
  const [repoReceived, setRepoReceived] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    let intervalId = null;

    const checkWorkspacesReady = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/check-workspaces`);
        if (response.data.isReady) {
          // If the file is ready, stop polling and show the WorkSpace component
          clearInterval(intervalId);
          setIsProcessing(false);
          setRepoReceived(true);
        }
      } catch (error) {
        console.error("Error checking workspace status:", error);
      }
    };

    if (isProcessing) {
      // Start polling every 3 seconds while the backend is processing
      intervalId = setInterval(checkWorkspacesReady, 3000);
    }

    // Clean up the interval when the component unmounts or processing is done
    return () => clearInterval(intervalId);
  }, [isProcessing]);

  return (
    <>
      {!repoReceived && !isProcessing ? (
        <RepoLink onRepoSubmitted={() => setIsProcessing(true)} /> 
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
    </>
  );
}
