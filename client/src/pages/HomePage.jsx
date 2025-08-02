import React, { useState } from 'react';

function Homepage({ onAnalyze }) {
  const [repoUrl, setRepoUrl] = useState('');

  const handleClick = () => {
    if (repoUrl.trim()) {
      onAnalyze(repoUrl); // Pass to parent (App.jsx)
    }
  };

  return (
    <div style={styles.container}>
      <img src="/cat-logo.png" alt="RepoFlow logo" style={styles.logo} />

      <h1 style={styles.title}>RepoFlow</h1>

      <p style={styles.subtitle}>
        Paste your GitHub Repository link and we’ll analyze it for you!
      </p>

      <input
        type="text"
        placeholder="Enter link"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        style={styles.input}
      />

      <button onClick={handleClick} style={styles.button}>
        Analyze Repo
      </button>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#003052',
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem',
    textAlign: 'center',
    fontFamily: '"Segoe UI", sans-serif',
  },
  logo: {
    width: 160,
    height: 160,
    borderRadius: '50%',
    marginBottom: 24,
    objectFit: 'cover',
  },
  title: {
    fontSize: 48,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    marginBottom: 24,
  },
  input: {
    width: '100%',
    maxWidth: 600,
    padding: '14px 20px',
    borderRadius: 30,
    backgroundColor: '#4a6173',
    border: 'none',
    color: 'white',
    fontSize: 16,
    marginBottom: 24,
    outline: 'none',
  },
  button: {
    padding: '14px 32px',
    backgroundColor: '#a3d4ec',
    color: '#003052',
    fontWeight: 'bold',
    fontSize: 16,
    border: 'none',
    borderRadius: 12,
    cursor: 'pointer',
  },
};

export default Homepage;
