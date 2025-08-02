import axios from 'axios';
import{ useState } from 'react';

const GithubIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="h-6 w-6 text-light me-2"
    fill="currentColor"
    viewBox="0 0 24 24"
  >
    <path
      d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.6.111.819-.26.819-.578 0-.28-.01-1.018-.01-2.008-3.332.724-4.043-1.61-4.043-1.61-.542-1.355-1.321-1.714-1.321-1.714-1.085-.744.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.998.108-.77.42-1.304.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.31.467-2.383 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.046.138 3.003.404 2.291-1.552 3.298-1.23 3.298-1.23.652 1.652.241 2.873.118 3.176.77.838 1.233 1.911 1.233 3.221 0 4.609-2.807 5.624-5.474 5.922.43.372.823 1.102.823 2.222 0 1.606-.015 2.896-.015 3.286 0 .315.216.695.825.578 4.761-1.588 8.199-6.085 8.199-11.387c0-6.627-5.373-12-12-12z"
    />
  </svg>
);

export default function RepoLink() {

    const [repoUrl, setRepoUrl] = useState('');
    
      // Handles changes to the input field, updating the state
      const handleInputChange = (event) => {
        setRepoUrl(event.target.value);
      };
    
      // Handles the form submission
      const handleSubmit = (event) => {
        event.preventDefault();
        if (!repoUrl.trim()) {
          alert('Please enter a GitHub repository URL.');
          return;
        }
        axios.post('http://localhost:8000/api/recieve-repo', { url: repoUrl })
          .then(response => {
            if (typeof response.data.err === 'boolean') {
              // Call the prop function to App.jsx, pass true if err is false (success)
              if (typeof props.onRepoAnalyzed === 'function') {
                props.onRepoAnalyzed(!response.data.err);
              }
              if (!response.data.err) {
                alert(response.data.message || 'Repository analyzed successfully!');
              } else {
                alert('Repository not found.');
              }
            } else {
              alert('Unexpected response from server.');
            }
          })
          .catch(error => {
            alert(error.response?.data?.error || 'Failed to analyze repository.');
          });
      };

      return (
        <>
          <div className="bg-dark text-light min-vh-100 d-flex align-items-center justify-content-center p-4">
            {/* Card-like container for the input form */}
            <div className="bg-dark p-5 rounded-4 shadow-lg" style={{ maxWidth: '600px', width: '100%' }}>
          {/* Main title of the application */}
          <div className="d-flex align-items-center justify-content-center mb-4">
            <GithubIcon />
            <h1 className="display-4 fw-bold text-light text-center">RepoFlow</h1>
          </div>
          
          {/* Descriptive text for the user */}
          <p className="text-center text-muted mb-5 lead">
            Enter a GitHub repository URL to get started. RepoFlow will analyze the repository and provide a structured overview.
          </p>

          {/* The form for submitting the URL */}
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="repo-url" className="form-label visually-hidden">
                GitHub Repository URL
              </label>
              <input
                id="repo-url"
                type="text"
                placeholder="https://github.com/owner/repository"
                value={repoUrl}
                onChange={handleInputChange}
                className="form-control form-control-lg bg-secondary text-white border-0"
                required
              />
            </div>
            
            {/* Submit button */}
            <button
              type="submit"
              className="btn btn-primary btn-lg w-100 fw-bold shadow-sm"
              onClick={handleSubmit}
            >
              Analyze Repo
            </button>
          </form>
        </div>
      </div>
    </>
  );
}