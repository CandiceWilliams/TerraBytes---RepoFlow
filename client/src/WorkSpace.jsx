import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = 'http://127.0.0.1:8000';

const Workspace = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [isProcessingWorkspace, setIsProcessingWorkspace] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        const { data } = await axios.post(`${API_BASE_URL}/api/get-workspaces`);
        setWorkspaces(data);
      } catch (err) {
        setError(
          'Failed to fetch workspaces. Please ensure the backend is running and a repository has been processed.'
        );
        console.error('Error fetching workspaces:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkspaces();
  }, []);

  const handleSelectWorkspace = async (selectedWorkspace) => {
    console.log('Selected workspace:', selectedWorkspace.name);
    setMessage(`Sending workspace "${selectedWorkspace.name}" to the backend…`);
    setIsProcessingWorkspace(true);

    try {
      const { data } = await axios.post(
        `${API_BASE_URL}/api/select-workspace`,
        selectedWorkspace
      );
      console.log('Backend response:', data.message);
      setMessage(
        `Workspace selected successfully: "${selectedWorkspace.name}". Processing for RAG model initiated.`
      );
      startPollingRagReady();
    } catch (err) {
      console.error('Error sending workspace to backend:', err);
      setMessage('Failed to send workspace to backend. See console for details.');
      setIsProcessingWorkspace(false);
    }
  };

  const startPollingRagReady = () => {
    setMessage('Building RAG model… This may take a moment.');
    const pollInterval = setInterval(async () => {
      try {
        const { data } = await axios.get(`${API_BASE_URL}/api/check-rag-ready`);
        if (data.isReady) {
          clearInterval(pollInterval);
          setMessage('RAG model ready! Redirecting to chat…');
          setIsProcessingWorkspace(false);
          navigate('/chat');
        } else {
          setMessage('Building RAG model… (Still processing)');
        }
      } catch (err) {
        clearInterval(pollInterval);
        console.error('Error polling RAG readiness:', err);
        setMessage('Error checking RAG model readiness. Please check backend logs.');
        setIsProcessingWorkspace(false);
      }
    }, 5000);
  };

  /* ---------- RENDER ---------- */

  if (isLoading) {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center bg-custom-1">
        <p className="text-white h4">Loading workspaces…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-vh-100 d-flex align-items-center justify-content-center bg-custom-1">
        <p className="text-danger h4 text-center px-3">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-vh-100 bg-custom-1 py-5">
      <div className="container-lg">
        {/* Title */}
        <h1 className="text-white display-5 fw-bold text-center mb-5">
          Select a Workspace
        </h1>

        {/* Message Alert */}
        {message && (
          <div className="alert alert-info text-center" role="alert">
            {message}
          </div>
        )}

        {/* Workspace Grid */}
        <div className="row row-cols-1 row-cols-md-2 g-4 justify-content-center">
          {workspaces.map((workspace, idx) => (
            <div className="col" key={idx}>
              <button
                onClick={() => handleSelectWorkspace(workspace)}
                disabled={isProcessingWorkspace}
                className="btn btn-custom-1 hover-lift w-100 h-100 text-start p-4 shadow-sm"
              >
                <h3 className="h5 fw-semibold mb-2 btn-custom-1">{workspace.name}</h3>
                <p className="btn-custom-1 small mb-0 bg-custom-1">{workspace.description}</p>
              </button>
            </div>
          ))}
        </div>

        {/* No workspaces message */}
        {workspaces.length === 0 && (
          <p className="text-white h5 text-center mt-5">
            No workspaces found. Please process a repository first.
          </p>
        )}
      </div>
    </div>
  );
};

export default Workspace;
