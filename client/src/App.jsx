import React, { useState } from 'react';

function App() {
  const [repoUrl, setRepoUrl] = useState('');

  const handleAnalyze = () => {
    console.log('Analyzing:', repoUrl);
    fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
      'Content-Type': 'application/json',
      },
      body: JSON.stringify({ repo_url: repoUrl }),
    })
      .then((response) => response.json())
      .then((data) => {
      console.log('Analysis result:', data);
      // You can update state here to display results
      })
      .catch((error) => {
      console.error('Error:', error);
      });
  };

  return (
    <div className="home">
      <img src="/cat-logo.png" alt="RepoFlow logo" className="logo" />

      <h1 className="title">RepoFlow</h1>

      <p className="subtitle">
        Paste your GitHub Repository link and we’ll analyze it for you!
      </p>

      <input
        type="text"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        placeholder="Enter link"
        className="repo-input"
      />

      <button onClick={handleAnalyze} className="analyze-button">
        Analyze Repo
      </button>
    </div>
  );
}

export default App;
