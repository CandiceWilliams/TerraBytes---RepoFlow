import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; // Import useNavigate for navigation

const API_BASE_URL = 'http://127.0.0.1:8000'; // Replace with your FastAPI backend URL

const Workspace = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [isProcessingWorkspace, setIsProcessingWorkspace] = useState(false);
  const navigate = useNavigate(); // Initialize navigate hook

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/get-workspaces`);
        setWorkspaces(response.data);
      } catch (err) {
        setError("Failed to fetch workspaces. Please ensure the backend is running and a repository has been processed.");
        console.error("Error fetching workspaces:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkspaces();
  }, []);

  const handleSelectWorkspace = async (selectedWorkspace) => {
    console.log("Selected workspace:", selectedWorkspace.name);
    setMessage(`Sending workspace "${selectedWorkspace.name}" to the backend...`);
    setIsProcessingWorkspace(true); // Indicate that processing has started
    try {
      const response = await axios.post(`${API_BASE_URL}/api/select-workspace`, selectedWorkspace);
      console.log("Backend response:", response.data.message);
      setMessage(`Workspace selected successfully: "${selectedWorkspace.name}". Processing for RAG model initiated.`);
      
      // Start polling for RAG readiness
      startPollingRagReady();

    } catch (err) {
      console.error("Error sending workspace to backend:", err);
      setMessage("Failed to send workspace to backend. See console for details.");
      setIsProcessingWorkspace(false); // Reset in case of immediate error
    }
  };

  const startPollingRagReady = () => {
    setMessage("Building RAG model... This may take a moment.");
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/check-rag-ready`);
        if (response.data.isReady) {
          clearInterval(pollInterval); // Stop polling
          setMessage("RAG model ready! Redirecting to chat...");
          setIsProcessingWorkspace(false); // Reset processing state
          navigate('/chat'); // Navigate to the chat page
        } else {
          setMessage("Building RAG model... (Still processing)");
        }
      } catch (err) {
        clearInterval(pollInterval); // Stop polling on error
        console.error("Error polling RAG readiness:", err);
        setMessage("Error checking RAG model readiness. Please check backend logs.");
        setIsProcessingWorkspace(false); // Reset processing state
      }
    }, 5000); // Poll every 5 seconds
  };


  if (isLoading) {
    return (
      <div className="d-flex align-items-center justify-content-center vh-100 bg-dark text-light">
        <p className="h4">Loading workspaces...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="d-flex align-items-center justify-content-center vh-100 bg-dark text-danger">
        <p className="h4">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-dark text-light p-5 min-vh-100">
      <div className="container-xl mx-auto">
        <h2 className="display-5 fw-bold mb-5 text-center text-info">Select a Workspace</h2>
        
        {message && (
          <div className="alert alert-info" role="alert">
            {message}
          </div>
        )}

        <div className="row g-4 justify-content-center">
          {workspaces.map((workspace, index) => (
            <div key={index} className="col-md-6 col-lg-4">
              <button
                onClick={() => handleSelectWorkspace(workspace)}
                className="btn btn-secondary text-start w-100 p-4 rounded-3 shadow-lg"
                disabled={isProcessingWorkspace} // Disable buttons while processing
              >
                <h3 className="h4 fw-semibold text-warning">
                  {workspace.name}
                </h3>
                <p className="text-secondary mb-0">
                  {workspace.description}
                </p>
              </button>
            </div>
          ))}
        </div>
        
        {workspaces.length === 0 && (
          <p className="text-center text-muted h5 mt-5">No workspaces found. Please process a repository first.</p>
        )}
      </div>
    </div>
  );
};

export default Workspace;
