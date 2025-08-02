import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Assume Bootstrap CSS is loaded globally in your index.html
// <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" xintegrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">

const API_BASE_URL = 'http://127.0.0.1:8000'; // Replace with your FastAPI backend URL

const Workspace = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    // Function to fetch the list of workspaces from the backend
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

  // Function to handle the button click and send the selected workspace to the backend
  const handleSelectWorkspace = async (selectedWorkspace) => {
    console.log("Selected workspace:", selectedWorkspace.name);
    setMessage(`Sending workspace "${selectedWorkspace.name}" to the backend...`);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/select-workspace`, selectedWorkspace);
      console.log("Backend response:", response.data.message);
      setMessage(`Workspace selected successfully: "${selectedWorkspace.name}". The backend is now processing.`);
    } catch (err) {
      console.error("Error sending workspace to backend:", err);
      setMessage("Failed to send workspace to backend. See console for details.");
    }
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
