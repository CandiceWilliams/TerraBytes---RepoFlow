import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Homepage from './pages/HomePage.jsx';
import RepoLink from './RepoLink.jsx';
import ChatPage from './ChatPage.jsx';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [repo, setRepo] = useState(null);

  const handleAnalyze = (repoUrl) => {
    console.log('Repo URL received in App:', repoUrl);
    setRepo(repoUrl);
    // You could route to another screen here or call FastAPI
  };

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            !repo ? (
              <Homepage onAnalyze={handleAnalyze} />
            ) : (
              <div style={{ padding: '2rem', color: '#003052' }}>
                <h2>Analyzing repo: {repo}</h2>
                {/* You can replace this with the repo analysis screen */}
              </div>
            )
          }
        />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;
